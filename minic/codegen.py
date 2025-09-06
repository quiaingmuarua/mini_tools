from llvmlite import binding, ir

from minic.runtime import declare_printf, intern_cstr


# ---------- 1) AST ----------
class Node:
    pass


class Expr(Node):
    pass


class Stmt(Node):
    pass


class IntLit(Expr):  # 常量
    def __init__(self, value: int):
        self.value = value


class Var(Expr):  # 变量读
    def __init__(self, name: str):
        self.name = name


class BinaryOp(Expr):  # + - * /
    def __init__(self, op: str, lhs: Expr, rhs: Expr):
        self.op, self.lhs, self.rhs = op, lhs, rhs


class Compare(Expr):  # == != < <= > >=
    def __init__(self, op: str, lhs: Expr, rhs: Expr):
        self.op, self.lhs, self.rhs = op, lhs, rhs  # 结果类型：i1


class VarDecl(Stmt):  # int x = init;
    def __init__(self, name: str, init: Expr):
        self.name, self.init = name, init


class Assign(Stmt):  # x = expr;
    def __init__(self, name: str, expr: Expr):
        self.name, self.expr = name, expr


class Return(Stmt):  # return expr;
    def __init__(self, expr: Expr):
        self.expr = expr


class Block(Stmt):  # { ... }
    def __init__(self, stmts):
        self.stmts = stmts


class IfElse(Stmt):  # if (cond) then_block else else_block
    def __init__(self, cond: Expr, then_blk: Block, else_blk: Block):
        self.cond, self.then_blk, self.else_blk = cond, then_blk, else_blk


class While(Stmt):
    def __init__(self, cond: Expr, body: Block):
        self.cond, self.body = cond, body


class Call(Expr):
    def __init__(self, name: str, args: list[Expr]):
        self.name = name
        self.args = args


class Function(Node):
    def __init__(self, name: str, params: list[str], body: Block):
        self.name = name
        self.params = params
        self.body = body


class Program(Node):
    def __init__(self, funcs: list[Function]):
        self.funcs = funcs  # 修正：从 func 改为 funcs


class PrintI32(Stmt):
    def __init__(self, expr: Expr):
        self.expr = expr


class UnaryOp(Expr):
    def __init__(self, op: str, expr: Expr):
        self.op, self.expr = op, expr


# ---------- 2) Codegen ----------
i32 = ir.IntType(32)
binding.initialize()
binding.initialize_native_target()
binding.initialize_native_asmprinter()


