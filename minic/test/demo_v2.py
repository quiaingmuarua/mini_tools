# mini_c.py
# A tiny C-like toy using llvmlite: int main(){...}
# Features: int, identifiers, decl/assign, blocks, if, while, return, calls(putint)
# Run: python mini_c.py

import ctypes
import sys

from llvmlite import binding as llvm
from llvmlite import ir

# ------------ LEXER ------------
KEYWORDS = {"int", "return", "if", "else", "while", "break", "continue"}
TYPES = {"int"}


class Token:
    def __init__(self, kind, value=None):
        self.kind = kind  # e.g. 'INT', 'IDENT', 'NUMBER', '+', '==', '{', ...
        self.value = value

    def __repr__(self):
        return f"Token({self.kind},{self.value})"


class Lexer:
    def __init__(self, src):
        self.src = src
        self.i = 0
        self.n = len(src)

    def _peek(self, k=0):
        j = self.i + k
        return self.src[j] if j < self.n else "\0"

    def _advance(self):
        ch = self._peek()
        if ch != "\0":
            self.i += 1
        return ch

    def _consume_while(self, pred):
        s = []
        while pred(self._peek()):
            s.append(self._advance())
        return "".join(s)

    def tokens(self):
        tks = []
        while True:
            ch = self._peek()
            if ch == "\0":
                tks.append(Token("EOF"))
                break
            if ch.isspace():
                self._advance()
                continue
            if ch.isalpha() or ch == "_":
                ident = self._consume_while(lambda c: c.isalnum() or c == "_")
                if ident in KEYWORDS:
                    tks.append(Token(ident.upper()))  # 'INT','RETURN','IF','ELSE','WHILE'
                else:
                    tks.append(Token("IDENT", ident))
                continue
            if ch.isdigit():
                num = self._consume_while(lambda c: c.isdigit())
                tks.append(Token("NUMBER", int(num)))
                continue

            # --- handle comments ---
            two = ch + self._peek(1)
            if two == "//":
                # skip till end of line
                self._advance()
                self._advance()
                while self._peek() not in ("\n", "\r", "\0"):
                    self._advance()
                continue
            if two == "/*":
                # skip block comment
                self._advance()
                self._advance()
                while True:
                    if self._peek() == "\0":
                        raise SyntaxError("Unterminated block comment")
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance()
                        self._advance()
                        break
                    self._advance()
                continue

            if two in ("==", "!=", "<=", ">="):
                tks.append(Token(two))
                self._advance()
                self._advance()
                continue

            if ch in "{}();=+-*/<>,":
                tks.append(Token(ch))
                self._advance()
                continue

            raise SyntaxError(f"Unexpected char: {ch}")
        return tks


# ------------ AST NODES ------------
class Node:
    pass


class Number(Node):
    def __init__(self, v):
        self.v = v


class Var(Node):
    def __init__(self, name):
        self.name = name


class BinOp(Node):
    def __init__(self, op, a, b):
        self.op, self.a, self.b = op, a, b


class Assign(Node):
    def __init__(self, name, expr):
        self.name, self.expr = name, expr


class VarDecl(Node):
    def __init__(self, name, init):
        self.name, self.init = name, init


class Return(Node):
    def __init__(self, expr):
        self.expr = expr


class If(Node):
    def __init__(self, cond, then, els):
        self.cond, self.then, self.els = cond, then, els


class While(Node):
    def __init__(self, cond, body):
        self.cond, self.body = cond, body


class Block(Node):
    def __init__(self, stmts):
        self.stmts = stmts


class Call(Node):
    def __init__(self, name, args):
        self.name, self.args = name, args


class Function(Node):
    def __init__(self, name, body):
        self.name, self.body = name, body


class Break(Node):
    pass


class Continue(Node):
    pass


