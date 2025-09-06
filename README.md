# Mini Tools Collection

A comprehensive collection of educational programming tools and language implementations, covering compilers, virtual
machines, cryptography, and systems programming.

[![CI](https://github.com/your-username/mini-tools/workflows/CI/badge.svg)](https://github.com/your-username/mini-tools/actions)
[![codecov](https://codecov.io/gh/your-username/mini-tools/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/mini-tools)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Purpose

This project is a comprehensive collection of educational and practical mini-tools for understanding fundamental
computer science concepts:

- **Compiler Construction** - C compiler with LLVM backend
- **Virtual Machines** - JVM implementation and JavaScript VM with VMP protection
- **Cryptography & Security** - TLS protocols, ECDHE, encryption algorithms
- **Systems Programming** - ELF parsing, linking, and binary analysis

## 🚀 Tools Overview

### 🔧 MiniC - C Compiler with LLVM Backend

- **Complete C subset compiler** with lexer, parser, and LLVM IR generation
- **JIT execution** using MCJIT engine
- **AOT compilation** to native executables
- **Optimization support** with LLVM passes (O0, O2)
- **Features**: variables, functions, control flow (if/while), expressions

### ☕ Mini JVM - Java Virtual Machine

- **Bytecode virtual machine** with stack-based execution
- **Object-oriented features** with classes, methods, inheritance
- **Static method support** and virtual method dispatch
- **Frame-based execution** with local variables and operand stack

### 🟨 Mini JSVMP - JavaScript VM with VMP Protection

- **Complete JavaScript interpreter** with bytecode compilation
- **Advanced VMP protection**:
    - Opcode permutation and stream decoding
    - Immediate encryption with position-based PRNG
    - Integrity checks and anti-tampering
- **Language features**: variables, functions, closures, control flow

### 🔐 MiniTLS - Cryptographic Tools

- **ECDHE key exchange** implementation (NIST P-256)
- **SEC1 point encoding/decoding** (compressed/uncompressed)
- **HKDF key derivation** function
- **Cryptographic primitives**: AES, MD5, SHA256
- **Montgomery ladder** scalar multiplication (side-channel resistant)

### 🔗 Mini Linker - Binary Analysis Tools

- **ELF parser** supporting ELF32/ELF64, little/big endian
- **Binary analysis** with header, section, and symbol parsing
- **Cross-platform support** for various architectures

## 📦 Installation

### Prerequisites

```bash
# For MiniC (LLVM backend)
pip install llvmlite

# For all tools (development)
pip install -e ".[dev]"
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/your-username/mini-tools.git
cd mini-tools

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

## 🧪 Usage Examples

### 🔧 MiniC - C Compiler

```python
from minic.driver import build_ir_from_source
from minic.runtime import emit_executable, run_executable

# C source code
c_code = '''
int add(int a, int b) { return a + b; }

int main() {
    int x = 2;
    int y = 3;
    int z = add(x, y);
    return z;
}
'''

# Compile to LLVM IR
llvm_ir = build_ir_from_source(c_code, optimization_level=0)

# Generate executable
exe_path = emit_executable(llvm_ir, "my_program")
exit_code = run_executable(exe_path)
print(f"Program returned: {exit_code}")  # Should print 5
```

### ☕ Mini JVM

```python
from mini_jvm.runtime import VM, ClassDef, Method, ObjRef

# Create a simple class with methods
class_def = ClassDef(
    name="Calculator",
    super=None,
    methods={"add": add_method},
    static_methods={"main": main_method}
)

# Run the virtual machine
vm = VM()
vm.load_class(class_def)
result = vm.call_static("Calculator", "main", [])
```

### 🟨 Mini JSVMP - JavaScript VM

```javascript
// Regular execution
const code = `
function factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
print(factorial(5));
`;

// Compile and run
compileAndRun(code);

// VMP protected execution
const protectedHex = packToHexHardened(bytecode, constants, functions);
runHexHardened(protectedHex, builtins);
```

### 🔐 MiniTLS - Cryptographic Tools

```python
from minit_tls.network.mini_ecdhe import gen_keypair, ecdhe_shared, hkdf_sha256

# Generate key pairs for Alice and Bob
alice_sk, alice_pk = gen_keypair()
bob_sk, bob_pk = gen_keypair()

# Perform ECDHE key exchange
alice_shared = ecdhe_shared(alice_sk, bob_pk)
bob_shared = ecdhe_shared(bob_sk, alice_pk)

# Both parties now have the same shared secret
assert alice_shared == bob_shared

# Derive session keys using HKDF
session_key = hkdf_sha256(alice_shared, salt=b"", info=b"demo", length=32)
print(f"Session key: {session_key.hex()}")
```

### 🔗 Mini Linker - ELF Analysis

```bash
# Analyze ELF files
python mini_linker/mini_read_elf.py -h binary_file    # ELF header
python mini_linker/mini_read_elf.py -l binary_file    # Program headers  
python mini_linker/mini_read_elf.py -S binary_file    # Section headers
python mini_linker/mini_read_elf.py -s binary_file    # Symbol table
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run tests for specific components
pytest minic/test/           # C compiler tests
pytest minit_tls/test/       # Cryptography tests

# Run tests with coverage
pytest --cov=minic --cov=minit_tls --cov=mini_jvm --cov=mini_linker --cov-report=html

# Run specific test files
pytest minit_tls/test/test_mini_ecdhe.py
pytest minic/test/minic_test.py
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy minic minit_tls mini_jvm mini_linker
```

### Tool-Specific Development

#### MiniC Development

```bash
# Run C compiler tests
python minic/test/minic_test.py

# Test with different optimization levels
python minic/test/example.py
```

#### Mini JSVMP Development

```bash
# Run JavaScript VM tests
node mini_jsvmp/test_examples.js
```

#### Cryptography Development

```bash
# Run comprehensive ECDHE tests
python minit_tls/test/test_mini_ecdhe.py
```

## 🏗️ Project Structure

```
mini_tools/
├── minic/                   # C Compiler with LLVM
│   ├── lexer.py            # Tokenization
│   ├── parser.py           # AST parsing  
│   ├── codegen.py          # LLVM IR generation
│   ├── runtime.py          # JIT & AOT execution
│   ├── driver.py           # Compilation driver
│   ├── examples/           # C source examples
│   └── test/               # Compiler tests
├── mini_jvm/               # Java Virtual Machine
│   └── runtime.py          # JVM implementation
├── mini_jsvmp/             # JavaScript VM with VMP
│   ├── mini_jsvmp.js       # Main VM implementation
│   ├── example.js          # Usage examples
│   └── test_examples.js    # Test cases
├── minit_tls/              # Cryptographic Tools
│   ├── network/            # TLS protocols
│   │   ├── mini_ecdhe.py   # ECDHE implementation  
│   │   └── mini_tls.py     # TLS protocol
│   ├── cryptor/            # Crypto primitives
│   │   ├── aes_encrypt_craft.py
│   │   ├── md5_craft.py
│   │   └── sha256_craft.py
│   ├── example/            # Usage examples
│   └── test/               # Cryptography tests
├── mini_linker/            # Binary Analysis Tools
│   └── mini_read_elf.py    # ELF parser
├── .github/workflows/      # CI/CD configuration
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## 🧪 Testing Philosophy

This project follows comprehensive testing practices across all components:

### Testing Approaches

- **Unit Tests** - Individual function and component testing
- **Integration Tests** - Cross-component interaction testing
- **Compiler Tests** - End-to-end compilation and execution testing
- **VM Tests** - Bytecode execution and runtime behavior testing
- **Cryptographic Tests** - Mathematical property and vector validation
- **Binary Analysis Tests** - ELF parsing and format validation

### Tool-Specific Testing

- **MiniC**: IR generation, optimization, and executable output validation
- **Mini JVM**: Bytecode execution, method dispatch, and object lifecycle
- **Mini JSVMP**: VMP protection, bytecode integrity, and language features
- **MiniTLS**: Cryptographic correctness, known test vectors, interoperability
- **Mini Linker**: ELF format compliance, cross-architecture support

## 🚦 Continuous Integration

Multi-component CI/CD pipeline with GitHub Actions:

### Testing Matrix

- **Python versions**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Operating systems**: Ubuntu, macOS, Windows
- **LLVM dependencies**: llvmlite compatibility testing
- **Node.js testing**: JavaScript VM validation

### Quality Assurance

- **Code formatting**: black, isort
- **Linting**: flake8, mypy type checking
- **Security scanning**: bandit, safety
- **Coverage reporting**: pytest-cov, codecov integration
- **Dependency management**: pip-audit for vulnerability scanning

## ⚠️ Security Notice

**Educational Purpose**: These implementations are primarily for educational and research purposes. While they follow
established best practices, they have not undergone formal security audits.

**Production Use Guidance**:

- **Cryptography**: Use established libraries (`cryptography`, `pycryptodome`, OpenSSL)
- **Compilers**: For production, use mature toolchains (GCC, Clang, OpenJDK)
- **VMs**: Consider proven implementations (V8, SpiderMonkey, OpenJDK HotSpot)

## 📚 Educational Resources

### Compiler Construction

- [Crafting Interpreters](https://craftinginterpreters.com/) - Language implementation guide
- [LLVM Language Reference](https://llvm.org/docs/LangRef.html) - LLVM IR documentation
- [Dragon Book](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools) - Classic compiler design

### Virtual Machines

- [JVM Specification](https://docs.oracle.com/javase/specs/jvms/se17/html/) - Official JVM documentation
- [Virtual Machine Design](https://www.amazon.com/Virtual-Machine-Design-Implementation-Book/dp/1558609105) - VM
  implementation guide

### Cryptography

- [Elliptic Curve Cryptography: A Gentle Introduction](https://andrea.corbellini.name/2015/05/17/elliptic-curve-cryptography-a-gentle-introduction/)
- [RFC 5869 - HKDF](https://tools.ietf.org/html/rfc5869) - Key derivation standard
- [SEC 1: Elliptic Curve Cryptography](https://www.secg.org/sec1-v2.pdf) - ECC standards

### Binary Analysis

- [ELF Format Specification](https://refspecs.linuxfoundation.org/elf/elf.pdf) - Official ELF documentation
- [Linkers and Loaders](https://www.amazon.com/Linkers-Loaders-John-Levine/dp/1558604960) - Linking concepts

## 🤝 Contributing

We welcome contributions to all components! Please:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Add tests** for new functionality
4. **Ensure** all tests pass (`pytest`)
5. **Format** code (`black .`, `isort .`)
6. **Submit** a pull request

### Component-Specific Guidelines

- **MiniC**: Add test cases for new language features
- **Mini JVM**: Include bytecode test cases
- **Mini JSVMP**: Test both regular and VMP-protected execution
- **MiniTLS**: Provide cryptographic test vectors
- **Mini Linker**: Test with various ELF files

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LLVM Project** - Infrastructure for modern compiler design
- **NIST** - Cryptographic standards and specifications
- **ELF Specification** - Binary format documentation
- **Open Source Community** - Inspiration and foundational knowledge
- **Contributors** - All users and contributors to this project
