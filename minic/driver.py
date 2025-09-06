# driver.py
import argparse
import pathlib
import sys

from minic.codegen import Codegen
from minic.lexer import Lexer
from minic.parser import (  # 如果你没暴露 ParseError，改成: "from parser import Parser"
    ParseError,
    Parser,
)
from minic.runtime import (
    emit_assembly,
    emit_executable,
    jit_run,
    optimize_ir,
)


def build_ir_from_source(src: str, opt_level: int) -> str:
    # 源码 -> AST -> IR -> (可选)优化
    prog = Parser(Lexer(src)).parse_program()
    ir = Codegen().codegen(prog)
    if opt_level and opt_level > 0:
        ir = optimize_ir(ir, level=opt_level)
    return ir


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="minicc", description="mini-C compiler (Python + llvmlite)"
    )
    ap.add_argument("file", help="source file (.mc). Use '-' to read from stdin")
    ap.add_argument(
        "-O",
        "--opt",
        type=int,
        default=0,
        choices=(0, 1, 2, 3),
        help="opt level (default: 0)",
    )
    ap.add_argument("-o", "--output", default="a.out", help="output (exe or .s)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--emit-llvm", action="store_true", help="print LLVM IR and exit")
    g.add_argument(
        "-S", "--emit-asm", action="store_true", help="emit assembly (.s) and exit"
    )
    g.add_argument(
        "--run", action="store_true", help="JIT run main() and print exit code"
    )
    args = ap.parse_args(argv)

    # 读源码
    if args.file == "-":
        src = sys.stdin.read()
    else:
        src = pathlib.Path(args.file).read_text(encoding="utf-8")

    try:
        llvm_ir = build_ir_from_source(src, opt_level=args.opt)
    except ParseError as e:
        print(f"[parse error] {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1

    # 三种模式：IR / ASM / JIT；否则默认生成可执行文件
    if args.emit_llvm:
        print(llvm_ir)
        return 0

    if args.emit_asm:
        out = pathlib.Path(args.output)
        if out.suffix != ".s":
            out = out.with_suffix(".s")
        emit_assembly(llvm_ir, str(out))
        print(f"[ok] wrote {out}")
        return 0

    if args.run:
        code = jit_run(llvm_ir, "main")
        print(code)  # 打印 main 的返回值
        return code

    # 默认：AOT 生成可执行文件
    emit_executable(llvm_ir, args.output, opt_level=args.opt)
    print(f"[ok] linked {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