class Codegen:
    def __init__(self):
        self.module = ir.Module(name="minic")

        # 设置目标平台信息
        triple = binding.get_default_triple()
        self.module.triple = triple
        tm = binding.Target.from_triple(triple).create_target_machine()
        self.module.data_layout = str(tm.target_data)

        self.vars = {}  # name -> alloca ptr
        self.funcs = {}  # 函数名 -> ir.Function
        self.fn = None  # 当前函数
        self.builder = None  # 当前构建器
        self.alloca_builder = None  # 分配构建器
        self._fmt_int = None  # 缓存 "%d\n" 的全局常量

    @property
    def safe_builder(self):
        assert self.builder is not None, "builder must be initialized"
        return self.builder

    @property
    def safe_alloca_builder(self):
        assert self.alloca_builder is not None, "alloca_builder must be initialized"
        return self.alloca_builder

    @property
    def safe_fn(self):
        assert self.fn is not None, "fn must be initialized"
        return self.fn

    def alloca_i32(self, name: str):
        # 在 entry 的跳转之前插入
        return self.safe_alloca_builder.alloca(i32, name=name)

    # ---- expr ----
    def codegen_expr(self, node: Expr):
        if isinstance(node, IntLit):
            return ir.Constant(i32, node.value)
        if isinstance(node, Var):
            ptr = self.vars[node.name]
            return self.safe_builder.load(ptr, name=node.name)
        if isinstance(node, BinaryOp):
            lv = self.codegen_expr(node.lhs)
            rv = self.codegen_expr(node.rhs)
            if node.op == "+":
                return self.safe_builder.add(lv, rv, name="addtmp")
            if node.op == "-":
                return self.safe_builder.sub(lv, rv, name="subtmp")
            if node.op == "*":
                return self.safe_builder.mul(lv, rv, name="multmp")
            if node.op == "/":
                return self.safe_builder.sdiv(lv, rv, name="divtmp")
            raise ValueError(f"unsupported op {node.op}")
        if isinstance(node, Compare):
            lv = self.codegen_expr(node.lhs)
            rv = self.codegen_expr(node.rhs)
            # i1 返回值（布尔）
            if node.op in ("==", "!=", "<", "<=", ">", ">="):
                return self.safe_builder.icmp_signed(node.op, lv, rv, name="cmptmp")
            raise ValueError(f"unsupported cmp {node.op}")
        if isinstance(node, Call):
            # 处理函数调用
            func = self.funcs[node.name]
            args = [self.codegen_expr(arg) for arg in node.args]
            return self.safe_builder.call(func, args, name="calltmp")
        if isinstance(node, UnaryOp):
            v = self.codegen_expr(node.expr)
            if node.op == "-":
                return self.safe_builder.sub(ir.Constant(i32, 0), v, name="negtmp")
            raise ValueError(f"unsupported unary {node.op}")
        raise TypeError(f"unknown expr {node}")

    # ---- stmt ----
    def codegen_stmt(self, st: Stmt):
        if isinstance(st, VarDecl):
            ptr = self.alloca_i32(st.name)
            initv = self.codegen_expr(st.init)
            self.safe_builder.store(initv, ptr)
            self.vars[st.name] = ptr
            return
        if isinstance(st, Assign):
            ptr = self.vars[st.name]
            val = self.codegen_expr(st.expr)
            self.safe_builder.store(val, ptr)
            return
        if isinstance(st, Return):
            val = self.codegen_expr(st.expr)
            self.safe_builder.ret(val)
            return
        if isinstance(st, Block):
            for s in st.stmts:
                self.codegen_stmt(s)
            return
        if isinstance(st, IfElse):
            condv = self.codegen_expr(st.cond)  # i1

            then_bb = self.safe_fn.append_basic_block("then")
            else_bb = self.safe_fn.append_basic_block("else")
            merge_bb = self.safe_fn.append_basic_block("merge")

            # 条件跳转
            self.safe_builder.cbranch(condv, then_bb, else_bb)

            # then
            self.safe_builder.position_at_end(then_bb)
            self.codegen_stmt(st.then_blk)
            if self.safe_builder.block.terminator is None:
                self.safe_builder.branch(merge_bb)

            # else
            self.safe_builder.position_at_end(else_bb)
            self.codegen_stmt(st.else_blk)
            if self.safe_builder.block.terminator is None:
                self.safe_builder.branch(merge_bb)

            # merge
            self.safe_builder.position_at_end(merge_bb)
            return
        if isinstance(st, While):
            # 基本块：cond -> body -> back_to_cond / after
            cond_bb = self.safe_fn.append_basic_block("loop.cond")
            body_bb = self.safe_fn.append_basic_block("loop.body")
            after_bb = self.safe_fn.append_basic_block("loop.after")

            # 跳到 cond
            self.safe_builder.branch(cond_bb)

            # cond: 计算条件并条件跳转
            self.safe_builder.position_at_end(cond_bb)
            condv = self.codegen_expr(st.cond)  # i1
            self.safe_builder.cbranch(condv, body_bb, after_bb)

            # body: 执行循环体，末尾回到 cond
            self.safe_builder.position_at_end(body_bb)
            self.codegen_stmt(st.body)
            if self.safe_builder.block.terminator is None:
                self.safe_builder.branch(cond_bb)

            # after: 继续往后
            self.safe_builder.position_at_end(after_bb)
            return
        if isinstance(st, PrintI32):
            v = self.codegen_expr(st.expr)  # 必须是 i32
            self._print_i32(v)
            return

        raise TypeError(f"unknown stmt {st}")

    # --- 声明所有函数原型 ---
    def declare_prototypes(self, prog: Program):
        for fn in prog.funcs:
            # TODO: 形参全是 i32
            param_types = [i32] * len(fn.params)
            fnty = ir.FunctionType(i32, param_types)
            self.funcs[fn.name] = ir.Function(self.module, fnty, name=fn.name)

    # --- 定义某个函数体 ---
    def define_function(self, fn_ast: Function):
        self.fn = self.funcs[fn_ast.name]
        self.vars = {}

        # 建两个基本块：entry 只放 allocas；跳到 body
        entry = self.safe_fn.append_basic_block("entry")
        body = self.safe_fn.append_basic_block("body")

        entry_builder = ir.IRBuilder(entry)
        prologue_br = entry_builder.branch(body)

        self.builder = ir.IRBuilder(body)
        self.alloca_builder = ir.IRBuilder(entry)
        self.safe_alloca_builder.position_before(prologue_br)

        # 形参：为每个参数分配一个 alloca，并把 %arg 值存进去
        for i, pname in enumerate(fn_ast.params):
            ptr = self.alloca_i32(pname)
            # self.safe_fn.args[i] 就是该参数的 SSA 值
            self.safe_fn.args[i].name = pname
            entry_builder.store(self.safe_fn.args[i], ptr)
            self.vars[pname] = ptr

        # 生成函数体语句
        self.codegen_stmt(fn_ast.body)

        # 安全兜底：若没有 ret，补一个 ret 0（避免 verify 报错）
        if self.safe_builder.block.terminator is None:
            self.safe_builder.ret(ir.Constant(i32, 0))

    def codegen(self, prog: Program) -> str:
        self.declare_prototypes(prog)
        for fn in prog.funcs:
            self.define_function(fn)
        return str(self.module)

    def codegen_block(self, program: Block) -> str:
        # 为独立的代码块创建一个完整的函数环境
        # 创建一个 main 函数来包装这个代码块
        fnty = ir.FunctionType(i32, [])
        self.fn = ir.Function(self.module, fnty, name="main")
        self.vars = {}

        # 建两个基本块：entry 只放 allocas；跳到 body
        entry = self.safe_fn.append_basic_block("entry")
        body = self.safe_fn.append_basic_block("body")

        entry_builder = ir.IRBuilder(entry)
        prologue_br = entry_builder.branch(body)

        self.builder = ir.IRBuilder(body)
        self.alloca_builder = ir.IRBuilder(entry)
        self.safe_alloca_builder.position_before(prologue_br)

        # 生成代码块语句
        self.codegen_stmt(program)

        # 安全兜底：若没有 ret，补一个 ret 0（避免 verify 报错）
        if self.safe_builder.block.terminator is None:
            self.safe_builder.ret(ir.Constant(i32, 0))

        return str(self.module)

    def _print_i32(self, val: ir.Value):
        printf = declare_printf(self.module)
        if self._fmt_int is None:
            self._fmt_int = intern_cstr(self.module, "%d\n", "fmt_int")
        zero = ir.Constant(ir.IntType(32), 0)
        # 取到全局数组的首元素地址：getelementptr [N x i8], [N x i8]* @fmt_int, i32 0, i32 0
        fmt_ptr = self.safe_builder.gep(self._fmt_int, [zero, zero], inbounds=True)
        self.safe_builder.call(printf, [fmt_ptr, val])


# ---------- 3) Driver ----------
def generate_ir(program: Program) -> str:
    return Codegen().codegen(program)


def generate_block_ir(program: Block) -> str:
    return Codegen().codegen_block(program)
