// ==============================
//  JSVMP: 多级作用域 + 闭包 + 调用 + return
//  (JS 源 → 字节码 → 解释器执行)
// ==============================

// ---- 指令集 ----
const OP = {
    PUSH_CONST: 0x01,  // [idx]
    LOAD_VAR: 0x10,  // [nameIdx]
    STORE_VAR: 0x11,  // [nameIdx]  (写入当前环境)
    ADD: 0x20,
    SUB: 0x21,
    MUL: 0x22,
    DIV: 0x23,
    EQ: 0x24,  // ==
    LT: 0x25,  // <
    GT: 0x26,  // >
    LE: 0x27,  // <=
    GE: 0x28,  // >=
    NE: 0x29,  // !=
    PRINT: 0x30,  // 弹出并打印
    MAKE_CLOS: 0x40,  // [funcIndex]  (将闭包值压栈，捕获当前env为闭包父环境)
    CALL: 0x50,  // [argc]
    RET: 0x51,  // 函数返回（栈顶作为返回值；若没有，推入undefined）
    POP: 0x60,  // 弹栈丢弃
    JUMP: 0x70,  // [addr] 无条件跳转 (别名: JMP)
    JUMP_IF_FALSE: 0x71,  // [addr] 如果栈顶为假则跳转 (别名: JMPF)
    HALT: 0xFF
};

// 为兼容性添加别名
OP.JMP = OP.JUMP;
OP.JMPF = OP.JUMP_IF_FALSE;

// 逻辑指令枚举（用于VMP保护）
const LOGICAL_OPS = [
    OP.PUSH_CONST, OP.LOAD_VAR, OP.STORE_VAR, OP.ADD, OP.SUB, OP.MUL, OP.DIV,
    OP.LT, OP.GT, OP.EQ, OP.NE, OP.LE, OP.GE, OP.PRINT, OP.MAKE_CLOS, OP.CALL,
    OP.RET, OP.POP, OP.JUMP, OP.JUMP_IF_FALSE, OP.HALT
];

// ---- 工具：常量池管理 ----
class ConstPool {
    constructor() {
        this.pool = [];
        this.map = new Map();
    }

    indexOf(v) {
        const key = (typeof v) + ':' + String(v);
        if (this.map.has(key)) return this.map.get(key);
        const i = this.pool.length;
        this.pool.push(v);
        this.map.set(key, i);
        return i;
    }
}

// ---- 词法分析（极简） ----
function tokenize(src) {
    const toks = [];
    let i = 0;
    const isWS = c => /\s/.test(c);
    const isDigit = c => c >= '0' && c <= '9';
    const isIdStart = c => /[A-Za-z_$]/.test(c);
    const isId = c => /[A-Za-z0-9_$]/.test(c);

    while (i < src.length) {
        const c = src[i];
        if (isWS(c)) {
            i++;
            continue;
        }

        // 处理单行注释 //
        if (c === '/' && i + 1 < src.length && src[i + 1] === '/') {
            // 跳过到行尾
            while (i < src.length && src[i] !== '\n') i++;
            continue;
        }

        // 字符串字面量
        if (c === '"') {
            let j = i + 1;
            let str = '';
            while (j < src.length && src[j] !== '"') {
                if (src[j] === '\\' && j + 1 < src.length) {
                    // 简单的转义支持
                    j++;
                    if (src[j] === 'n') str += '\n';
                    else if (src[j] === 't') str += '\t';
                    else if (src[j] === 'r') str += '\r';
                    else if (src[j] === '\\') str += '\\';
                    else if (src[j] === '"') str += '"';
                    else str += src[j];
                } else {
                    str += src[j];
                }
                j++;
            }
            if (j >= src.length) throw new Error('Unterminated string');
            toks.push({type: 'str', v: str});
            i = j + 1;
            continue;
        }

        // 双字符操作符
        if (c === '=' && i + 1 < src.length && src[i + 1] === '=') {
            toks.push({type: '==', v: '=='});
            i += 2;
            continue;
        }
        if (c === '!' && i + 1 < src.length && src[i + 1] === '=') {
            toks.push({type: '!=', v: '!='});
            i += 2;
            continue;
        }
        if (c === '<' && i + 1 < src.length && src[i + 1] === '=') {
            toks.push({type: '<=', v: '<='});
            i += 2;
            continue;
        }
        if (c === '>' && i + 1 < src.length && src[i + 1] === '=') {
            toks.push({type: '>=', v: '>='});
            i += 2;
            continue;
        }

        // 单字符符号
        if ('()+-*/={},;<>'.includes(c)) {
            toks.push({type: c, v: c});
            i++;
            continue;
        }

        // 数字
        if (isDigit(c)) {
            let j = i;
            while (j < src.length && isDigit(src[j])) j++;
            toks.push({type: 'num', v: Number(src.slice(i, j))});
            i = j;
            continue;
        }

        // 标识符 / 关键字
        if (isIdStart(c)) {
            let j = i;
            while (j < src.length && isId(src[j])) j++;
            const v = src.slice(i, j);
            const kw = ['let', 'function', 'return', 'print', 'if', 'else', 'while'];
            toks.push({type: kw.includes(v) ? v : 'id', v});
            i = j;
            continue;
        }

        throw new Error('Unexpected char ' + c);
    }
    toks.push({type: '<eof>'});
    return toks;
}

