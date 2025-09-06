# Mini Tool

A collection of mini cryptographic tools focusing on TLS and encryption algorithms.

[![CI](https://github.com/your-username/mini-tool/workflows/CI/badge.svg)](https://github.com/your-username/mini-tool/actions)
[![codecov](https://codecov.io/gh/your-username/mini-tool/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/mini-tool)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Purpose

This project is a collection of educational and practical mini-tools for cryptographic operations, particularly focused on:

- **TLS/SSL protocols** - Implementation and understanding
- **Elliptic Curve Cryptography** - ECDHE key exchange
- **Encryption algorithms** - Various symmetric and asymmetric algorithms
- **Protocol analysis** - Tools for analyzing cryptographic protocols

## 🚀 Features

### Currently Implemented

- **ECDHE (Elliptic Curve Diffie-Hellman Ephemeral)**
  - Complete implementation of ECDHE key exchange
  - Based on NIST P-256 curve (secp256r1)
  - SEC1 standard public key encoding/decoding
  - HKDF key derivation function
  - Montgomery ladder scalar multiplication (side-channel resistant)

### Planned Features

- **TLS Handshake** - Mini TLS implementation
- **Additional Curves** - Support for more elliptic curves
- **Symmetric Ciphers** - AES, ChaCha20, etc.
- **Hash Functions** - SHA family, BLAKE, etc.
- **Digital Signatures** - ECDSA, EdDSA

## 📦 Installation

### Development Installation

```bash
# Clone the repository
git clone https://github.com/your-username/mini-tool.git
cd mini-tool

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### Basic Installation

```bash
pip install -e .
```

## 🧪 Usage

### ECDHE Example

```python
from core.mini_ecdhe import gen_keypair, ecdhe_shared, hkdf_sha256

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

### Public Key Encoding

```python
from core.mini_ecdhe import gen_keypair, encode_point, decode_point

# Generate a key pair
sk, pk = gen_keypair()

# Encode public key in compressed format (33 bytes)
compressed = encode_point(pk, compressed=True)

# Encode public key in uncompressed format (65 bytes)
uncompressed = encode_point(pk, compressed=False)

# Decode back to point
decoded_pk = decode_point(compressed)
assert decoded_pk == pk
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=core --cov-report=html

# Run only unit tests
pytest -m unit

# Run specific test file
pytest test/test_mini_ecdhe.py
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
mypy core example
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

## 🏗️ Project Structure

```
mini_tool/
├── core/                    # Core implementations
│   ├── __init__.py
│   ├── mini_ecdhe.py       # ECDHE implementation
│   └── mini_tls.py         # TLS implementation (WIP)
├── example/                 # Usage examples
│   └── __init__.py
├── test/                    # Test suite
│   ├── __init__.py
│   └── test_mini_ecdhe.py  # ECDHE tests
├── .github/workflows/       # CI/CD configuration
│   └── ci.yml
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## 🧪 Testing Philosophy

This project follows rigorous testing practices:

- **Unit Tests** - Test individual functions and components
- **Integration Tests** - Test component interactions
- **Property-based Tests** - Test mathematical properties
- **Fixed Test Cases** - Known-good test vectors
- **Comprehensive Coverage** - Aim for >90% code coverage

All cryptographic implementations are thoroughly tested against:
- Known test vectors
- Mathematical properties
- Edge cases and error conditions
- Interoperability with standard implementations

## 🚦 Continuous Integration

The project uses GitHub Actions for CI/CD:

- **Multiple Python versions** (3.8-3.12)
- **Code quality checks** (black, isort, flake8, mypy)
- **Security scanning** (bandit, safety)
- **Test coverage reporting** (codecov)
- **Automated testing** on every push and PR

## ⚠️ Security Notice

**Educational Purpose**: These implementations are primarily for educational and research purposes. While they follow cryptographic best practices, they have not undergone the same level of security audit as production cryptographic libraries.

**Use in Production**: For production use, prefer well-established and audited cryptographic libraries like:
- `cryptography` (Python)
- `pycryptodome` (Python)
- OpenSSL-based implementations

## 📚 Educational Resources

- [Elliptic Curve Cryptography: A Gentle Introduction](https://andrea.corbellini.name/2015/05/17/elliptic-curve-cryptography-a-gentle-introduction/)
- [RFC 5869 - HKDF](https://tools.ietf.org/html/rfc5869)
- [SEC 1: Elliptic Curve Cryptography](https://www.secg.org/sec1-v2.pdf)
- [NIST SP 800-186 - Elliptic Curve Cryptography](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-186.pdf)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- NIST for the P-256 curve specification
- The cryptographic research community
- All contributors and users of this project
