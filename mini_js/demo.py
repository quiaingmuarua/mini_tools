# lifter_cfg_pretty.py
# Minimal stack-VM -> three-address IR -> basic blocks -> simple decompile to JS-like code
from collections import defaultdict, namedtuple

Instr = namedtuple("Instr", ["addr", "op", "args"])
Assign = namedtuple("Assign", ["dst", "op", "args"])  # dst: temp or "ret"
Jmp = namedtuple("Jmp", ["cond", "target", "is_cond"])  # cond is temp or None


class TempGen:
    def __init__(self):
        self.i = 0

    def new(self):
        self.i += 1
        return f"t{self.i}"


def lift_bytecode(bytecode):
    """
    Input: list of Instr(addr, op, args)
    Output: ir_list (list of Assign or Jmp), addr_to_index, addr_list
    """
    temps = TempGen()
    stack = []
    ir = []
    addr_list = [ins.addr for ins in bytecode]
    addr_to_index = {ins.addr: i for i, ins in enumerate(bytecode)}

    for ins in bytecode:
        op = ins.op
        if op == "PUSH_CONST":
            t = temps.new()
            ir.append(Assign(t, "CONST", [ins.args[0]]))
            stack.append(t)
        elif op == "LOAD_GLOBAL":
            t = temps.new()
            ir.append(Assign(t, "LOAD_GLOBAL", [ins.args[0]]))
            stack.append(t)
        elif op == "DUP":
            if not stack:
                stack.append(None)
            else:
                stack.append(stack[-1])
        elif op == "POP":
            if stack:
                stack.pop()
        elif op in ("ADD", "SUB", "MUL", "DIV", "EQ", "NE", "LT", "GT"):
            r = stack.pop()
            l = stack.pop()
            t = temps.new()
            ir.append(Assign(t, op, [l, r]))
            stack.append(t)
        elif op == "CALL":
            argc = ins.args[0]
            args = [stack.pop() for _ in range(argc)][::-1]
            func = stack.pop()
            t = temps.new()
            ir.append(Assign(t, "CALL", [func] + args))
            stack.append(t)
        elif op == "JMP":
            ir.append(Jmp(None, ins.args[0], False))
        elif op == "JMP_IF_FALSE":
            cond = stack.pop()
            ir.append(Jmp(cond, ins.args[0], True))
        elif op == "RET":
            val = stack.pop() if stack else None
            ir.append(Assign("ret", "RET", [val]))
        else:
            # blackbox / unknown
            t = temps.new()
            ir.append(Assign(t, "BBX_" + op, ins.args))
            stack.append(t)
    return ir, addr_to_index, addr_list


def find_leaders(ir, addr_list, addr_to_index):
    """
    Heuristics:
    - first instruction is leader
    - any jump target is leader
    - instruction immediately following a conditional or unconditional jump is leader (possible fall-through)
    We'll map IR indices to the originating bytecode addresses via addr_list.
    For simplicity assume IR[i] corresponds to bytecode[i] (since lift preserves order).
    """
    leaders = set()
    if not addr_list:
        return leaders
    leaders.add(addr_list[0])
    for i, addr in enumerate(addr_list):
        if i >= len(ir):
            break
        instr = ir[i]
        if isinstance(instr, Jmp):
            # target is leader
            leaders.add(instr.target)
            # next instr (fall-through) is leader if exists
            if i + 1 < len(addr_list):
                leaders.add(addr_list[i + 1])
    return leaders


def split_basic_blocks(ir, addr_list):
    # build mapping addr->ir_index (we assume 1-to-1)
    addr_to_idx = {addr_list[i]: i for i in range(len(addr_list))}
    leaders = find_leaders(ir, addr_list, addr_to_idx)
    # sort leaders by position
    leader_idxs = sorted([addr_to_idx[a] for a in leaders])
    # create blocks: from each leader idx to just before next leader idx
    blocks = {}
    for i, start_idx in enumerate(leader_idxs):
        end_idx = leader_idxs[i + 1] if i + 1 < len(leader_idxs) else len(ir)
        name = f"BB{start_idx}"
        blocks[name] = {
            "start": start_idx,
            "end": end_idx,
            "instrs": ir[start_idx:end_idx],
            "succ": set(),
            "pred": set(),
            "addr": addr_list[start_idx],
        }
    # build CFG edges
    addr_by_idx = {i: addr_list[i] for i in range(len(addr_list))}

    # helper: find block name by ir index
    def block_of(idx):
        for bname, b in blocks.items():
            if b["start"] <= idx < b["end"]:
                return bname
        return None

    for bname, b in blocks.items():
        last_idx = b["end"] - 1
        if last_idx < 0 or last_idx >= len(ir):
            continue
        last_instr = ir[last_idx]
        if isinstance(last_instr, Jmp):
            # edge to target
            target_addr = last_instr.target
            if target_addr in addr_to_idx:
                target_idx = addr_to_idx[target_addr]
                tgt_blk = block_of(target_idx)
                if tgt_blk:
                    b["succ"].add(tgt_blk)
                    blocks[tgt_blk]["pred"].add(bname)
            # if conditional, also fall-through to next instr
            if last_instr.is_cond:
                next_idx = last_idx + 1
                if next_idx < len(ir):
                    fall_blk = block_of(next_idx)
                    if fall_blk:
                        b["succ"].add(fall_blk)
                        blocks[fall_blk]["pred"].add(bname)
        else:
            # fall-through to next block if exists
            next_idx = last_idx + 1
            if next_idx < len(ir):
                nt = block_of(next_idx)
                if nt:
                    b["succ"].add(nt)
                    blocks[nt]["pred"].add(bname)
    return blocks