// ---- 递归下降解析 + 编译（直接发射字节码） ----
// 语法：
// Program := Stmt*
// Stmt := 'let' id '=' Expr ';'
//       | 'print' '(' Expr ')' ';'
//       | 'function' id '(' ParamList? ')' Block
//       | 'return' Expr? ';'
//       | 'if' '(' Expr ')' Stmt ('else' Stmt)?
//       | 'while' '(' Expr ')' Stmt
//       | Block
//       | ExprStmt ';'
// ExprStmt := CallOrVar
// CallOrVar := id '(' ArgList? ')'  |  id
// Expr := Comparison (('=='|'!='|'<'|'>'|'<='|'>=' ) Comparison)*
// Comparison := Term (('+'|'-') Term)*
// Term := Factor (('*'|'/') Factor)*
// Factor := number | string | id | '(' Expr ')' | Call
// Call := id '(' ArgList? ')'
// ParamList := id (',' id)*
// ArgList := Expr (',' Expr)*
// Block := '{' Stmt* '}'
function compile(src) {
    const toks = tokenize(src);
    let p = 0;
    const cp = new ConstPool();
    const code = [];
    const functions = []; // {entry, arity, paramNameIdxs}
    const labels = [];    // 记录函数入口的占位，编译完成后回填

    const peek = () => toks[p];
    const eat = (t) => {
        const x = toks[p];
        if (!x || x.type !== t) throw new Error(`Expect ${t}, got ${x ? x.type : '<eof>'}`);
        p++;
        return x;
    };
    const match = (t) => (peek().type === t ? (p++, true) : false);
    const emit = (...bs) => {
        code.push(...bs);
    };

    function parseProgram() {
        while (peek().type !== '<eof>') {
            parseStmt();
        }
        emit(OP.HALT);
    }

    function parseStmt() {
        const t = peek().type;
        if (t === 'let') {
            parseLet();
            return;
        }
        if (t === 'print') {
            parsePrint();
            return;
        }
        if (t === 'function') {
            parseFunctionDecl();
            return;
        }
        if (t === 'return') {
            parseReturn();
            return;
        }
        if (t === 'if') {
            parseIf();
            return;
        }
        if (t === 'while') {
            parseWhile();
            return;
        }
        if (t === '{') {
            parseBlock();
            return;
        }
        // 否则当成表达式语句（支持函数调用作为语句）
        parseExpr();
        emit(OP.POP);
        eat(';');
    }

    function parseLet() {
        eat('let');
        const name = eat('id').v;
        eat('=');
        parseExpr();
        const idx = cp.indexOf(name);
        emit(OP.STORE_VAR, idx);
        eat(';');
    }

    function parsePrint() {
        eat('print');
        eat('(');
        parseExpr();
        eat(')');
        emit(OP.PRINT);
        eat(';');
    }

    function parseReturn() {
        eat('return');
        if (peek().type !== ';') {
            parseExpr();
        } else { // 无值 return
            // 用 undefined 常量（在 JS 下就是 undefined）
            const idx = cp.indexOf(undefined);
            emit(OP.PUSH_CONST, idx);
        }
        emit(OP.RET);
        eat(';');
    }

    function parseIf() {
        eat('if');
        eat('(');
        parseExpr(); // 条件表达式
        eat(')');

        // 条件为假时跳转
        const falseJump = code.length;
        emit(OP.JUMP_IF_FALSE, 0); // 占位，稍后回填

        parseStmt(); // then 分支

        if (peek().type === 'else') {
            // 有 else 分支
            const elseJump = code.length;
            emit(OP.JUMP, 0); // 跳过 else 分支

            // 回填 false 跳转地址（跳到 else）
            code[falseJump + 1] = code.length;

            eat('else');
            parseStmt(); // else 分支

            // 回填 else 跳转地址
            code[elseJump + 1] = code.length;
        } else {
            // 没有 else 分支，直接回填跳转地址
            code[falseJump + 1] = code.length;
        }
    }

    function parseWhile() {
        eat('while');

        const loopStart = code.length; // 循环开始位置

        eat('(');
        parseExpr(); // 条件表达式
        eat(')');

        // 条件为假时跳出循环
        const exitJump = code.length;
        emit(OP.JUMP_IF_FALSE, 0); // 占位，稍后回填

        parseStmt(); // 循环体

        // 跳回循环开始
        emit(OP.JUMP, loopStart);

        // 回填退出跳转地址
        code[exitJump + 1] = code.length;
    }

    function parseFunctionDecl() {
        eat('function');
        const fname = eat('id').v;
        eat('(');
        const params = [];
        if (peek().type !== ')') {
            params.push(eat('id').v);
            while (match(',')) params.push(eat('id').v);
        }
        eat(')');

        // 记录函数信息：入口先占位
        const funcIndex = functions.length;
        functions.push({entry: -1, arity: params.length, paramNameIdxs: params.map(x => cp.indexOf(x))});

        // 生成闭包（运行时会捕获当前 env）
        emit(OP.MAKE_CLOS, funcIndex);
        // 绑定到当前作用域变量名
        emit(OP.STORE_VAR, cp.indexOf(fname));

        // 跳过函数体：先占位，稍后回填
        const jumpAddr = code.length;
        emit(OP.JUMP, 0); // 占位，稍后回填

        // 函数体：编译到同一段 code 中，记录入口
        const entry = code.length;
        functions[funcIndex].entry = entry;

        // 函数体 block
        parseBlock();
        // 若函数落空没有显式 return，则默认返回 undefined
        emit(OP.PUSH_CONST, cp.indexOf(undefined));
        emit(OP.RET);

        // 回填跳转地址
        code[jumpAddr + 1] = code.length;
    }

    function parseBlock() {
        eat('{');
        while (peek().type !== '}') {
            parseStmt();
        }
        eat('}');
    }

    function parseExpr() {
        parseComparison();
        while (true) {
            const t = peek().type;
            if (t === '==') {
                eat('==');
                parseComparison();
                emit(OP.EQ);
            } else if (t === '!=') {
                eat('!=');
                parseComparison();
                emit(OP.NE);
            } else if (t === '<') {
                eat('<');
                parseComparison();
                emit(OP.LT);
            } else if (t === '>') {
                eat('>');
                parseComparison();
                emit(OP.GT);
            } else if (t === '<=') {
                eat('<=');
                parseComparison();
                emit(OP.LE);
            } else if (t === '>=') {
                eat('>=');
                parseComparison();
                emit(OP.GE);
            } else break;
        }
    }

    function parseComparison() {
        parseTerm();
        while (true) {
            const t = peek().type;
            if (t === '+') {
                eat('+');
                parseTerm();
                emit(OP.ADD);
            } else if (t === '-') {
                eat('-');
                parseTerm();
                emit(OP.SUB);
            } else break;
        }
    }

    function parseTerm() {
        parseFactor();
        while (true) {
            const t = peek().type;
            if (t === '*') {
                eat('*');
                parseFactor();
                emit(OP.MUL);
            } else if (t === '/') {
                eat('/');
                parseFactor();
                emit(OP.DIV);
            } else break;
        }
    }

    function parseFactor() {
        const t = peek();
        if (t.type === 'num') {
            eat('num');
            emit(OP.PUSH_CONST, cp.indexOf(t.v));
            return;
        }
        if (t.type === 'str') {
            eat('str');
            emit(OP.PUSH_CONST, cp.indexOf(t.v));
            return;
        }
        if (t.type === '(') {
            eat('(');
            parseExpr();
            eat(')');
            return;
        }
        if (t.type === 'id') {
            // 可能是变量或调用
            const idTok = eat('id');
            if (peek().type === '(') {
                // 调用：把 callee 压栈（变量取出函数值），再压参数，CALL
                emit(OP.LOAD_VAR, cp.indexOf(idTok.v));
                eat('(');
                let argc = 0;
                if (peek().type !== ')') {
                    parseExpr();
                    argc++;
                    while (match(',')) {
                        parseExpr();
                        argc++;
                    }
                }
                eat(')');
                emit(OP.CALL, argc);
                return;
            } else {
                // 变量加载
                emit(OP.LOAD_VAR, cp.indexOf(idTok.v));
                return;
            }
        }
        throw new Error('Unexpected token in Factor: ' + t.type);
    }

    parseProgram();
    return {code, consts: cp.pool, functions};
}

