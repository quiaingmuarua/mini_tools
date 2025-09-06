# ---------- Token ----------
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Kind(Enum):
    # keywords
    KW_INT = auto()
    KW_RETURN = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    # identifiers & literals
    IDENT = auto()
    INT_LIT = auto()
    # operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQ = auto()
    EQEQ = auto()
    BANGEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()
    # punct
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    SEMI = auto()
    EOF = auto()


KEYWORDS = {
    "int": Kind.KW_INT,
    "return": Kind.KW_RETURN,
    "if": Kind.KW_IF,
    "else": Kind.KW_ELSE,
    "while": Kind.KW_WHILE,
}


@dataclass
class Token:
    kind: Kind
    lexeme: str
    line: int
    col: int
    value: int | None = None  # only for INT_LIT


# ---------- Lexer ----------
class Lexer:
    def __init__(self, src: str):
        self.src = src
        self.i = 0
        self.line = 1
        self.col = 1

    def _eof(self):
        return self.i >= len(self.src)

    def _peek(self, k=0):
        return "\0" if self.i + k >= len(self.src) else self.src[self.i + k]

    def _adv(self):
        ch = self._peek()
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _match(self, s: str) -> bool:
        if self.src.startswith(s, self.i):
            for _ in s:
                self._adv()
            return True
        return False

    def _skip_ws_and_comments(self):
        while True:
            ch = self._peek()
            # whitespace
            if ch in " \t\r\n":
                self._adv()
                continue
            # // line comment
            if ch == "/" and self._peek(1) == "/":
                while not self._eof() and self._peek() != "\n":
                    self._adv()
                continue
            # /* block comment */
            if ch == "/" and self._peek(1) == "*":
                self._adv()
                self._adv()
                while not self._eof() and not (
                    self._peek() == "*" and self._peek(1) == "/"
                ):
                    self._adv()
                if not self._eof():
                    self._adv()
                    self._adv()
                continue
            break

    def _read_ident_or_kw(self):
        start_i, start_col, start_line = self.i, self.col, self.line
        while self._peek().isalnum() or self._peek() == "_":
            self._adv()
        lex = self.src[start_i : self.i]
        kind = KEYWORDS.get(lex, Kind.IDENT)
        return Token(kind, lex, start_line, start_col)

    def _read_number(self):
        start_i, start_col, start_line = self.i, self.col, self.line
        # 十进制整数
        while self._peek().isdigit():
            self._adv()
        lex = self.src[start_i : self.i]
        return Token(Kind.INT_LIT, lex, start_line, start_col, value=int(lex))

    def next(self) -> Token:
        self._skip_ws_and_comments()
        if self._eof():
            return Token(Kind.EOF, "", self.line, self.col)

        ch = self._peek()
        line, col = self.line, self.col

        # identifiers / keywords
        if ch.isalpha() or ch == "_":
            return self._read_ident_or_kw()

        # numbers
        if ch.isdigit():
            return self._read_number()

        # two-char ops
        if self._match("=="):
            return Token(Kind.EQEQ, "==", line, col)
        if self._match("!="):
            return Token(Kind.BANGEQ, "!=", line, col)
        if self._match("<="):
            return Token(Kind.LTE, "<=", line, col)
        if self._match(">="):
            return Token(Kind.GTE, ">=", line, col)

        # single-char
        ch = self._adv()
        table = {
            "+": Kind.PLUS,
            "-": Kind.MINUS,
            "*": Kind.STAR,
            "/": Kind.SLASH,
            "%": Kind.PERCENT,
            "=": Kind.EQ,
            "<": Kind.LT,
            ">": Kind.GT,
            "(": Kind.LPAREN,
            ")": Kind.RPAREN,
            "{": Kind.LBRACE,
            "}": Kind.RBRACE,
            ",": Kind.COMMA,
            ";": Kind.SEMI,
        }
        if ch in table:
            return Token(table[ch], ch, line, col)

        raise SyntaxError(f"Unexpected char {repr(ch)} at {line}:{col}")


if __name__ == "__main__":
    src = r"""
    int add(int a, int b) { return a + b; }

    int main() {
      int x = 2;
      int y = 3;  // comment
      int z = add(x, y);
      if (z == 5) { z = z + 1; } else { z = 0; }
      while (z > 0) { z = z - 1; }
      return z;
    }
    """
    lx = Lexer(src)
    toks = []
    while True:
        t = lx.next()
        toks.append(t)
        if t.kind == Kind.EOF:
            break

    # 简洁打印
    for t in toks[:40]:
        val = f"={t.value}" if t.kind == Kind.INT_LIT else ""
        print(f"{t.kind.name}:{t.lexeme}{val}", end="  ")
    print("\n(total:", len(toks), "tokens)")
