# runtime.py
import os, sys, subprocess, tempfile, ctypes
from llvmlite import binding as llvm

def initialize_llvm():
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

def make_target_machine(opt_level=2):
    triple = llvm.get_default_triple()
    target = llvm.Target.from_triple(triple)
    return target.create_target_machine(opt=opt_level)

def jit_run(llvm_ir: str, func: str = "main") -> int:
    initialize_llvm()
    mod = llvm.parse_assembly(llvm_ir); mod.verify()
    tm = make_target_machine()
    backing = llvm.parse_assembly("")               # 空壳引擎
    engine = llvm.create_mcjit_compiler(backing, tm)
    engine.add_module(mod); engine.finalize_object(); engine.run_static_constructors()
    addr = engine.get_function_address(func)
    return ctypes.CFUNCTYPE(ctypes.c_int)(addr)()

def optimize_ir(llvm_ir: str, level: int = 2) -> str:
    initialize_llvm()
    mod = llvm.parse_assembly(llvm_ir); mod.verify()
    pmb = llvm.PassManagerBuilder(); pmb.opt_level = level
    pm  = llvm.ModulePassManager(); pmb.populate(pm); pm.run(mod)
    return str(mod)

def emit_object(llvm_ir: str, obj_path: str, opt_level: int = 2):
    initialize_llvm()
    tm = make_target_machine(opt_level)
    mod = llvm.parse_assembly(llvm_ir); mod.verify()
    with open(obj_path, "wb") as f: f.write(tm.emit_object(mod))

def link_executable(obj_path: str, exe_path: str):
    cc = "clang"
    cmd = [cc, obj_path, "-o", exe_path]
    if sys.platform == "darwin": cmd += ["-Wl,-dead_strip"]
    subprocess.check_call(cmd)

def emit_executable(llvm_ir: str, exe_path: str, opt_level: int = 2):
    with tempfile.TemporaryDirectory() as td:
        obj_path = os.path.join(td, "out.o")
        emit_object(llvm_ir, obj_path, opt_level)
        link_executable(obj_path, exe_path)
    return exe_path

def run_executable(exe_path: str) -> int:
    return subprocess.run([exe_path]).returncode

# —— 可选：给 Codegen 用的外部符号工具 ——
from llvmlite import ir
def declare_printf(module: ir.Module) -> ir.Function:
    fn = module.globals.get('printf')
    if isinstance(fn, ir.Function): return fn
    i8p = ir.IntType(8).as_pointer()
    fnty = ir.FunctionType(ir.IntType(32), [i8p], var_arg=True)
    return ir.Function(module, fnty, name="printf")

def intern_cstr(module: ir.Module, s: str, name: str) -> ir.GlobalVariable:
    data = bytearray(s.encode()) + b"\x00"
    arr_ty = ir.ArrayType(ir.IntType(8), len(data))
    gv = ir.GlobalVariable(module, arr_ty, name=name)
    gv.linkage = 'internal'; gv.global_constant = True
    gv.initializer = ir.Constant(arr_ty, data)
    return gv

def emit_assembly(llvm_ir: str, asm_path: str):
    initialize_llvm()
    tm = make_target_machine()
    mod = llvm.parse_assembly(llvm_ir); mod.verify()
    with open(asm_path, "w") as f: f.write(tm.emit_assembly(mod))