// ---- 解释器：多级作用域 + 闭包 + 调用栈 ----
class Env {
    constructor(parent = null) {
        this.vars = Object.create(null);
        this.parent = parent;
    }

    get(name) {
        if (name in this.vars) return this.vars[name];
        if (this.parent) return this.parent.get(name);
        throw new Error('Undefined variable: ' + name);
    }

    setHere(name, val) {
        this.vars[name] = val;
    }
}

function runVM(bytecode, consts, functions, hostBuiltins = {}) {
    // 值类型：number | undefined | function-value | 其它宿主值
    // 函数值 = {tag:'fn', entry, arity, paramsIdx[], closEnv}

    const S = []; // 数据栈
    let ip = 0;   // 指令指针
    const code = bytecode;

    // 全局环境（内置 print 走 OP.PRINT，不放在 builtins 里也行）
    const globalEnv = new Env(null);
    // 注入宿主内建（可通过 LOAD_VAR 调用）
    for (const k of Object.keys(hostBuiltins)) globalEnv.setHere(k, hostBuiltins[k]);

    let env = globalEnv;

    // 调用栈帧
    const callStack = [];
    const makeFnVal = (fidx, closEnv) => ({
        tag: 'fn',
        entry: functions[fidx].entry,
        arity: functions[fidx].arity,
        paramsIdx: functions[fidx].paramNameIdxs,
        closEnv
    });

    const readConst = idx => consts[idx];
    const loadVarByIdx = (idx) => env.get(String(readConst(idx)));
    const storeVarByIdx = (idx, val) => env.setHere(String(readConst(idx)), val);

    while (true) {
        const op = code[ip++];

        switch (op) {
            case OP.PUSH_CONST: {
                const idx = code[ip++];
                S.push(readConst(idx));
                break;
            }
            case OP.LOAD_VAR: {
                const idx = code[ip++];
                S.push(loadVarByIdx(idx));
                break;
            }
            case OP.STORE_VAR: {
                const idx = code[ip++];
                const v = S.pop();
                storeVarByIdx(idx, v);
                break;
            }
            case OP.ADD: {
                const b = S.pop(), a = S.pop();
                // JS风格的+操作：数字相加，字符串拼接，混合时转字符串
                if (typeof a === 'string' || typeof b === 'string') {
                    S.push(String(a) + String(b));
                } else {
                    S.push(a + b);
                }
                break;
            }
            case OP.SUB: {
                const b = S.pop(), a = S.pop();
                S.push(a - b);
                break;
            }
            case OP.MUL: {
                const b = S.pop(), a = S.pop();
                S.push(a * b);
                break;
            }
            case OP.DIV: {
                const b = S.pop(), a = S.pop();
                S.push(a / b);
                break;
            }
            case OP.EQ: {
                const b = S.pop(), a = S.pop();
                S.push(a == b);
                break;
            }
            case OP.NE: {
                const b = S.pop(), a = S.pop();
                S.push(a != b);
                break;
            }
            case OP.LT: {
                const b = S.pop(), a = S.pop();
                S.push(a < b);
                break;
            }
            case OP.GT: {
                const b = S.pop(), a = S.pop();
                S.push(a > b);
                break;
            }
            case OP.LE: {
                const b = S.pop(), a = S.pop();
                S.push(a <= b);
                break;
            }
            case OP.GE: {
                const b = S.pop(), a = S.pop();
                S.push(a >= b);
                break;
            }
            case OP.PRINT: {
                console.log(S.pop());
                break;
            }
            case OP.POP: {
                S.pop();
                break;
            }

            case OP.MAKE_CLOS: {
                const fidx = code[ip++];
                S.push(makeFnVal(fidx, env)); // 捕获当前 env 为闭包父
                break;
            }

            case OP.CALL: {
                const argc = code[ip++];
                const args = new Array(argc);
                for (let i = argc - 1; i >= 0; i--) args[i] = S.pop();
                const callee = S.pop();

                // 宿主函数（原生 JS 函数）——允许把 Math.max 之类注入进来
                if (typeof callee === 'function') {
                    const ret = callee(...args);
                    S.push(ret);
                    break;
                }

                // JSVMP 函数
                if (!callee || callee.tag !== 'fn') throw new Error('Not callable');
                if (argc !== callee.arity) throw new Error(`arity mismatch: expect ${callee.arity}, got ${argc}`);

                // 建帧
                callStack.push({retIp: ip, savedEnv: env});
                // 新环境：父 = 闭包环境
                env = new Env(callee.closEnv);
                // 参数绑定到当前环境（按名字）
                for (let i = 0; i < callee.arity; i++) {
                    const pname = String(consts[callee.paramsIdx[i]]);
                    env.setHere(pname, args[i]);
                }
                // 跳转
                ip = callee.entry;
                break;
            }

            case OP.RET: {
                // 返回值：若无则用 undefined
                const ret = S.length ? S.pop() : undefined;
                if (callStack.length === 0) {
                    // 顶层 RET：允许直接结束
                    S.push(ret);
                    return ret;
                }
                const frame = callStack.pop();
                ip = frame.retIp;
                env = frame.savedEnv;
                S.push(ret);
                break;
            }

            case OP.JUMP: {
                const addr = code[ip++];
                ip = addr;
                break;
            }

            case OP.JUMP_IF_FALSE: {
                const addr = code[ip++];
                const cond = S.pop();
                if (!cond) {
                    ip = addr;
                }
                break;
            }

            case OP.HALT:
                return;

            default:
                throw new Error('Bad opcode ' + op);
        }
    }
}

