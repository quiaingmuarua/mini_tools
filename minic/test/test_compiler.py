#!/usr/bin/env python3
"""
Test suite for MiniC compiler
"""

import os
import tempfile
import pytest
from minic.driver import build_ir_from_source
from minic.runtime import emit_assembly, emit_executable, run_executable


def test_simple_function():
    """Test compiling a simple function"""
    src = """
    int add(int a, int b) { 
        return a + b; 
    }
    
    int main() {
        return add(2, 3);
    }
    """
    
    # Should not raise an exception
    llvm_ir = build_ir_from_source(src, 0)
    assert llvm_ir is not None
    assert 'define i32 @"add"' in llvm_ir
    assert 'define i32 @"main"' in llvm_ir


def test_control_flow():
    """Test if/else control flow"""
    src = """
    int main() {
        int x = 5;
        if (x > 3) {
            return 1;
        } else {
            return 0;
        }
    }
    """
    
    llvm_ir = build_ir_from_source(src, 0)
    assert llvm_ir is not None
    assert "br i1" in llvm_ir  # Conditional branch


def test_while_loop():
    """Test while loop compilation"""
    src = """
    int main() {
        int x = 3;
        while (x > 0) {
            x = x - 1;
        }
        return x;
    }
    """
    
    llvm_ir = build_ir_from_source(src, 0)
    assert llvm_ir is not None
    assert "loop.cond" in llvm_ir
    assert "loop.body" in llvm_ir


def test_arithmetic_operations():
    """Test basic arithmetic operations"""
    src = """
    int main() {
        int a = 10;
        int b = 5;
        int sum = a + b;
        int diff = a - b;
        int prod = a * b;
        int quot = a / b;
        return sum + diff + prod + quot;
    }
    """
    
    llvm_ir = build_ir_from_source(src, 0)
    assert llvm_ir is not None
    assert "add i32" in llvm_ir
    assert "sub i32" in llvm_ir
    assert "mul i32" in llvm_ir
    assert "sdiv i32" in llvm_ir


def test_comparison_operations():
    """Test comparison operations"""
    src = """
    int main() {
        int x = 5;
        int y = 3;
        if (x == y) return 1;
        if (x != y) return 2;
        if (x > y) return 3;
        if (x < y) return 4;
        if (x >= y) return 5;
        if (x <= y) return 6;
        return 0;
    }
    """
    
    llvm_ir = build_ir_from_source(src, 0)
    assert llvm_ir is not None
    assert "icmp eq" in llvm_ir
    assert "icmp ne" in llvm_ir
    assert "icmp sgt" in llvm_ir


def test_nested_calls():
    """Test nested function calls"""
    src = """
    int multiply(int a, int b) {
        return a * b;
    }
    
    int square(int x) {
        return multiply(x, x);
    }
    
    int main() {
        return square(4);
    }
    """
    
    llvm_ir = build_ir_from_source(src, 0)
    assert llvm_ir is not None
    assert 'call i32 @"multiply"' in llvm_ir
    assert 'call i32 @"square"' in llvm_ir


@pytest.mark.slow
def test_executable_generation():
    """Test generating and running an executable (slow test)"""
    import platform
    
    # Skip this test on Windows or if clang is not available
    if platform.system() == "Windows":
        pytest.skip("Executable generation not supported on Windows in CI")
    
    src = """
    int main() {
        return 42;
    }
    """
    
    llvm_ir = build_ir_from_source(src, 0)
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        try:
            exe_path = emit_executable(llvm_ir, tmp.name)
            # Just check that the file was created
            assert os.path.exists(exe_path)
        except FileNotFoundError:
            # clang not available, skip test
            pytest.skip("clang not available for executable generation")
        finally:
            # Clean up
            try:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)
            except (PermissionError, FileNotFoundError):
                pass  # Ignore cleanup errors


def test_optimization_levels():
    """Test different optimization levels"""
    src = """
    int main() {
        int x = 1 + 2;
        return x;
    }
    """
    
    # Test O0 (no optimization)
    llvm_ir_o0 = build_ir_from_source(src, 0)
    assert llvm_ir_o0 is not None
    
    # Test O2 (optimization)
    llvm_ir_o2 = build_ir_from_source(src, 2)
    assert llvm_ir_o2 is not None
    
    # O2 should generally be shorter due to optimizations
    # (though this is not guaranteed for all cases)


def test_variable_declarations():
    """Test variable declarations and assignments"""
    src = """
    int main() {
        int a;
        int b = 5;
        a = 10;
        return a + b;
    }
    """
    
    llvm_ir = build_ir_from_source(src, 0)
    assert llvm_ir is not None
    assert "alloca i32" in llvm_ir  # Variable allocations
    assert "store i32" in llvm_ir   # Variable stores
    assert "load i32" in llvm_ir    # Variable loads


def test_unary_minus():
    """Test unary minus operator"""
    src = """
    int main() {
        return -5;
    }
    """
    
    llvm_ir = build_ir_from_source(src, 0)
    assert llvm_ir is not None
    assert "sub i32 0" in llvm_ir  # Unary minus implemented as 0 - x
