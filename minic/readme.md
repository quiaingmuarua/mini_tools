下面是一份可直接放到仓库根目录的 **README.md**（你可以按需删改）。我把“已完成”和“下一步 TODO”列得很清楚，便于继续迭代。

````markdown
# mini-c (Python + llvmlite)

一个教学取向的“mini C”编译器：**前端自研（Lexer/Parser/AST）**，**后端用 LLVM（llvmlite）生成 IR**，既可 **JIT 运行**，也可 **输出可执行文件**。目标是把编译器主干完整串一遍：词法 → 语法 → 语义（轻量） → IR → 优化/生成。

> 适合作为“从脚本 VM 思维过渡到 LLVM/IR 思维”的练习项目。

---

## 功能概览（Status）

### ✅ 语言特性（子集）
- 基本类型：`int`
- 表达式：`+ - * /`，比较 `== != < <= > >=`
- 一元运算：**`-x`（一元负号）**
- 语句：变量定义 `int x = ...;`、赋值 `x = ...;`、`return`
- 控制流：`if (...) { ... } else { ... }`、`while (...) { ... }`
- 函数：`int f(int a, int b) { ... }`；**调用**与**返回值**
- 简易 I/O：`PrintI32(expr)` → 经由 `printf("%d\n")` 打印整型

### ✅ 编译链路
- **Lexer**：关键字、标识符、十进制整型字面量、运算符/分隔符、`//` 与 `/* */` 注释、行列号
- **Parser（递归下降）**：表达式优先级分层（或然等价 Pratt），函数/语句/块
- **AST → LLVM IR**：
  - 模块 triple & datalayout（取自本机）
  - 函数原型声明 → 函数体定义
  - **入口块 `entry` 专用 `alloca` + `br body`**（便于后续 `mem2reg`）
  - 变量：`alloca/load/store`（简单直观，后续交由优化器提升）
  - 分支/循环：`icmp` + `cbranch` + 基本块组织
  - 调用：`call`（参数与返回值均 `i32`）
- **执行方式**：
  - **JIT（MCJIT）**：`engine.get_function_address("main")` → `ctypes` 调用
  - **AOT**：IR → **.o（emit_object）** → **clang 链接为可执行文件**
- **优化实验**：
  - `-O2` 或 `mem2reg`：观察局部变量/形参被提升为寄存器、分支合流自动插入 `phi`
  - 汇编导出（可选）：`emit_assembly` 便于对照 ABI/栈帧

---

## 快速开始

### 依赖
- Python 3.9+
- `llvmlite`
- 系统编译器（建议 `clang`；macOS 需 `xcode-select --install`）

```bash
pip install llvmlite
````

### 运行示例

* **JIT 运行**：`python your_main.py`（示例程序会返回/打印预期结果）
* **生成可执行文件**：

  ```python
  exe = emit_executable(llvm_ir, "mini_c_prog")  # 生成本机可执行文件
  code = run_executable(exe)                      # 以进程退出码返回 main 的返回值
  ```
* **观察优化**：

  ```python
  print(optimize_o2(llvm_ir))  # 在 Python 内部跑类似 -O2 的 pass
  # 或将 IR 存盘后：opt -S -mem2reg in.ll -o out.ll
  ```

---

## 目录建议（示例）

```
core/
  lang/
    lexer.py         # Token/Kind/Lexer
    parser.py        # Parser + AST（或 AST 单独 ast.py）
    codegen.py       # AST -> LLVM IR（llvmlite.ir）
    runtime.py       # 与 printf 等外部函数交互的封装
    driver.py        # JIT/AOT/opt 入口（emit_executable / run_llvm / optimize_o2）
examples/
  add.mc
  control.mc