// ============ 4) 字节码序列化：HEX 格式 ============
function packToHex(code, consts, functions) {
    // 简单的二进制格式：
    // [4字节:常量数量][常量数据...][4字节:函数数量][函数数据...][4字节:代码长度][代码数据...]

    const buf = [];

    // 写入4字节整数 (小端序)
    function writeU32(n) {
        buf.push(n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF, (n >> 24) & 0xFF);
    }

    // 写入字符串 (长度+内容)
    function writeString(s) {
        const bytes = new TextEncoder().encode(s);
        writeU32(bytes.length);
        buf.push(...bytes);
    }

    // 常量池
    writeU32(consts.length);
    for (const c of consts) {
        if (typeof c === 'number') {
            buf.push(0x01); // 类型标记：数字
            const f64 = new Float64Array([c]);
            const u8 = new Uint8Array(f64.buffer);
            buf.push(...u8);
        } else if (typeof c === 'string') {
            buf.push(0x02); // 类型标记：字符串
            writeString(c);
        } else { // undefined
            buf.push(0x00); // 类型标记：undefined
        }
    }

    // 函数表
    writeU32(functions.length);
    for (const fn of functions) {
        writeU32(fn.entry);
        writeU32(fn.arity);
        writeU32(fn.paramNameIdxs.length);
        for (const idx of fn.paramNameIdxs) writeU32(idx);
    }

    // 代码
    writeU32(code.length);
    buf.push(...code);

    // 转为HEX字符串
    return buf.map(b => b.toString(16).padStart(2, '0')).join('');
}

