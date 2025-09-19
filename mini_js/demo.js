// ---- minimal_vm.js ----
// minimal stack VM
globalThis.consts = [10, 20];
globalThis.bytecode = [0, 0,  // PUSH_CONST 0
                       0, 1,  // PUSH_CONST 1
                       2,     // ADD
                       3];    // RET

globalThis.handlers = [
  function PUSH_CONST(pc) {
    const idx = bytecode[pc+1];
    stack.push(consts[idx]);
    return pc + 2;
  },
  // (not used)
];

function run_vm(code) {
  let pc = 0;
  globalThis.stack = [];
  while (pc < code.length) {
    const op = code[pc++];
    switch (op) {
      case 0: { // PUSH_CONST
        const idx = code[pc++];
        stack.push(consts[idx]);
        break;
      }
      case 2: { // ADD
        const b = stack.pop(), a = stack.pop();
        stack.push(a + b);
        break;
      }
      case 3: {
        return stack.pop();
      }
      default: throw new Error('unknown op ' + op);
    }
  }
}

// ---- instrumentation: proxy bytecode ----
const orig = globalThis.bytecode;
globalThis.bytecode = new Proxy(orig, {
  get(t, p) {
    if (String(Number(p)) === p) {
      console.log(`[GET] idx=${p} val=${t[p]}`);
    }
    return t[p];
  },
  set(t, p, v) { console.log(`[SET] idx=${p} => ${v}`); t[p] = v; return true; }
});

console.log('vm result =', run_vm(globalThis.bytecode));