# ------------ PARSER (recursive descent with precedence) ------------
class Parser:
    def __init__(self, tokens):
        self.tks = tokens
        self.i = 0

    def _peek(self, k=0):
        return self.tks[self.i + k]

    def _eat(self, kind=None):
        tk = self._peek()
        if kind and tk.kind != kind:
            raise SyntaxError(f"Expected {kind}, got {tk}")
        self.i += 1
        return tk

    # program := 'INT' 'main' '(' ')' block
    def parse_program(self):
        self._eat("INT")
        ident = self._eat("IDENT")
        if ident.value != "main":
            raise SyntaxError("Only 'int main()' supported in this toy.")
        self._eat("(")
        self._eat(")")
        body = self.parse_block()
        return Function("main", body)

    def parse_block(self):
        self._eat("{")
        stmts = []
        while self._peek().kind != "}":
            stmts.append(self.parse_stmt())
        self._eat("}")
        return Block(stmts)

    def parse_stmt(self):
        k = self._peek().kind
        if k == ";":
            self._eat(";")
            return Block([])  # empty statement
        if k == "INT":
            self._eat("INT")
            name = self._eat("IDENT").value
            init = None
            if self._peek().kind == "=":
                self._eat("=")
                init = self.parse_expr()
            self._eat(";")
            return VarDecl(name, init)
        if k == "RETURN":
            self._eat("RETURN")
            expr = self.parse_expr()
            self._eat(";")
            return Return(expr)
        if k == "IF":
            self._eat("IF")
            self._eat("(")
            cond = self.parse_expr()
            self._eat(")")
            then = self.parse_stmt()
            els = None
            if self._peek().kind == "ELSE":
                self._eat("ELSE")
                els = self.parse_stmt()
            return If(cond, then, els)
        if k == "WHILE":
            self._eat("WHILE")
            self._eat("(")
            cond = self.parse_expr()
            self._eat(")")
            body = self.parse_stmt()
            return While(cond, body)
        if k == "{":
            return self.parse_block()
        if k == "BREAK":
            self._eat("BREAK")
            self._eat(";")
            return Break()
        if k == "CONTINUE":
            self._eat("CONTINUE")
            self._eat(";")
            return Continue()

        # assignment or expr-stmt
        if k == "IDENT" and self._peek(1).kind == "=":
            name = self._eat("IDENT").value
            self._eat("=")
            expr = self.parse_expr()
            self._eat(";")
            return Assign(name, expr)
        expr = self.parse_expr()
        self._eat(";")
        return expr  # expression statement (e.g., call)

    # expr precedence: equality > relational > add > mul > unary > primary
    def parse_expr(self):
        return self.parse_equality()

    def parse_equality(self):
        node = self.parse_rel()
        while self._peek().kind in ("==", "!="):
            op = self._eat().kind
            rhs = self.parse_rel()
            node = BinOp(op, node, rhs)
        return node

    def parse_rel(self):
        node = self.parse_add()
        while self._peek().kind in ("<", ">", "<=", ">="):
            op = self._eat().kind
            rhs = self.parse_add()
            node = BinOp(op, node, rhs)
        return node

    def parse_add(self):
        node = self.parse_mul()
        while self._peek().kind in ("+", "-"):
            op = self._eat().kind
            rhs = self.parse_mul()
            node = BinOp(op, node, rhs)
        return node

    def parse_mul(self):
        node = self.parse_unary()
        while self._peek().kind in ("*", "/"):
            op = self._eat().kind
            rhs = self.parse_unary()
            node = BinOp(op, node, rhs)
        return node

    def parse_unary(self):
        if self._peek().kind in ("+", "-"):
            op = self._eat().kind
            rhs = self.parse_unary()
            # encode unary as (0 +/- rhs)
            zero = Number(0)
            return BinOp(op, zero, rhs)
        return self.parse_primary()

    def parse_primary(self):
        tk = self._peek()
        if tk.kind == "NUMBER":
            self._eat("NUMBER")
            return Number(tk.value)
        if tk.kind == "IDENT":
            ident = self._eat("IDENT").value
            if self._peek().kind == "(":
                self._eat("(")
                args = []
                if self._peek().kind != ")":
                    args.append(self.parse_expr())
                    while self._peek().kind == ",":
                        self._eat(",")
                        args.append(self.parse_expr())
                self._eat(")")
                return Call(ident, args)
            return Var(ident)
        if tk.kind == "(":
            self._eat("(")
            e = self.parse_expr()
            self._eat(")")
            return e
        raise SyntaxError(f"Unexpected token in primary: {tk}")