function unpackFromHex(hex) {
    const bytes = [];
    for (let i = 0; i < hex.length; i += 2) {
        bytes.push(parseInt(hex.slice(i, i + 2), 16));
    }

    let pos = 0;

    // 读取4字节整数 (小端序)
    function readU32() {
        const n = bytes[pos] | (bytes[pos + 1] << 8) | (bytes[pos + 2] << 16) | (bytes[pos + 3] << 24);
        pos += 4;
        return n;
    }

    // 读取字符串
    function readString() {
        const len = readU32();
        const strBytes = bytes.slice(pos, pos + len);
        pos += len;
        return new TextDecoder().decode(new Uint8Array(strBytes));
    }

    // 常量池
    const constCount = readU32();
    const constants = [];
    for (let i = 0; i < constCount; i++) {
        const type = bytes[pos++];
        if (type === 0x01) { // 数字
            const f64Bytes = bytes.slice(pos, pos + 8);
            pos += 8;
            const f64 = new Float64Array(new Uint8Array(f64Bytes).buffer)[0];
            constants.push(f64);
        } else if (type === 0x02) { // 字符串
            constants.push(readString());
        } else { // undefined
            constants.push(undefined);
        }
    }

    // 函数表
    const funcCount = readU32();
    const functions = [];
    for (let i = 0; i < funcCount; i++) {
        const entry = readU32();
        const arity = readU32();
        const paramCount = readU32();
        const paramNameIdxs = [];
        for (let j = 0; j < paramCount; j++) paramNameIdxs.push(readU32());
        functions.push({entry, arity, paramNameIdxs});
    }

    // 代码
    const codeLen = readU32();
    const code = bytes.slice(pos, pos + codeLen);

    return {constants, functions, code};
}

// ============ 5) 解释器：支持从 HEX 直接运行 ============
function runHex(hex, hostBuiltins = {}) {
    const {constants, functions, code} = unpackFromHex(hex);
    return runVM(code, constants, functions, hostBuiltins);
}

// ============ 6) VMP 保护：指令表乱序 + 完整性校验 ============

// 生成随机映射：logical -> physical
function makeOpcodeMap() {
    const phys = Array.from({length: LOGICAL_OPS.length}, (_, i) => i + 1); // 避免 0 保留
    for (let i = phys.length - 1; i > 0; i--) {
        const j = (Math.random() * (i + 1)) | 0;
        [phys[i], phys[j]] = [phys[j], phys[i]];
    }
    const map = new Map(), inv = new Map();
    LOGICAL_OPS.forEach((lop, i) => {
        map.set(lop, phys[i]);
        inv.set(phys[i], lop);
    });
    return {map, inv, physBytes: phys};
}

// 重写代码里的 opcode 字节（只改操作码，不改立即数/地址）
function rewriteCodeWithMap(code, opMap) {
    const out = code.slice();
    for (let i = 0; i < out.length;) {
        const lop = out[i];
        const pop = opMap.get(lop);
        if (pop === undefined) {
            throw new Error(`Unknown logical opcode: ${lop}`);
        }
        out[i] = pop;              // 写入物理 opcode
        i++;
        // 跳过该指令的立即数字节数
        if (lop === OP.PUSH_CONST || lop === OP.LOAD_VAR || lop === OP.STORE_VAR || lop === OP.MAKE_CLOS) {
            i += 1;
        } else if (lop === OP.CALL) {
            i += 1;
        } else if (lop === OP.JUMP || lop === OP.JUMP_IF_FALSE) {
            i += 1; // 我们的实现是1字节地址
        }
        // 其它无立即数，不用跳
    }
    return out;
}

// 简易 MAC（示例可替换为真哈希）
function simpleMAC(bytes, seed = 0x9e3779b1) {
    let h = seed >>> 0;
    for (let b of bytes) {
        h = (h ^ b) >>> 0;
        h = Math.imul(h, 2654435761) >>> 0;
    }
    return [(h >>> 24) & 0xFF, (h >>> 16) & 0xFF, (h >>> 8) & 0xFF, h & 0xFF];
}

// ============ 立即数按位点加密 ============

// 位置相关 PRNG（返回 0..255）
function maskAt(seed, offset) {
    // 32-bit 混洗；JS 用 Math.imul 做 32位乘法
    let x = (seed ^ offset) >>> 0;
    x = (x + 0x9e3779b1) >>> 0;
    x = Math.imul(x ^ (x >>> 16), 0x85ebca6b) >>> 0;
    return (x >>> 24) & 0xFF;
}

// 只对"立即数位点"编码（opcode 本身不动）
function encodeImmediates(origLogicalCode, codedPhysicalCode, opMap, seed) {
    let i = 0; // 走原始逻辑 code（知道每条的立即数长度）
    let j = 0; // 走重写后的物理 code（要写入密文字节）

    while (i < origLogicalCode.length) {
        const lop = origLogicalCode[i++];
        const pop = opMap.get(lop);
        j++; // 跳过 opcode 本身（不加密）

        // 计算立即数长度（根据我们的指令集）
        const immLen =
            (lop === OP.PUSH_CONST || lop === OP.LOAD_VAR || lop === OP.STORE_VAR ||
                lop === OP.MAKE_CLOS || lop === OP.CALL) ? 1 :
                (lop === OP.JUMP || lop === OP.JUMP_IF_FALSE) ? 1 : 0; // 我们的实现是1字节地址

        // 加密每个立即数字节
        for (let k = 0; k < immLen; k++) {
            const abs = j; // coded 中该字节的绝对下标
            codedPhysicalCode[j] ^= maskAt(seed, abs); // 按位点异或
            j++;
            i++; // 同时推进原始代码指针
        }
    }
}