README.md
```

> 当前实现把这些组合在一个/几个脚本中也 OK；后续可按上面的模块拆分。

---

## 设计要点（为什么这样做）

* **alloca 都放入口块**：简单的“变量即内存槽”模型，交给 `mem2reg` 提升为 SSA，省去手写 `phi` 的复杂度。
* **entry/body 双基本块**：保证 `ret` 之后不会插入新指令（避免非法 IR），同时固定 `alloca` 的插入点。
* **前端不做重优化**：只保证**结构正确且清晰**，把常见优化（常量折叠、CSE、DCE、寄存器提升）交给 LLVM。
* **目标中立**：IR 抽象与 ABI/寄存器分配解耦；需要时可用 `emit_assembly` 对照底层机器码。

---

## 示例（等价 C）

```c
int add(int a, int b) { return a + b; }
int main() {
  int x = 2, y = 3, z = add(x, y);
  if (z == 5) { z = z + 1; } else { z = 0; }
  while (z > 0) { z = z - 1; }
  // PrintI32(z); // 如需输出
  return z;
}
```

* **O0 IR**：含 `alloca/load/store`、分支/循环基本块清晰可读
* **O2 IR**：局部/形参被提升，可能标注 `tail call`，CFG 简化

---

## 已知限制 / 暂未支持

* 只有 `int`，无 `bool/float/char/字符串字面量/数组/指针/struct`
* 仅支持 `-x` 一元运算（**`!x`、`&&/||` 短路未实现**）
* 无作用域嵌套与遮蔽（当前按函数级处理）
* 无错误恢复（遇错即抛，后续可加“尖头 ^ 定位”）
* 无类型系统/语义检查（未定义变量/重复定义等仅靠运行时 KeyError）

---

## 路线图 / TODO（按优先级）

### 1. 语言&前端

* [ ] 一元 **`!x`**（i1 结果）；二元 **`&& / ||`** 短路（基本块 + `phi`）
* [ ] `for` 语句（或语法糖成 while）
* [ ] **块级作用域**与遮蔽：`{ int x; { int x; } }`
* [ ] 简单**语义检查**：未定义/重复定义、return 路径完整性
* [ ] 错误信息增强：**行列号 + 源码切片 + ^ 指示**
* [ ] 一元 `+`、括号嵌套、逗号表达式（可选）

### 2. 类型系统（最小化）

* [ ] `bool` 与 `int` 的区分与**显式转换**
* [ ] 字符串字面量 & `PrintStr`（内部全局常量池）
* [ ] 未来：`float`（Care：`sitofp/fptosi` 转换）

### 3. IR/优化/后端

* [ ] **手工插 `phi`**（体验 SSA 构造），对比 `mem2reg`
* [ ] 小型**前端优化**实验：常量折叠、DCE（对照 LLVM pass）
* [ ] 函数属性：`noinline` / `alwaysinline`，观察 O2 行为差异
* [ ] 导出/分析汇编：对照 **AArch64 调用约定**、栈帧大小、尾调用
* [ ] 额外目标：x86-64（仅需换 triple/data layout）

### 4. 语言扩展（中期）

* [ ] 数组 & 指针基础（`getelementptr`）、`&`/`*` 运算
* [ ] 简易字符串库：`puts`、`strlen`
* [ ] 运行时：输入（`scanf` 或自制读整函数）

### 5. 工程化

* [ ] 简易 CLI：`minicc <file.mc> [-S|--emit-llvm|--emit-obj|-o a.out] [-O0|O1|O2]`
* [ ] **测试夹具**：golden IR/ASM 测试 + 运行期退出码断言
* [ ] CI：在 macOS/Ubuntu 上跑 JIT/AOT 栈
* [ ] 文档：BNF 语法说明、贡献指南

---

## 开发者指南

* **看 IR 是否合法**：`binding.parse_assembly(llvm_ir).verify()`
* **定位非法 IR**：注意不要在 `ret` 之后插指令；`alloca` 固定放 entry 的 `br body` 之前
* **观测优化点**：先写“朴素 IR”，用 `opt -S -mem2reg` 看自动插入的 `phi` 再理解控制流

---

## 许可证

TODO（例如 MIT）

```

如果你想，我也可以把这份 README 按你的文件名/模块名做一次“对号入座”的微调；或者我们先挑 TODO 里的“`!` 与 `&&/||` 短路”做一个小迭代，把差异 IR 展开给你看。
```
