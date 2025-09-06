import os

from minic.driver import build_ir_from_source
from minic.runtime import emit_assembly, emit_executable, run_executable

demo_src = """

int add(int a, int b) { return a + b; }

int loop() {
      int x = -3;
      if (-x == 3) { x = x + 10; } else { x = 0; }
      return x;
    }

int main() {
  int x = 2;
  int y = loop();
  int z = add(x, y);

  return z;      
}


"""

if __name__ == "__main__":
    llvm_ir = build_ir_from_source(demo_src, 0)
    print(llvm_ir)
    with open("out/mini_c_add.ll", "w") as f:
        f.write(llvm_ir)

    exe = os.path.abspath("out/mini_c_add")
    emit_executable(llvm_ir, exe)  # 生成可执行文件
    code = run_executable(exe)  # 运行可执行文件
    print("program exit code:", code)  # 期望 5

    emit_assembly(llvm_ir, "out/mini_c_add.s")