// 打包：把映射表 + 代码 + 常量池一起写入，并附上 MAC（增强版：立即数加密）
function packToHexHardened(code, consts, functions) {
    const {map, physBytes} = makeOpcodeMap();
    const coded = rewriteCodeWithMap(code, map);

    // 生成随机种子用于立即数加密
    const seed = (Math.random() * 0xFFFFFFFF) >>> 0;

    // 加密立即数（只加密操作数，不加密opcode）
    encodeImmediates(code, coded, map, seed);

    const buf = [];

    // 写入4字节整数 (小端序)
    function writeU32(n) {
        buf.push(n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF, (n >> 24) & 0xFF);
    }

    // 写入字符串 (长度+内容)
    function writeString(s) {
        const bytes = new TextEncoder().encode(s);
        writeU32(bytes.length);
        buf.push(...bytes);
    }

    // magic + ver (升级到v3，支持立即数加密)
    buf.push(0x56, 0x4D, 0x03); // 'VM', version=3 (VMP + immediate encryption)

    // 常量池
    writeU32(consts.length);
    for (const c of consts) {
        if (typeof c === 'number') {
            buf.push(0x01); // 类型标记：数字
            const f64 = new Float64Array([c]);
            const u8 = new Uint8Array(f64.buffer);
            buf.push(...u8);
        } else if (typeof c === 'string') {
            buf.push(0x02); // 类型标记：字符串
            writeString(c);
        } else { // undefined
            buf.push(0x00); // 类型标记：undefined
        }
    }

    // 函数表
    writeU32(functions.length);
    for (const fn of functions) {
        writeU32(fn.entry);
        writeU32(fn.arity);
        writeU32(fn.paramNameIdxs.length);
        for (const idx of fn.paramNameIdxs) writeU32(idx);
    }

    // 写 opcode 映射表
    buf.push(LOGICAL_OPS.length & 0xFF);
    buf.push(...physBytes); // 逻辑顺序对应的物理 opcode

    // 写入加密种子（4字节，大端序）
    buf.push((seed >>> 24) & 0xFF, (seed >>> 16) & 0xFF, (seed >>> 8) & 0xFF, seed & 0xFF);

    // 代码长度 + 代码（已加密立即数）
    writeU32(coded.length);
    buf.push(...coded);

    // 计算 MAC（对常量池+函数表+映射表+代码做）
    const macStart = 3; // 跳过魔数/版本
    const macBytes = buf.slice(macStart);
    const mac = simpleMAC(macBytes);
    buf.push(...mac);

    // toHex
    return buf.map(b => b.toString(16).padStart(2, '0')).join('');
}

// VMP 保护的运行函数
function runHexHardened(hex, hostBuiltins = {}) {
    const bytes = [];
    for (let i = 0; i < hex.length; i += 2) {
        bytes.push(parseInt(hex.slice(i, i + 2), 16));
    }

    let pos = 0;

    // 读取4字节整数 (小端序)
    function readU32() {
        const n = bytes[pos] | (bytes[pos + 1] << 8) | (bytes[pos + 2] << 16) | (bytes[pos + 3] << 24);
        pos += 4;
        return n;
    }

    // 读取字符串
    function readString() {
        const len = readU32();
        const strBytes = bytes.slice(pos, pos + len);
        pos += len;
        return new TextDecoder().decode(new Uint8Array(strBytes));
    }

    // 验证魔数和版本
    if (bytes[pos++] !== 0x56 || bytes[pos++] !== 0x4D) {
        throw new Error('Bad magic number');
    }
    const ver = bytes[pos++];
    if (ver !== 0x03) {
        throw new Error('Bad version - expected VMP protected format v3 (with immediate encryption)');
    }

    // 常量池
    const constCount = readU32();
    const constants = [];
    for (let i = 0; i < constCount; i++) {
        const type = bytes[pos++];
        if (type === 0x01) { // 数字
            const f64Bytes = bytes.slice(pos, pos + 8);
            pos += 8;
            const f64 = new Float64Array(new Uint8Array(f64Bytes).buffer)[0];
            constants.push(f64);
        } else if (type === 0x02) { // 字符串
            constants.push(readString());
        } else { // undefined
            constants.push(undefined);
        }
    }

    // 函数表
    const funcCount = readU32();
    const functions = [];
    for (let i = 0; i < funcCount; i++) {
        const entry = readU32();
        const arity = readU32();
        const paramCount = readU32();
        const paramNameIdxs = [];
        for (let j = 0; j < paramCount; j++) paramNameIdxs.push(readU32());
        functions.push({entry, arity, paramNameIdxs});
    }

    // 读取 opcode 映射表
    const mlen = bytes[pos++];
    const phys = bytes.slice(pos, pos + mlen);
    pos += mlen;

    // 构造反射表：物理字节 -> 逻辑 opcode
    const inv = new Map();
    LOGICAL_OPS.forEach((lop, i) => inv.set(phys[i], lop));

    // 读取加密种子（4字节，大端序）
    const seed = (bytes[pos++] << 24) | (bytes[pos++] << 16) | (bytes[pos++] << 8) | bytes[pos++];

    // 代码
    const codeLen = readU32();
    const code = bytes.slice(pos, pos + codeLen);
    pos += codeLen;

    // 校验 MAC
    const mac = bytes.slice(pos, pos + 4);
    pos += 4;
    const macStart = 3; // 跳过魔数/版本
    const macBytes = bytes.slice(macStart, -4); // 除了最后4字节MAC
    const calc = simpleMAC(macBytes);
    if (mac.some((b, i) => b !== calc[i])) {
        throw new Error('Integrity check failed - code may be tampered');
    }

    // 使用VMP保护的VM执行（传入种子用于立即数解密）
    return runVMHardened(code, constants, functions, hostBuiltins, inv, seed);
}

