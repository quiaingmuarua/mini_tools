#!/usr/bin/env python3
"""
Test suite for Mini ELF parser
"""

import io

import pytest

from mini_linker.mini_read_elf import (
    EI_CLASS,
    EI_DATA,
    ELFCLASS64,
    ELFDATA2LSB,
    ELFMAG,
    ELFFile,
    read_exact,
    uleb,
)


def test_read_exact():
    """Test read_exact helper function"""
    data = b"Hello, World!"
    stream = io.BytesIO(data)

    # Read exact number of bytes
    result = read_exact(stream, 5)
    assert result == b"Hello"

    # Read more bytes
    result = read_exact(stream, 2)
    assert result == b", "

    # Test EOF error
    with pytest.raises(EOFError):
        read_exact(stream, 20)  # More than available


def test_uleb():
    """Test uleb helper function"""
    # uleb just returns the value as-is in this implementation
    assert uleb(0) == 0
    assert uleb(42) == 42
    assert uleb(0xFFFFFFFF) == 0xFFFFFFFF


def test_elf_magic_validation():
    """Test ELF magic number validation"""
    # Valid ELF header start
    valid_elf_start = ELFMAG + b"\x02\x01\x01\x00" + b"\x00" * 8

    parser = ELFFile(valid_elf_start)
    # Should not raise an exception during magic validation
    assert parser.ei_class == 2  # ELFCLASS64
    assert parser.ei_data == 1  # ELFDATA2LSB


def test_invalid_elf_magic():
    """Test invalid ELF magic number detection"""
    # Invalid magic number
    invalid_data = b"FAKE" + b"\x02\x01\x01\x00" + b"\x00" * 8

    with pytest.raises(ValueError, match="Not an ELF file"):
        ELFFile(invalid_data)


def test_elf_class_detection():
    """Test ELF class (32/64 bit) detection"""
    # 64-bit ELF
    elf64_header = ELFMAG + bytes([ELFCLASS64, ELFDATA2LSB]) + b"\x01\x00" + b"\x00" * 8
    parser = ELFFile(elf64_header)
    assert parser.ei_class == ELFCLASS64
    assert parser.ei_class == ELFCLASS64

    # 32-bit ELF
    elf32_header = ELFMAG + bytes([1, ELFDATA2LSB]) + b"\x01\x00" + b"\x00" * 8  # 1 = ELFCLASS32
    parser = ELFFile(elf32_header)
    assert parser.ei_class == 1
    assert parser.ei_class == 1  # ELFCLASS32


def test_endianness_detection():
    """Test endianness detection"""
    # Little endian
    le_header = ELFMAG + bytes([ELFCLASS64, ELFDATA2LSB]) + b"\x01\x00" + b"\x00" * 8
    parser = ELFFile(le_header)
    assert parser.ei_data == ELFDATA2LSB
    assert parser.ei_data == ELFDATA2LSB

    # Big endian
    be_header = ELFMAG + bytes([ELFCLASS64, 2]) + b"\x01\x00" + b"\x00" * 8  # 2 = ELFDATA2MSB
    parser = ELFFile(be_header)
    assert parser.ei_data == 2
    assert parser.ei_data == 2  # ELFDATA2MSB


def test_minimal_elf_parsing():
    """Test parsing a minimal valid ELF header"""
    # Create a minimal but valid ELF64 header
    elf_header = (
        ELFMAG  # Magic number
        + bytes([ELFCLASS64])  # 64-bit
        + bytes([ELFDATA2LSB])  # Little endian
        + bytes([1])  # EV_CURRENT
        + bytes([0])  # Generic ABI
        + b"\x00" * 8  # Padding
        + b"\x02\x00"  # e_type: ET_EXEC
        + b"\x3e\x00"  # e_machine: EM_X86_64
        + b"\x01\x00\x00\x00"  # e_version
        + b"\x00" * 8  # e_entry
        + b"\x40\x00\x00\x00\x00\x00\x00\x00"  # e_phoff
        + b"\x00" * 8  # e_shoff
        + b"\x00\x00\x00\x00"  # e_flags
        + b"\x40\x00"  # e_ehsize
        + b"\x38\x00"  # e_phentsize
        + b"\x00\x00"  # e_phnum
        + b"\x40\x00"  # e_shentsize
        + b"\x00\x00"  # e_shnum
        + b"\x00\x00"  # e_shstrndx
    )

    # Should parse without errors
    parser = ELFFile(elf_header)
    assert parser.ei_class == ELFCLASS64
    assert parser.ei_data == ELFDATA2LSB


def test_empty_file():
    """Test handling of empty file"""
    with pytest.raises(EOFError):
        ELFFile(b"")


def test_truncated_header():
    """Test handling of truncated header"""
    # Only partial magic number
    truncated = b"\x7fEL"

    with pytest.raises(EOFError):
        ELFFile(truncated)


@pytest.mark.parametrize(
    "class_val,expected",
    [
        (1, False),  # ELFCLASS32
        (2, True),  # ELFCLASS64
    ],
)
def test_class_detection_parametrized(class_val, expected):
    """Parametrized test for ELF class detection"""
    header = ELFMAG + bytes([class_val, ELFDATA2LSB]) + b"\x01\x00" + b"\x00" * 8
    parser = ELFFile(header)
    assert (parser.ei_class == ELFCLASS64) == expected


@pytest.mark.parametrize(
    "data_val,expected",
    [
        (1, True),  # ELFDATA2LSB
        (2, False),  # ELFDATA2MSB
    ],
)
def test_endian_detection_parametrized(data_val, expected):
    """Parametrized test for endianness detection"""
    header = ELFMAG + bytes([ELFCLASS64, data_val]) + b"\x01\x00" + b"\x00" * 8
    parser = ELFFile(header)
    assert (parser.ei_data == ELFDATA2LSB) == expected
