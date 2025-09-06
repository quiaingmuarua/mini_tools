#!/usr/bin/env python3
"""
Test suite for Mini JVM runtime
"""

import pytest

from mini_jvm.runtime import (
    CALL_STATIC,
    CALL_VIRT,
    IADD,
    LOAD_LOCAL,
    PUSH_CONST,
    RETURN,
    STORE_LOCAL,
    VM,
    ClassDef,
    Method,
    ObjRef,
)


def test_vm_creation():
    """Test VM instantiation"""
    vm = VM()
    assert vm is not None
    assert len(vm.stack_frames) == 0


def test_simple_method_execution():
    """Test executing a simple method that returns a constant"""
    # Method that just returns 42
    simple_method = Method("test", [(PUSH_CONST, 42), (RETURN, None)], max_locals=0)

    vm = VM()
    vm.push_frame(simple_method, [])
    result = vm.run_until_return()

    assert result == 42


def test_local_variable_operations():
    """Test local variable load/store operations"""
    # Method that loads local 0, adds 10, and returns
    method = Method(
        "test",
        [
            (LOAD_LOCAL, 0),  # Load argument
            (PUSH_CONST, 10),  # Push constant 10
            (IADD, None),  # Add them
            (RETURN, None),  # Return result
        ],
        max_locals=1,
    )

    vm = VM()
    vm.push_frame(method, [5])  # Pass 5 as argument
    result = vm.run_until_return()

    assert result == 15  # 5 + 10


def test_class_method_resolution():
    """Test class method resolution"""
    # Simple method that returns 100
    test_method = Method("getValue", [(PUSH_CONST, 100), (RETURN, None)], max_locals=1)

    # Create a class with the method
    test_class = ClassDef("TestClass", None, methods={"getValue": test_method}, static_methods={})

    # Test method resolution
    resolved = test_class.resolve_method("getValue")
    assert resolved == test_method

    # Test non-existent method
    with pytest.raises(LookupError):
        test_class.resolve_method("nonExistent")


def test_static_method_resolution():
    """Test static method resolution"""
    # Static method that adds two numbers
    add_method = Method(
        "add",
        [(LOAD_LOCAL, 0), (LOAD_LOCAL, 1), (IADD, None), (RETURN, None)],
        max_locals=2,
    )

    test_class = ClassDef("MathUtils", None, methods={}, static_methods={"add": add_method})

    resolved = test_class.resolve_static("add")
    assert resolved == add_method


def test_inheritance():
    """Test class inheritance and method resolution"""
    # Base class method
    base_method = Method("method", [(PUSH_CONST, 1), (RETURN, None)], max_locals=1)
    base_class = ClassDef("Base", None, methods={"method": base_method}, static_methods={})

    # Derived class that overrides the method
    derived_method = Method("method", [(PUSH_CONST, 2), (RETURN, None)], max_locals=1)
    derived_class = ClassDef(
        "Derived", base_class, methods={"method": derived_method}, static_methods={}
    )

    # Test that derived class method is resolved
    resolved = derived_class.resolve_method("method")
    assert resolved == derived_method

    # Test that base method can still be resolved from derived if not overridden
    other_base_method = Method("otherMethod", [(PUSH_CONST, 3), (RETURN, None)], max_locals=1)
    base_class.methods["otherMethod"] = other_base_method

    resolved_other = derived_class.resolve_method("otherMethod")
    assert resolved_other == other_base_method


def test_object_creation():
    """Test object reference creation"""
    test_class = ClassDef("TestClass", None, methods={}, static_methods={})
    obj = ObjRef(test_class, {"field": 42})

    assert obj.cls == test_class
    assert obj.fields["field"] == 42


def test_frame_stack():
    """Test frame stack operations"""
    method = Method("test", [(PUSH_CONST, 1), (RETURN, None)], max_locals=0)

    vm = VM()
    assert len(vm.stack_frames) == 0

    vm.push_frame(method, [])
    assert len(vm.stack_frames) == 1
    assert vm.stack_frames[-1].method == method

    vm.pop_frame()
    assert len(vm.stack_frames) == 0


def test_arithmetic_operations():
    """Test arithmetic operations in the VM"""
    # Method that computes (5 + 3) = 8
    method = Method(
        "arithmetic",
        [(PUSH_CONST, 5), (PUSH_CONST, 3), (IADD, None), (RETURN, None)],
        max_locals=0,
    )

    vm = VM()
    vm.push_frame(method, [])
    result = vm.run_until_return()

    assert result == 8


def test_complex_computation():
    """Test a more complex computation"""
    # Method that computes ((10 + 5) + (3 + 2)) = 20
    method = Method(
        "complex",
        [
            (PUSH_CONST, 10),
            (PUSH_CONST, 5),
            (IADD, None),  # 15 on stack
            (PUSH_CONST, 3),
            (PUSH_CONST, 2),
            (IADD, None),  # 5 on stack, 15 below
            (IADD, None),  # 20 on stack
            (RETURN, None),
        ],
        max_locals=0,
    )

    vm = VM()
    vm.push_frame(method, [])
    result = vm.run_until_return()

    assert result == 20