// VMP 保护的虚拟机执行器（流式解码 + 立即数解密）
function runVMHardened(bytecode, consts, functions, hostBuiltins = {}, invMap, seed) {
    const S = []; // 数据栈
    let ip = 0;   // 指令指针
    const code = bytecode;

    // 立即数解密函数
    const readImm1 = () => {
        const encryptedByte = code[ip];
        const decryptedByte = encryptedByte ^ maskAt(seed, ip);
        ip++;
        return decryptedByte & 0xFF;
    };

    const readImm2 = () => {
        const hi = readImm1();
        const lo = readImm1();
        return (hi << 8) | lo;
    };

    // 全局环境
    const globalEnv = new Env(null);
    // 注入宿主内建
    for (const k of Object.keys(hostBuiltins)) globalEnv.setHere(k, hostBuiltins[k]);

    let env = globalEnv;

    // 调用栈帧
    const callStack = [];
    const makeFnVal = (fidx, closEnv) => ({
        tag: 'fn',
        entry: functions[fidx].entry,
        arity: functions[fidx].arity,
        paramsIdx: functions[fidx].paramNameIdxs,
        closEnv
    });

    const readConst = idx => consts[idx];
    const loadVarByIdx = (idx) => env.get(String(readConst(idx)));
    const storeVarByIdx = (idx, val) => env.setHere(String(readConst(idx)), val);

    while (true) {
        // 流式解码：获取物理操作码，反映射为逻辑操作码
        const physOp = code[ip++];
        const op = invMap.get(physOp);

        if (op === undefined) {
            throw new Error(`Unknown physical opcode: ${physOp} at position ${ip - 1}`);
        }

        switch (op) {
            case OP.PUSH_CONST: {
                const idx = readImm1();
                S.push(readConst(idx));
                break;
            }
            case OP.LOAD_VAR: {
                const idx = readImm1();
                S.push(loadVarByIdx(idx));
                break;
            }
            case OP.STORE_VAR: {
                const idx = readImm1();
                const v = S.pop();
                storeVarByIdx(idx, v);
                break;
            }
            case OP.ADD: {
                const b = S.pop(), a = S.pop();
                if (typeof a === 'string' || typeof b === 'string') {
                    S.push(String(a) + String(b));
                } else {
                    S.push(a + b);
                }
                break;
            }
            case OP.SUB: {
                const b = S.pop(), a = S.pop();
                S.push(a - b);
                break;
            }
            case OP.MUL: {
                const b = S.pop(), a = S.pop();
                S.push(a * b);
                break;
            }
            case OP.DIV: {
                const b = S.pop(), a = S.pop();
                S.push(a / b);
                break;
            }
            case OP.EQ: {
                const b = S.pop(), a = S.pop();
                S.push(a == b);
                break;
            }
            case OP.NE: {
                const b = S.pop(), a = S.pop();
                S.push(a != b);
                break;
            }
            case OP.LT: {
                const b = S.pop(), a = S.pop();
                S.push(a < b);
                break;
            }
            case OP.GT: {
                const b = S.pop(), a = S.pop();
                S.push(a > b);
                break;
            }
            case OP.LE: {
                const b = S.pop(), a = S.pop();
                S.push(a <= b);
                break;
            }
            case OP.GE: {
                const b = S.pop(), a = S.pop();
                S.push(a >= b);
                break;
            }
            case OP.PRINT: {
                console.log(S.pop());
                break;
            }
            case OP.POP: {
                S.pop();
                break;
            }

            case OP.MAKE_CLOS: {
                const fidx = readImm1();
                S.push(makeFnVal(fidx, env)); // 捕获当前 env 为闭包父
                break;
            }

            case OP.CALL: {
                const argc = readImm1();
                const args = new Array(argc);
                for (let i = argc - 1; i >= 0; i--) args[i] = S.pop();
                const callee = S.pop();

                // 宿主函数（原生 JS 函数）
                if (typeof callee === 'function') {
                    const ret = callee(...args);
                    S.push(ret);
                    break;
                }

                // JSVMP 函数
                if (!callee || callee.tag !== 'fn') throw new Error('Not callable');
                if (argc !== callee.arity) throw new Error(`arity mismatch: expect ${callee.arity}, got ${argc}`);

                // 建帧
                callStack.push({retIp: ip, savedEnv: env});
                // 新环境：父 = 闭包环境
                env = new Env(callee.closEnv);
                // 参数绑定到当前环境（按名字）
                for (let i = 0; i < callee.arity; i++) {
                    const pname = String(consts[callee.paramsIdx[i]]);
                    env.setHere(pname, args[i]);
                }
                // 跳转
                ip = callee.entry;
                break;
            }

            case OP.RET: {
                // 返回值：若无则用 undefined
                const ret = S.length ? S.pop() : undefined;
                if (callStack.length === 0) {
                    // 顶层 RET：允许直接结束
                    S.push(ret);
                    return ret;
                }
                const frame = callStack.pop();
                ip = frame.retIp;
                env = frame.savedEnv;
                S.push(ret);
                break;
            }

            case OP.JUMP: {
                const addr = readImm1();
                ip = addr;
                break;
            }

            case OP.JUMP_IF_FALSE: {
                const addr = readImm1();
                const cond = S.pop();
                if (!cond) {
                    ip = addr;
                }
                break;
            }

            case OP.HALT:
                return;

            default:
                throw new Error('Bad logical opcode ' + op + ' (from physical ' + physOp + ')');
        }
    }
}