# ------------ CODEGEN ------------
i32 = ir.IntType(32)
i1 = ir.IntType(1)


class CodeGen:
    def __init__(self):
        self.module = ir.Module(name="mini_c")
        self.builder = None
        self.func = None
        self.env_stack = []  # list of dicts: name -> alloca

        # declare external putint(i32) -> i32
        self.putint_ty = ir.FunctionType(i32, [i32])
        self.putint_fn = ir.Function(self.module, self.putint_ty, name="putint")
        self.break_stack = []
        self.continue_stack = []

    def push_env(self):
        self.env_stack.append({})

    def pop_env(self):
        self.env_stack.pop()

    def env(self):
        return self.env_stack[-1]

    def lookup(self, name):
        for env in reversed(self.env_stack):
            if name in env:
                return env[name]
        raise NameError(f"Undefined variable: {name}")

    def create_entry_alloca(self, name):
        # allocate in entry block
        with self.builder.goto_entry_block():
            ptr = self.builder.alloca(i32, name=name)
        return ptr

    def codegen(self, node):
        if isinstance(node, Function):
            fnty = ir.FunctionType(i32, [])
            self.func = ir.Function(self.module, fnty, name=node.name)
            block = self.func.append_basic_block(name="entry")
            self.builder = ir.IRBuilder(block)
            self.push_env()
            # body
            rv = self.codegen(node.body)
            # ensure function is properly terminated
            if not self.builder.block.is_terminated:
                self.builder.ret(i32(0))
            self.pop_env()
            return self.func

        if isinstance(node, Block):
            self.push_env()
            for s in node.stmts:
                self.codegen(s)
            self.pop_env()
            return None

        if isinstance(node, VarDecl):
            ptr = self.create_entry_alloca(node.name)
            self.env()[node.name] = ptr
            init_val = self.codegen(node.init) if node.init else i32(0)
            self.builder.store(init_val, ptr)
            return None

        if isinstance(node, Assign):
            ptr = self.lookup(node.name)
            val = self.codegen(node.expr)
            self.builder.store(val, ptr)
            return val

        if isinstance(node, Return):
            val = self.codegen(node.expr)
            self.builder.ret(val)
            return None

        if isinstance(node, If):
            cond = self.codegen(node.cond)
            cond_bool = self._truth(cond)
            then_bb = self.func.append_basic_block("then")
            else_bb = self.func.append_basic_block("else") if node.els else None
            end_bb = self.func.append_basic_block("ifend")

            if else_bb:
                self.builder.cbranch(cond_bool, then_bb, else_bb)
            else:
                self.builder.cbranch(cond_bool, then_bb, end_bb)

            # then
            self.builder.position_at_end(then_bb)
            self.codegen(node.then)
            if not self.builder.block.is_terminated:
                self.builder.branch(end_bb)

            # else
            if else_bb:
                self.builder.position_at_end(else_bb)
                self.codegen(node.els)
                if not self.builder.block.is_terminated:
                    self.builder.branch(end_bb)

            # end
            self.builder.position_at_end(end_bb)
            return None

        if isinstance(node, While):
            cond_bb = self.func.append_basic_block("while.cond")
            body_bb = self.func.append_basic_block("while.body")
            end_bb = self.func.append_basic_block("while.end")
            self.builder.branch(cond_bb)

            # cond
            self.builder.position_at_end(cond_bb)
            cond = self._truth(self.codegen(node.cond))
            self.builder.cbranch(cond, body_bb, end_bb)

            # body
            self.builder.position_at_end(body_bb)
            self.codegen(node.body)
            if not self.builder.block.is_terminated:
                self.builder.branch(cond_bb)

            # end
            self.builder.position_at_end(end_bb)
            return None

        if isinstance(node, BinOp):
            a = self.codegen(node.a)
            b = self.codegen(node.b)
            if node.op in ("+", "-", "*", "/"):
                ops = {
                    "+": self.builder.add,
                    "-": self.builder.sub,
                    "*": self.builder.mul,
                    "/": self.builder.sdiv,
                }
                return ops[node.op](a, b)
            elif node.op in ("<", ">", "<=", ">=", "==", "!="):
                return self.builder.zext(self.builder.icmp_signed(node.op, a, b), i32)
            else:
                raise NotImplementedError(node.op)

        if isinstance(node, Number):
            return ir.Constant(i32, node.v)

        if isinstance(node, Var):
            ptr = self.lookup(node.name)
            return self.builder.load(ptr, name=node.name)

        if isinstance(node, Call):
            callee = node.name
            argsv = [self.codegen(arg) for arg in node.args]
            if callee == "print":
                # map print(x) to putint(x)
                return self.builder.call(self.putint_fn, argsv)
            # TODO(1): 允许调用更多外部函数（如 putchard(double) 等）
            # 提示：像 putint 一样先声明，再 call。
            fn = self.module.globals.get(callee, None)
            if not isinstance(fn, ir.Function):
                raise NameError(f"Unknown function: {callee}")
            return self.builder.call(fn, argsv)

        raise NotImplementedError(type(node))

    def _truth(self, val_i32):
        zero = ir.Constant(i32, 0)
        cmp = self.builder.icmp_signed("!=", val_i32, zero)  # ← 这里用 '!='
        return cmp


