import os

from minic.codegen import *
from minic.codegen import Block
from minic.runtime import emit_assembly, emit_executable, jit_run, optimize_ir, run_executable


def if_statement_expr():
    # 等价于：
    # int main() {
    #   int x = 2;
    #   int y = 0;
    #   if (x == 0) { y = 1; } else { y = 2; }
    #   return y;
    # }
    return Block(
        [
            VarDecl("x", IntLit(2)),
            VarDecl("y", IntLit(0)),
            IfElse(
                Compare("==", Var("x"), IntLit(0)),
                then_blk=Block([Assign("y", IntLit(1))]),
                else_blk=Block([Assign("y", IntLit(2))]),
            ),
            Return(Var("y")),
        ]
    )


def while_statement_expr():
    """
        int main() {
      int x = 3;
      while (x > 0) {
        x = x - 1;
      }
      return x;
    }
    """
    return Block(
        [
            VarDecl("x", IntLit(3)),
            While(
                Compare(">", Var("x"), IntLit(0)),
                Block([Assign("x", BinaryOp("-", Var("x"), IntLit(1)))]),
            ),
            Return(Var("x")),
        ]
    )


def function_statement_expr():
    return Program(
        [
            Function("add", ["a", "b"], Block([Return(BinaryOp("+", Var("a"), Var("b")))])),
            Function(
                "main",
                [],
                Block(
                    [
                        VarDecl("x", IntLit(2)),
                        VarDecl("y", IntLit(3)),
                        VarDecl("z", Call("add", [Var("x"), Var("y")])),
                        PrintI32(Var("z")),  # ← 打印 z
                        Return(Var("z")),
                    ]
                ),
            ),
        ]
    )


def block_demo():
    ll = generate_block_ir(while_statement_expr())

    print("=== LLVM IR ===\n", ll)
    ll = optimize_ir(ll)
    print("=== LLVM IR (O2) ===\n", ll)
    print("exit code:", jit_run(ll))


def function_demo():
    llvm_ir = generate_ir(function_statement_expr())
    print("=== LLVM IR ===\n", llvm_ir)
    # llvm_ir = optimize_o2(ll)
    print("=== LLVM IR (O2) ===\n", llvm_ir)
    # print("exit code:", run_llvm(llvm_ir))

    with open("out/mini_c_add.ll", "w") as f:
        f.write(llvm_ir)

    exe = os.path.abspath("out/mini_c_add")
    emit_executable(llvm_ir, exe)  # 生成可执行文件
    code = run_executable(exe)  # 运行可执行文件
    print("program exit code:", code)  # 期望 5

    emit_assembly(llvm_ir, "out/mini_c_add.s")


if __name__ == "__main__":
    # block_demo()
    function_demo()