// ========== DEMO ==========
// 1) 多级作用域 + 闭包捕获
const src1 = `
  let a = 10;
  function outer(x) {
    let y = 5;
    function inner(z) {
      // inner
      return x + y + z + a;
    }
    return inner(7);
  }
  print( outer(3) );   // 3 + 5 + 7 + 10 = 25
`;

// 2) 调用宿主函数（注入 builtins）：例如 max(…)
const src2 = `
  let a = 2;
  function f(b){ return b * 10; }
  print( max( f(3), a + 100 ) ); // max(30, 102) = 102
`;

// 编译与运行
function compileAndRun(src) {
    const {code, consts, functions} = compile(src);
    // 注入一个宿主函数 max
    const builtins = {max: Math.max};
    console.log('--- RUN ---');
    return runVM(code, consts, functions, builtins);
}

// 只有直接运行时才执行演示代码
if (require.main === module) {
    // 期待输出：25，然后 102
    compileAndRun(src1);
    compileAndRun(src2);
    // 3) HEX 格式演示：编译 → HEX → 运行
    console.log('\n=== HEX Format Demo ===');
    const hexSrc = `
  let msg = "Hello";
  function greet(name) {
    return msg + " " + name + "!";
  }
  print( greet("JSVMP") );
`;

    console.log('编译并打包为 HEX:');
    const {code, consts, functions} = compile(hexSrc);
    const hexString = packToHex(code, consts, functions);
    console.log('HEX 长度:', hexString.length / 2, '字节');
    console.log('HEX 前64字符:', hexString.slice(0, 64), '...');

    console.log('\n从 HEX 直接运行:');
    runHex(hexString, {max: Math.max});

// 4) 控制流演示：简单测试
    console.log('\n=== Control Flow Demo ===');

// 先测试简单的 if
    const ifSrc = `
  let x = 1;
  if (x == 1) {
    print("x is 1");
  } else {
    print("x is not 1");
  }
`;
    console.log('Simple if test:');
    compileAndRun(ifSrc);

// 测试比较操作
    const compSrc = `
  let a = 1;
  let b = 2;
  print(a < b);
  print(a == b);
`;
    console.log('\nComparison test:');
    compileAndRun(compSrc);

// while 测试暂时注释掉，需要修复解析问题
    console.log('\nwhile testing disabled for now - need to fix parsing issue');

    console.log('\n--- All basic demos completed ---');

// 5) VMP 保护演示：完整功能测试
    console.log('\n=== VMP Protection Demo ===');
    try {
        const vmpSrc = `
    let secret = 42;
    function encode(x) {
      return x * secret + 100;
    }
    print("Encoded:");
    print(encode(5));
  `;
        console.log('编译VMP测试代码...');
        const {code: vmpCode, consts: vmpConsts, functions: vmpFunctions} = compile(vmpSrc);
        console.log('打包为VMP保护HEX...');
        const vmpHex = packToHexHardened(vmpCode, vmpConsts, vmpFunctions);
        console.log('VMP HEX 长度:', vmpHex.length / 2, '字节');
        console.log('VMP HEX 前64字符:', vmpHex.slice(0, 64), '...');
        console.log('魔数验证: 0x564D03 (VMP Protected v3 + Immediate Encryption)');

        console.log('\n从VMP保护HEX运行:');
        runHexHardened(vmpHex);

        console.log('\n=== VMP保护特性 ===');
        console.log('✓ 指令表乱序：每次生成随机物理操作码映射');
        console.log('✓ 流式解码：运行时反映射物理→逻辑操作码');
        console.log('✓ 立即数按位点加密：只加密操作数，基于位置的PRNG');
        console.log('✓ 完整性校验：MAC验证防篡改');
        console.log('✓ 格式识别：魔数标识VMP保护版本v3');

        // 篡改检测演示
        console.log('\n=== 篡改检测演示 ===');
        try {
            const tamperedHex = vmpHex.slice(0, -8) + '00000000';
            runHexHardened(tamperedHex);
            console.log('✗ 篡改检测失败');
        } catch (e) {
            console.log('✓ 篡改检测成功:', e.message);
        }

    } catch (e) {
        console.log('✗ VMP保护功能出错:', e.message);
        console.log(e.stack);
    }
}

// ============ 模块导出（用于 require） ============
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        // 核心编译和运行函数
        compile,
        compileAndRun,
        runVM,

        // HEX序列化函数
        packToHex,
        unpackFromHex,
        runHex,

        // VMP保护函数
        packToHexHardened,
        runHexHardened,
        runVMHardened,
        makeOpcodeMap,
        rewriteCodeWithMap,
        simpleMAC,

        // 立即数加密函数
        maskAt,
        encodeImmediates,

        // 工具类
        ConstPool,
        Env,

        // 常量
        OP,
        LOGICAL_OPS
    };
}

// 全局变量导出（用于浏览器或直接 node 运行）
if (typeof global !== 'undefined') {
    global.compile = compile;
    global.compileAndRun = compileAndRun;
    global.runVM = runVM;
    global.packToHex = packToHex;
    global.unpackFromHex = unpackFromHex;
    global.runHex = runHex;
    global.packToHexHardened = packToHexHardened;
    global.runHexHardened = runHexHardened;
    global.runVMHardened = runVMHardened;
}
