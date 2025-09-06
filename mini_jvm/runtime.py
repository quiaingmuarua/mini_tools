# tiny_vm_static.py
from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple

# ---------- Bytecode opcodes ----------
LOAD_LOCAL = "LOAD_LOCAL"    # push local[slot]
STORE_LOCAL = "STORE_LOCAL"  # pop -> local[slot]
PUSH_CONST = "PUSH_CONST"    # push immediate int
IADD       = "IADD"          # pop b, pop a, push a+b
RETURN     = "RETURN"        # return from current frame
CALL_VIRT  = "CALL_VIRT"     # pop recv; dynamic dispatch on recv.class
CALL_STATIC= "CALL_STATIC"   # pop N args; call class.static[method]

@dataclass
class Method:
    name: str
    code: List[Tuple[str, Any]]
    max_locals: int  # number of local slots (for static, it's the arg count)

@dataclass
class ClassDef:
    name: str
    super: Optional["ClassDef"]
    methods: Dict[str, Method]          # instance (virtual) methods
    static_methods: Dict[str, Method]   # static methods

    # virtual resolve
    def resolve_method(self, name: str) -> Method:
        c = self
        while c:
            if name in c.methods:
                return c.methods[name]
            c = c.super
        raise LookupError(f"{self.name}: virtual method {name} not found")

    # static resolve (no hierarchy walk needed in JVM,但这里给个单层字典)
    def resolve_static(self, name: str) -> Method:
        if name in self.static_methods:
            return self.static_methods[name]
        raise LookupError(f"{self.name}: static method {name} not found")

@dataclass
class ObjRef:
    cls: ClassDef
    fields: Dict[str, Any]

@dataclass
class Frame:
    method: Method
    locals: List[Any]
    stack: List[Any]
    ip: int = 0

class VM:
    def __init__(self, trace=False):
        self.stack_frames: List[Frame] = []
        self.trace = trace

    def push_frame(self, method: Method, args: List[Any]):
        frame = Frame(method=method, locals=[None]*method.max_locals, stack=[])
        for i, v in enumerate(args):
            frame.locals[i] = v
        self.stack_frames.append(frame)
        if self.trace:
            print(f"\n-- push_frame: {method.name} --")
            self.dump_frame()

    def pop_frame(self) -> Frame:
        frame = self.stack_frames.pop()
        if self.trace:
            print(f"-- pop_frame: {frame.method.name} --\n")
        return frame

    def current(self) -> Frame:
        return self.stack_frames[-1]

    def step(self):
        f = self.current()
        op_tuple = f.method.code[f.ip]
        op = op_tuple[0]
        arg = list(op_tuple[1:])
        f.ip += 1

        if self.trace:
            print(f"ip={f.ip-1:<2} op={op} arg={arg if arg else ''}")

        if op == LOAD_LOCAL:
            idx = arg[0]; f.stack.append(f.locals[idx])

        elif op == STORE_LOCAL:
            idx = arg[0]; f.locals[idx] = f.stack.pop()

        elif op == PUSH_CONST:
            f.stack.append(arg[0])

        elif op == IADD:
            b = f.stack.pop(); a = f.stack.pop(); f.stack.append(a + b)

        elif op == CALL_VIRT:
            method_name = arg[0]
            recv = f.stack.pop()
            if not isinstance(recv, ObjRef):
                raise TypeError("CALL_VIRT expects an object")
            target = recv.cls.resolve_method(method_name)  # 动态分派
            self.push_frame(target, [recv])                # this 放在 slot0
            ret = self.run_until_return()
            if ret is not None:
                f.stack.append(ret)

        elif op == CALL_STATIC:
            # 形如 (class_def, method_name, n_args)
            cls: ClassDef = arg[0]
            method_name: str = arg[1]
            n_args: int = arg[2]
            target = cls.resolve_static(method_name)       # 静态解析（不看接收者类型）
            # 从操作数栈弹 n_args（注意参数顺序）
            args = [f.stack.pop() for _ in range(n_args)][::-1]
            self.push_frame(target, args)
            ret = self.run_until_return()
            if ret is not None:
                f.stack.append(ret)

        elif op == RETURN:
            val = f.stack.pop() if f.stack else None
            self.pop_frame()
            return val

        else:
            raise ValueError(f"Unknown opcode {op}")

        if self.trace:
            self.dump_frame()
        return None

    def run_until_return(self):
        while self.stack_frames:
            ret = self.step()
            if ret is not None:
                return ret
        return None

    def dump_frame(self):
        f = self.current()
        print(f"  method: {f.method.name}")
        print(f"  locals: {f.locals}")
        print(f"  stack : {f.stack}")
        print()

# ---------- Build classes ----------
# Animal.sound() -> 1
Animal_sound = Method("sound", [(PUSH_CONST, 1), (RETURN,)], max_locals=1)
Animal = ClassDef("Animal", None, methods={"sound": Animal_sound}, static_methods={})

# Dog overrides sound() -> 2
Dog_sound = Method("sound", [(PUSH_CONST, 2), (RETURN,)], max_locals=1)
Dog = ClassDef("Dog", Animal, methods={"sound": Dog_sound}, static_methods={})

# Util.add(x, y) is static -> return x+y
Util_add = Method(
    "add",
    [
        (LOAD_LOCAL, 0),   # x
        (LOAD_LOCAL, 1),   # y
        (IADD,),           # x+y
        (RETURN,),
    ],
    max_locals=2,          # 两个形参，无 this
)
Util = ClassDef("Util", None, methods={}, static_methods={"add": Util_add})

# Main.call(a): return a.sound();
Main_call = Method(
    "Main.call",
    [
        (LOAD_LOCAL, 0),          # a
        (CALL_VIRT, "sound"),     # 虚调用
        (RETURN,),
    ],
    max_locals=1,
)

# Main.staticDemo(): return Util.add(7, 5);
Main_staticDemo = Method(
    "Main.staticDemo",
    [
        (PUSH_CONST, 7),
        (PUSH_CONST, 5),
        (CALL_STATIC, Util, "add", 2),  # 静态调用，弹 2 个实参
        (RETURN,),
    ],
    max_locals=0,  # 无局部（这里全用常量入栈）
)

if __name__ == "__main__":
    vm = VM(trace=True)

    # 动态分派演示：Main.call(new Dog()) -> 2
    dog = ObjRef(Dog, {})
    vm.push_frame(Main_call, [dog])
    print("call(new Dog()) =>", vm.run_until_return())

    # 静态绑定演示：Main.staticDemo() -> Util.add(7,5) = 12
    vm.push_frame(Main_staticDemo, [])
    print("staticDemo()    =>", vm.run_until_return())