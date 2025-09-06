# -------- Parser (recursive descent) --------
from codegen import *
from lexer import *
from runtime import *


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.cur = self.lexer.next()

    # -- utilities --
    def _eat(self, kind):
        if self.cur.kind != kind:
            raise ParseError(
                f"expected {kind.name} at {self.cur.line}:{self.cur.col}, got {self.cur.kind.name}"
            )
        t = self.cur
        self.cur = self.lexer.next()
        return t

    def _match(self, kind):
        if self.cur.kind == kind:
            return self._eat(kind)
        return None

    def _expect_ident(self):
        if self.cur.kind != Kind.IDENT:
            raise ParseError(f"expected IDENT at {self.cur.line}:{self.cur.col}")
        name = self.cur.lexeme
        self.cur = self.lexer.next()
        return name

    # -- entry --
    def parse_program(self) -> Program:
        funcs = []
        while self.cur.kind != Kind.EOF:
            funcs.append(self.parse_function())
        return Program(funcs)

    def parse_function(self) -> Function:
        self._eat(Kind.KW_INT)
        name = self._expect_ident()
        self._eat(Kind.LPAREN)
        params = []
        if self.cur.kind != Kind.RPAREN:
            params = self.parse_param_list()
        self._eat(Kind.RPAREN)
        body = self.parse_block()
        return Function(name, params, body)

    def parse_param_list(self):
        params = []
        while True:
            self._eat(Kind.KW_INT)
            pname = self._expect_ident()
            params.append(pname)
            if not self._match(Kind.COMMA):
                break
        return params

    def parse_block(self) -> Block:
        self._eat(Kind.LBRACE)
        stmts = []
        while self.cur.kind != Kind.RBRACE:
            stmts.append(self.parse_stmt())
        self._eat(Kind.RBRACE)
        return Block(stmts)

    def parse_stmt(self) -> Stmt:
        k = self.cur.kind
        if k == Kind.KW_INT:  # vardecl
            self._eat(Kind.KW_INT)
            name = self._expect_ident()
            init = IntLit(0)
            if self._match(Kind.EQ):
                init = self.parse_expr()
            self._eat(Kind.SEMI)
            return VarDecl(name, init)

        if k == Kind.KW_RETURN:
            self._eat(Kind.KW_RETURN)
            expr = self.parse_expr()
            self._eat(Kind.SEMI)
            return Return(expr)

        if k == Kind.KW_IF:
            self._eat(Kind.KW_IF)
            self._eat(Kind.LPAREN)
            cond = self.parse_expr()
            self._eat(Kind.RPAREN)
            then_blk = self.parse_stmt()
            else_blk = Block([])
            if self._match(Kind.KW_ELSE):
                else_blk = self.parse_stmt()
            return IfElse(
                cond,
                then_blk if isinstance(then_blk, Block) else Block([then_blk]),
                else_blk if isinstance(else_blk, Block) else Block([else_blk]),
            )

        if k == Kind.KW_WHILE:
            self._eat(Kind.KW_WHILE)
            self._eat(Kind.LPAREN)
            cond = self.parse_expr()
            self._eat(Kind.RPAREN)
            body = self.parse_stmt()
            return While(cond, body if isinstance(body, Block) else Block([body]))

        if k == Kind.LBRACE:
            return self.parse_block()

        # assignment: IDENT '=' expr ';'
        if k == Kind.IDENT:
            name = self._expect_ident()
            self._eat(Kind.EQ)
            expr = self.parse_expr()
            self._eat(Kind.SEMI)
            return Assign(name, expr)

        raise ParseError(
            f"unexpected token {self.cur.kind.name} at {self.cur.line}:{self.cur.col}"
        )

    # -- expressions (precedence climbing via levels) --
    def parse_expr(self):  # lowest
        return self.parse_equality()

    def parse_equality(self):
        node = self.parse_relational()
        while self.cur.kind in (Kind.EQEQ, Kind.BANGEQ):
            op = "==" if self.cur.kind == Kind.EQEQ else "!="
            self._eat(self.cur.kind)
            rhs = self.parse_relational()
            node = Compare(op, node, rhs)
        return node

    def parse_relational(self):
        node = self.parse_additive()
        while self.cur.kind in (Kind.LT, Kind.LTE, Kind.GT, Kind.GTE):
            k = self.cur.kind
            op = {Kind.LT: "<", Kind.LTE: "<=", Kind.GT: ">", Kind.GTE: ">="}[k]
            self._eat(k)
            rhs = self.parse_additive()
            node = Compare(op, node, rhs)
        return node

    def parse_additive(self):
        node = self.parse_multiplicative()
        while self.cur.kind in (Kind.PLUS, Kind.MINUS):
            op = "+" if self.cur.kind == Kind.PLUS else "-"
            self._eat(self.cur.kind)
            rhs = self.parse_multiplicative()
            node = BinaryOp(op, node, rhs)
        return node

    def parse_multiplicative(self):
        node = self.parse_primary()
        while self.cur.kind in (Kind.STAR, Kind.SLASH):
            op = "*" if self.cur.kind == Kind.STAR else "/"
            self._eat(self.cur.kind)
            rhs = self.parse_primary()
            node = BinaryOp(op, node, rhs)
        return node

    def parse_primary(self):
        if self.cur.kind == Kind.INT_LIT:
            v = self.cur.value
            self._eat(Kind.INT_LIT)
            return IntLit(v)

        if self.cur.kind == Kind.IDENT:
            name = self.cur.lexeme
            self._eat(Kind.IDENT)
            # call or variable
            if self._match(Kind.LPAREN):
                args = []
                if self.cur.kind != Kind.RPAREN:
                    args.append(self.parse_expr())
                    while self._match(Kind.COMMA):
                        args.append(self.parse_expr())
                self._eat(Kind.RPAREN)
                return Call(name, args)
            return Var(name)

        if self._match(Kind.LPAREN):
            node = self.parse_expr()
            self._eat(Kind.RPAREN)
            return node

        raise ParseError(
            f"unexpected token in primary: {self.cur.kind.name} at {self.cur.line}:{self.cur.col}"
        )

    def parse_multiplicative(self):
        node = self.parse_unary()
        while self.cur.kind in (Kind.STAR, Kind.SLASH):
            op = "*" if self.cur.kind == Kind.STAR else "/"
            self._eat(self.cur.kind)
            rhs = self.parse_unary()
            node = BinaryOp(op, node, rhs)
        return node

    def parse_unary(self):
        if self.cur.kind == Kind.MINUS:
            self._eat(Kind.MINUS)
            return UnaryOp("-", self.parse_unary())  # 右结合：-(-x) OK
        return self.parse_primary()


if __name__ == "__main__":
    src = r"""
    int main() {
      int x = -3;
      if (-x == 3) { x = x + 10; } else { x = 0; }
      return x;
    }
    """

    # 1) 词法
    lx = Lexer(src)
    # 2) 语法
    parser = Parser(lx)
    prog_ast = parser.parse_program()
    # 3) 代码生成 & 运行
    llvm_ir = generate_ir(prog_ast)
    print("=== IR ===\n", llvm_ir)
    print("exit code:", jit_run(llvm_ir))