def analyze_use_counts(ir):
    uses = defaultdict(int)
    defs = {}
    for instr in ir:
        if isinstance(instr, Assign):
            if instr.dst != "ret":
                defs[instr.dst] = instr
            for a in instr.args:
                if isinstance(a, str) and a.startswith("t"):
                    uses[a] += 1
        elif isinstance(instr, Jmp):
            if instr.cond and isinstance(instr.cond, str) and instr.cond.startswith("t"):
                uses[instr.cond] += 1
    return uses, defs


# simple expression renderer with inlining for temps used once
def render_expr(operand, defs, uses):
    # operand: None or temp like "t1" or literal
    if operand is None:
        return "undefined"
    if not (isinstance(operand, str) and operand.startswith("t")):
        # literal or global name
        return (
            repr(operand) if not (isinstance(operand, str) and operand.isidentifier()) else operand
        )
    # temp: check its defining instruction
    if operand not in defs:
        return operand
    instr = defs[operand]
    # if temp used only once, inline
    if uses.get(operand, 0) <= 1:
        op = instr.op
        args = instr.args
        if op == "CONST":
            return repr(args[0])
        if op == "LOAD_GLOBAL":
            return args[0]
        if op == "CALL":
            func = render_expr(args[0], defs, uses)
            arg_strs = [render_expr(a, defs, uses) for a in args[1:]]
            return f"{func}({', '.join(arg_strs)})"
        if op in ("ADD", "SUB", "MUL", "DIV", "EQ", "NE", "LT", "GT"):
            left = render_expr(args[0], defs, uses)
            right = render_expr(args[1], defs, uses)
            opmap = {
                "ADD": "+",
                "SUB": "-",
                "MUL": "*",
                "DIV": "/",
                "EQ": "==",
                "NE": "!=",
                "LT": "<",
                "GT": ">",
            }
            return f"({left} {opmap.get(op,op)} {right})"
        return f"{op}({', '.join(map(str,args))})"
    else:
        # not inlining: print temp name
        return operand


def pretty_print_blocks(blocks, defs, uses):
    out = []
    for name, b in sorted(blocks.items(), key=lambda kv: kv[1]["start"]):
        out.append(f"// {name}  (addr={b['addr']})")
        for instr in b["instrs"]:
            if isinstance(instr, Assign):
                if instr.op == "CONST":
                    out.append(f"var {instr.dst} = {repr(instr.args[0])};")
                elif instr.op == "LOAD_GLOBAL":
                    out.append(f"var {instr.dst} = {instr.args[0]};")
                elif instr.op == "CALL":
                    expr = render_expr(instr.dst, defs, uses)  # will usually be tN
                    func = render_expr(instr.args[0], defs, uses)
                    args = ", ".join(render_expr(a, defs, uses) for a in instr.args[1:])
                    out.append(f"var {instr.dst} = {func}({args});")
                elif instr.op == "RET":
                    out.append(f"return {render_expr(instr.args[0], defs, uses)};")
                else:
                    # binary ops or unknown
                    if instr.op in ("ADD", "SUB", "MUL", "DIV", "EQ", "NE", "LT", "GT"):
                        a = render_expr(instr.args[0], defs, uses)
                        b2 = render_expr(instr.args[1], defs, uses)
                        opmap = {
                            "ADD": "+",
                            "SUB": "-",
                            "MUL": "*",
                            "DIV": "/",
                            "EQ": "==",
                            "NE": "!=",
                            "LT": "<",
                            "GT": ">",
                        }
                        out.append(f"var {instr.dst} = {a} {opmap.get(instr.op,instr.op)} {b2};")
                    else:
                        # fallback
                        args_repr = ", ".join(map(str, instr.args))
                        out.append(f"var {instr.dst} = {instr.op}({args_repr});")
            elif isinstance(instr, Jmp):
                if instr.is_cond:
                    cond_expr = render_expr(instr.cond, defs, uses)
                    out.append(f"if (!{cond_expr}) goto L_{instr.target};")
                else:
                    out.append(f"goto L_{instr.target};")
        # print successors as comment
        succs = ", ".join(sorted(b["succ"]))
        if succs:
            out.append(f"// succ -> {succs}")
        out.append("")
    return "\n".join(out)


# ---------------- demo ----------------
if __name__ == "__main__":
    # sample bytecode: compute print(10+20)
    bc = [
        Instr(0, "PUSH_CONST", [10]),
        Instr(1, "PUSH_CONST", [20]),
        Instr(2, "ADD", []),
        Instr(3, "LOAD_GLOBAL", ["print"]),
        # Instr(4, "DUP", []),   # ← 去掉它
        Instr(4, "CALL", [1]),  # 栈顶此时为 [..., print, 30]
        Instr(5, "RET", []),
    ]

    ir, addr_to_index, addr_list = lift_bytecode(bc)
    blocks = split_basic_blocks(ir, addr_list)
    uses, defs = analyze_use_counts(ir)
    output = pretty_print_blocks(blocks, defs, uses)
    print(output)