# ------------ JIT UTILS ------------
def create_execution_engine():
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()
    target = llvm.Target.from_default_triple()
    tm = target.create_target_machine()
    backing = llvm.parse_assembly("")
    engine = llvm.create_mcjit_compiler(backing, tm)
    return engine


# Keep CFUNCTYPE alive
PUTINT_CFUNC = None


def register_python_symbols():
    global PUTINT_CFUNC

    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
    def putint(n):
        print(n)
        return 0

    PUTINT_CFUNC = putint
    llvm.add_symbol("putint", ctypes.cast(PUTINT_CFUNC, ctypes.c_void_p).value)


def compile_ir(engine, llvm_ir):
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    return mod


# ------------ DRIVER ------------
def compile_and_run(source):
    # 1. lex & parse
    toks = Lexer(source).tokens()
    ast = Parser(toks).parse_program()

    # 2. codegen
    cg = CodeGen()
    cg.codegen(ast)

    # 3. JIT
    engine = create_execution_engine()
    register_python_symbols()
    llvm_ir = str(cg.module)
    compile_ir(engine, llvm_ir)

    # 4. get address & call
    func_ptr = engine.get_function_address("main")
    cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(func_ptr)
    rv = cfunc()
    return rv, llvm_ir


# ------------ DEMO ------------
DEMO = r"""
int main() {
    int i = 0;
    while (i < 5) {
        print(i);      
        i = i + 1;
    }
    if (i == 5) {
        print(999); //print
    } else {
        print(123);
    }
    return i;
}

"""

# todo
"""
break / continue
逻辑运算 && / ||（短路求值）
多个函数定义 + 调用
"""

if __name__ == "__main__":
    src = DEMO if len(sys.argv) == 1 else open(sys.argv[1], "r", encoding="utf-8").read()
    rv, ir_text = compile_and_run(src)
    print("------ return value:", rv)
    # Uncomment to inspect IR:
    # print("====== LLVM IR ======")
    # print(ir_text)
