#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mini_readelf.py — a tiny readelf-like tool for practicing ELF parsing.
Supports: -h (ELF header), -l (program headers), -S (section headers), -s (symbols).
ELF32/ELF64, little/big endian.
"""

import argparse
import io
import struct
import sys

# ---- ELF constants (subset) ----
ELFMAG = b"\x7fELF"
EI_CLASS = 4
EI_DATA = 5
EI_VERSION = 6
EI_OSABI = 7

ELFCLASS32 = 1
ELFCLASS64 = 2

ELFDATA2LSB = 1
ELFDATA2MSB = 2

PT_TYPES = {
    0: "NULL", 1: "LOAD", 2: "DYNAMIC", 3: "INTERP", 4: "NOTE", 5: "SHLIB",
    6: "PHDR", 7: "TLS", 0x6474e550: "GNU_EH_FRAME", 0x6474e551: "GNU_STACK",
    0x6474e552: "GNU_RELRO", 0x6474e553: "GNU_PROPERTY"
}

SHT_TYPES = {
    0: "NULL", 1: "PROGBITS", 2: "SYMTAB", 3: "STRTAB", 4: "RELA", 5: "HASH",
    6: "DYNAMIC", 7: "NOTE", 8: "NOBITS", 9: "REL", 10: "SHLIB", 11: "DYNSYM",
    14: "INIT_ARRAY", 15: "FINI_ARRAY", 17: "GNU_HASH", 0x6ffffff6: "GNU_VERDEF",
    0x6fffffff: "GNU_VERNEED", 0x6ffffffe: "GNU_VERSYM"
}

ST_BIND = {0: "LOCAL", 1: "GLOBAL", 2: "WEAK"}
ST_TYPE = {0: "NOTYPE", 1: "OBJECT", 2: "FUNC", 3: "SECTION", 4: "FILE", 10: "LOOS"}

E_TYPE = {0: "NONE", 1: "REL", 2: "EXEC", 3: "DYN", 4: "CORE"}
E_MACHINE = {
    0: "NoMachine", 3: "x86", 40: "ARM", 62: "x86-64", 183: "AArch64", 243: "RISC-V"
}


# ---- Helpers ----
def read_exact(f: io.BufferedReader, n: int) -> bytes:
    b = f.read(n)
    if len(b) != n:
        raise EOFError("Unexpected EOF")
    return b


def uleb(val):  # map unsigned to signed repr friendly
    return val


def get_endian_prefix(ei_data: int) -> str:
    if ei_data == ELFDATA2LSB:
        return "<"
    elif ei_data == ELFDATA2MSB:
        return ">"
    else:
        raise ValueError(f"Unknown EI_DATA: {ei_data}")


def str_from_table(strtab: bytes, off: int) -> str:
    if off >= len(strtab):
        return ""
    end = strtab.find(b"\x00", off)
    if end == -1:
        end = len(strtab)
    return strtab[off:end].decode("utf-8", errors="replace")


# ---- Parsers ----
class ELFFile:
    def __init__(self, data: bytes):
        self.data = data
        self.f = io.BytesIO(data)
        self.parse_ident()
        self.parse_header()
        self.read_section_headers()
        self.read_program_headers()
        self.load_string_tables()

    def parse_ident(self):
        self.f.seek(0)
        ident = read_exact(self.f, 16)
        if ident[:4] != ELFMAG:
            raise ValueError("Not an ELF file")
        self.ei_class = ident[EI_CLASS]
        self.ei_data = ident[EI_DATA]
        self.ei_version = ident[EI_VERSION]
        self.ei_osabi = ident[EI_OSABI]
        self.end = get_endian_prefix(self.ei_data)

    def parse_header(self):
        self.f.seek(16)
        if self.ei_class == ELFCLASS32:
            fmt = self.end + "HHIIIIIHHHHHH"
            (self.e_type, self.e_machine, self.e_version,
             self.e_entry, self.e_phoff, self.e_shoff, self.e_flags,
             self.e_ehsize, self.e_phentsize, self.e_phnum,
             self.e_shentsize, self.e_shnum, self.e_shstrndx) = struct.unpack(fmt,
                                                                              read_exact(self.f, struct.calcsize(fmt)))
        elif self.ei_class == ELFCLASS64:
            fmt = self.end + "HHIQQQIHHHHHH"
            (self.e_type, self.e_machine, self.e_version,
             self.e_entry, self.e_phoff, self.e_shoff, self.e_flags,
             self.e_ehsize, self.e_phentsize, self.e_phnum,
             self.e_shentsize, self.e_shnum, self.e_shstrndx) = struct.unpack(fmt,
                                                                              read_exact(self.f, struct.calcsize(fmt)))
        else:
            raise ValueError(f"Unknown EI_CLASS: {self.ei_class}")

    def read_program_headers(self):
        self.ph = []
        if self.e_phoff == 0 or self.e_phnum == 0:
            return
        self.f.seek(self.e_phoff)
        if self.ei_class == ELFCLASS32:
            fmt = self.end + "IIIIIIII"
        else:
            fmt = self.end + "IIQQQQQQ"
        size = struct.calcsize(fmt)
        for _ in range(self.e_phnum):
            vals = struct.unpack(fmt, read_exact(self.f, size))
            if self.ei_class == ELFCLASS32:
                keys = ("p_type", "p_offset", "p_vaddr", "p_paddr", "p_filesz", "p_memsz", "p_flags", "p_align")
            else:
                keys = ("p_type", "p_flags", "p_offset", "p_vaddr", "p_paddr", "p_filesz", "p_memsz", "p_align")
            self.ph.append(dict(zip(keys, vals)))

    def read_section_headers(self):
        self.sh = []
        if self.e_shoff == 0 or self.e_shnum == 0:
            return
        self.f.seek(self.e_shoff)
        if self.ei_class == ELFCLASS32:
            fmt = self.end + "IIIIIIIIII"
        else:
            fmt = self.end + "IIQQQQIIQQ"
        size = struct.calcsize(fmt)
        for _ in range(self.e_shnum):
            vals = struct.unpack(fmt, read_exact(self.f, size))
            if self.ei_class == ELFCLASS32:
                keys = ("sh_name", "sh_type", "sh_flags", "sh_addr", "sh_offset", "sh_size", "sh_link", "sh_info",
                        "sh_addralign", "sh_entsize")
            else:
                keys = ("sh_name", "sh_type", "sh_flags", "sh_addr", "sh_offset", "sh_size", "sh_link", "sh_info",
                        "sh_addralign", "sh_entsize")
            self.sh.append(dict(zip(keys, vals)))

    def load_string_tables(self):
        self.shstrtab = b""
        self.strtabs = {}  # index -> bytes
        if self.sh and 0 <= self.e_shstrndx < len(self.sh):
            sh = self.sh[self.e_shstrndx]
            self.shstrtab = self.data[sh["sh_offset"]: sh["sh_offset"] + sh["sh_size"]]
        for idx, sh in enumerate(self.sh):
            if sh["sh_type"] == 3:  # STRTAB
                self.strtabs[idx] = self.data[sh["sh_offset"]: sh["sh_offset"] + sh["sh_size"]]

    def section_name(self, idx: int) -> str:
        if not self.sh:
            return ""
        sh = self.sh[idx]
        return str_from_table(self.shstrtab, sh["sh_name"])

    def dump_header(self):
        print("ELF Header:")
        print(f"  Magic:   7f 45 4c 46")
        klass = {ELFCLASS32: 'ELF32', ELFCLASS64: 'ELF64'}.get(self.ei_class, f'Unknown({self.ei_class})')
        data = {ELFDATA2LSB: '2\'s complement, little endian', ELFDATA2MSB: '2\'s complement, big endian'}.get(
            self.ei_data, f'Unknown({self.ei_data})')
        print(f"  Class:                             {klass}")
        print(f"  Data:                              {data}")
        print(f"  Version:                           {self.ei_version}")
        print(f"  OS/ABI:                            {self.ei_osabi}")
        print(f"  Type:                              {E_TYPE.get(self.e_type, self.e_type)}")
        print(f"  Machine:                           {E_MACHINE.get(self.e_machine, self.e_machine)}")
        print(f"  Entry point address:               0x{self.e_entry:x}")
        print(f"  Start of program headers:          {self.e_phoff} (bytes into file)")
        print(f"  Start of section headers:          {self.e_shoff} (bytes into file)")
        print(f"  Flags:                             0x{self.e_flags:x}")
        print(f"  Size of this header:               {self.e_ehsize} (bytes)")
        print(f"  Size of program headers:           {self.e_phentsize} (bytes)")
        print(f"  Number of program headers:         {self.e_phnum}")
        print(f"  Size of section headers:           {self.e_shentsize} (bytes)")
        print(f"  Number of section headers:         {self.e_shnum}")
        print(f"  Section header string table index: {self.e_shstrndx}")

    def dump_program_headers(self):
        if not self.ph:
            print("No program headers.")
            return
        print("Program Headers:")
        for i, p in enumerate(self.ph):
            ptype = PT_TYPES.get(p["p_type"], f"0x{p['p_type']:x}")
            print(f"  Type {ptype:>12} off 0x{p['p_offset']:x} vaddr 0x{p['p_vaddr']:x} paddr 0x{p['p_paddr']:x}")
            print(
                f"       filesz 0x{p['p_filesz']:x} memsz 0x{p['p_memsz']:x} flags 0x{p['p_flags']:x} align 0x{p['p_align']:x}")

    def dump_section_headers(self):
        if not self.sh:
            print("No section headers.")
            return
        print("Section Headers:")
        print("  [Nr] Name              Type            Addr             Off      Size     ES Flg Lk Inf Al")
        for i, sh in enumerate(self.sh):
            name = self.section_name(i)
            shtype = SHT_TYPES.get(sh["sh_type"], f"0x{sh['sh_type']:x}")
            print(
                f"  [{i:2}] {name:17.17} {shtype:14.14} {sh['sh_addr']:016x} {sh['sh_offset']:08x} {sh['sh_size']:08x} {sh['sh_entsize']:02x} "
                f"{sh['sh_flags']:03x} {sh['sh_link']:2} {sh['sh_info']:3} {sh['sh_addralign']:2}")

    def iter_symbols(self):
        # returns (table_name, list_of_symbols)
        for idx, sh in enumerate(self.sh):
            if sh["sh_type"] not in (2, 11):  # SYMTAB, DYNSYM
                continue
            tab_bytes = self.data[sh["sh_offset"]: sh["sh_offset"] + sh["sh_size"]]
            entsize = sh["sh_entsize"]
            if entsize == 0:
                # infer entsize by class
                entsize = 16 if self.ei_class == ELFCLASS32 else 24
            strtab = self.strtabs.get(sh["sh_link"], b"")
            syms = []
            off = 0
            while off + entsize <= len(tab_bytes):
                ent = tab_bytes[off:off + entsize]
                off += entsize
                if self.ei_class == ELFCLASS32:
                    st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack(
                        self.end + "IIIBBH", ent
                    )
                else:
                    st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack(
                        self.end + "IBBHQQ", ent
                    )
                bind = ST_BIND.get(st_info >> 4, str(st_info >> 4))
                typ = ST_TYPE.get(st_info & 0xF, str(st_info & 0xF))
                name = str_from_table(strtab, st_name)
                syms.append({
                    "name": name, "value": st_value, "size": st_size,
                    "bind": bind, "type": typ, "shndx": st_shndx
                })
            yield (self.section_name(idx), syms)

    def dump_symbols(self):
        printed_any = False
        for tabname, syms in self.iter_symbols():
            printed_any = True
            print(f"Symbol table '{tabname}': {len(syms)} entries")
            print("   Num:    Value             Size Type    Bind   Ndx Name")
            for i, s in enumerate(syms):
                ndx = f"{s['shndx']}" if isinstance(s['shndx'], int) else str(s['shndx'])
                print(f"  {i:5}: {s['value']:016x} {s['size']:5} {s['type']:<7} {s['bind']:<6} {ndx:>3} {s['name']}")
        if not printed_any:
            print("No symbol tables found.")


# ---- CLI ----
def main():
    ap = argparse.ArgumentParser(description="A tiny readelf-like parser.")
    ap.add_argument("file", help="ELF file path")
    ap.add_argument("-hH", "--elf-header", dest="show_header", action="store_true",
                    help="Display the ELF file header")
    ap.add_argument("-l", "--program-headers", dest="show_ph", action="store_true",
                    help="Display the program headers")
    ap.add_argument("-S", "--section-headers", dest="show_sh", action="store_true",
                    help="Display the section headers")
    ap.add_argument("-s", "--syms", dest="show_syms", action="store_true",
                    help="Display the symbol table")

    args = ap.parse_args()

    # Default to header if no flags
    if not (args.show_header or args.show_ph or args.show_sh or args.show_syms):
        args.show_header = True

    with open(args.file, "rb") as f:
        data = f.read()

    try:
        elf = ELFFile(data)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.show_header:
        elf.dump_header()
        print()
    if args.show_ph:
        elf.dump_program_headers()
        print()
    if args.show_sh:
        elf.dump_section_headers()
        print()
    if args.show_syms:
        elf.dump_symbols()


def parse_elf(file_path: str, show_header: bool = False, show_ph: bool = False,
              show_sh: bool = False, show_syms: bool = False):
    """
    直接解析ELF文件的函数版本

    Args:
        file_path: ELF文件路径
        show_header: 显示ELF文件头
        show_ph: 显示程序头
        show_sh: 显示段头
        show_syms: 显示符号表
    """
    # 默认显示文件头，如果没有指定任何选项
    if not (show_header or show_ph or show_sh or show_syms):
        show_header = True

    with open(file_path, "rb") as f:
        data = f.read()

    try:
        elf = ELFFile(data)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

    if show_header:
        elf.dump_header()
        print()
    if show_ph:
        elf.dump_program_headers()
        print()
    if show_sh:
        elf.dump_section_headers()
        print()
    if show_syms:
        elf.dump_symbols()

    return elf


if __name__ == "__main__":
    parse_elf(file_path="../lib/libollvm_demo.so", show_header=True, show_ph=True, show_sh=True, show_syms=True)
