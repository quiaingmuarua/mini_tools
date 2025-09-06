# Mini JSVMP - JavaScript Virtual Machine with VMP Protection

一个功能完整的JavaScript虚拟机实现，支持编译、字节码执行和VMP保护机制。

## 🚀 主要特性

### 核心功能

- **完整的编程语言支持**：变量、函数、闭包、控制流
- **多级作用域**：词法作用域和闭包环境
- **函数调用栈**：支持递归和参数传递
- **字节码编译**：源码 → 字节码 → 执行
- **HEX序列化**：字节码可序列化为HEX字符串

### 语言特性

```javascript
// 变量声明
let x = 42;

// 函数定义
function add(a, b) {
  return a + b;
}

// 控制流
if (x > 10) {
  print("大于10");
} else {
  print("小于等于10");
}

// 字符串操作
let msg = "Hello " + "World";
```

### VMP保护机制 🛡️

- **指令表乱序（Opcode Permutation）**：每次打包生成随机映射表
- **流式解码（Stream Decoding）**：运行时实时反映射物理→逻辑操作码
- **立即数按位点加密（Rolling-by-Offset）**：只加密操作数，基于位置的PRNG
- **完整性校验（Integrity Check）**：MAC验证防止代码篡改
- **格式识别**：魔数标识和版本控制

## 📖 API 文档

### 基础编译运行

```javascript
// 编译源码
const {code, consts, functions} = compile(sourceCode);

// 直接运行
compileAndRun(sourceCode);

// 序列化为HEX
const hexString = packToHex(code, consts, functions);

// 从HEX运行
runHex(hexString, builtins);
```

### VMP保护模式

```javascript
// VMP保护打包
const protectedHex = packToHexHardened(code, consts, functions);

// VMP保护运行
runHexHardened(protectedHex, builtins);
```

## 🔧 指令集

| 操作码                 | 功能    | 参数          |
|---------------------|-------|-------------|
| `PUSH_CONST`        | 推入常量  | [idx]       |
| `LOAD_VAR`          | 加载变量  | [nameIdx]   |
| `STORE_VAR`         | 存储变量  | [nameIdx]   |
| `ADD/SUB/MUL/DIV`   | 算术运算  | -           |
| `EQ/NE/LT/GT/LE/GE` | 比较运算  | -           |
| `JUMP`              | 无条件跳转 | [addr]      |
| `JUMP_IF_FALSE`     | 条件跳转  | [addr]      |
| `CALL`              | 函数调用  | [argc]      |
| `RET`               | 函数返回  | -           |
| `MAKE_CLOS`         | 创建闭包  | [funcIndex] |
| `PRINT`             | 打印输出  | -           |
| `HALT`              | 程序结束  | -           |

## 🛡️ VMP保护原理

### 1. 指令表乱序

```
逻辑操作码：[0x01, 0x10, 0x20, ...]
     ↓ 随机映射
物理操作码：[0x0C, 0x03, 0x15, ...]
```

### 2. 流式解码

```javascript
while (true) {
  const physOp = code[ip++];        // 读取物理操作码
  const logicalOp = invMap.get(physOp); // 反映射为逻辑操作码
  executeInstruction(logicalOp);    // 执行逻辑指令
}
```

### 3. 立即数按位点加密

```javascript
// 加密（打包时）
function encodeImmediates(code, seed) {
  for (每个立即数字节 at position) {
    code[position] ^= maskAt(seed, position);
  }
}

// 解密（运行时）
const readImm1 = () => {
  const encrypted = code[ip];
  const decrypted = encrypted ^ maskAt(seed, ip);
  ip++;
  return decrypted;
};
```

### 4. 完整性校验

```
数据 = 常量池 + 函数表 + 映射表 + 种子 + 代码
MAC = simpleMAC(数据)
验证 = 运行时重新计算MAC并比较
```

## 📦 HEX格式规范

### 普通格式 (v1)

```
[常量数量:4B][常量数据...][函数数量:4B][函数数据...][代码长度:4B][代码...]
```

### VMP保护格式 (v3)

```
[魔数:VM][版本:03][常量池...][函数表...][映射表长度:1B][映射表...][种子:4B][代码长度:4B][代码...][MAC:4B]
```

## 🔍 安全特性

- **反调试**：指令表乱序使静态分析困难
- **防篡改**：MAC校验确保代码完整性
- **反逆向**：物理操作码与逻辑操作码解耦
- **立即数保护**：操作数按位点加密，防止参数分析
- **运行时保护**：每次执行使用不同的映射表和种子
- **执行路径无关**：基于绝对位置的解密，避免路径依赖

## 🚧 已知限制

- `while` 循环解析存在问题，需要进一步修复
- 错误信息可以更详细
- 可添加更多内置函数支持

## 📝 示例代码

参见 `example.js` 获取完整的使用示例。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
