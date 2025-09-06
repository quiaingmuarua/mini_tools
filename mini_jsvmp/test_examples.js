#!/usr/bin/env node

// 测试示例运行脚本
// 加载 mini_jsvmp 并运行示例

// 加载主文件
const jsvmp = require('./mini_jsvmp.js');
const examples = require('./example.js');

// 解构导入常用函数
const {
    compile,
    compileAndRun,
    runVM,
    packToHex,
    runHex,
    packToHexHardened,
    runHexHardened
} = jsvmp;

console.log('🧪 运行 Mini JSVMP 示例测试\n');

// 测试1：基础语法
console.log('1️⃣ 测试基础语法:');
try {
    compileAndRun(examples.basicSyntax);
    console.log('✅ 基础语法测试通过\n');
} catch (e) {
    console.log('❌ 基础语法测试失败:', e.message, '\n');
}

// 测试2：闭包
console.log('2️⃣ 测试闭包功能:');
try {
    compileAndRun(examples.closureExample);
    console.log('✅ 闭包测试通过\n');
} catch (e) {
    console.log('❌ 闭包测试失败:', e.message, '\n');
}

// 测试3：递归
console.log('3️⃣ 测试递归功能:');
try {
    compileAndRun(examples.recursionExample);
    console.log('✅ 递归测试通过\n');
} catch (e) {
    console.log('❌ 递归测试失败:', e.message, '\n');
}

// 测试4：条件控制
console.log('4️⃣ 测试条件控制:');
try {
    compileAndRun(examples.conditionalExample);
    console.log('✅ 条件控制测试通过\n');
} catch (e) {
    console.log('❌ 条件控制测试失败:', e.message, '\n');
}

// 测试5：字符串处理
console.log('5️⃣ 测试字符串处理:');
try {
    compileAndRun(examples.stringExample);
    console.log('✅ 字符串处理测试通过\n');
} catch (e) {
    console.log('❌ 字符串处理测试失败:', e.message, '\n');
}

// 测试6：VMP示例
console.log('6️⃣ 测试VMP示例代码:');
try {
    compileAndRun(examples.vmpExample);
    console.log('✅ VMP示例测试通过\n');
} catch (e) {
    console.log('❌ VMP示例测试失败:', e.message, '\n');
}

// 测试7：HEX序列化
console.log('7️⃣ 测试HEX序列化:');
try {
    const testCode = 'print("HEX test");';
    const {code, consts, functions} = compile(testCode);
    const hex = packToHex(code, consts, functions);
    runHex(hex);
    console.log('✅ HEX序列化测试通过\n');
} catch (e) {
    console.log('❌ HEX序列化测试失败:', e.message, '\n');
}

// 测试8：VMP保护
console.log('8️⃣ 测试VMP保护:');
try {
    const testCode = 'print("VMP protection test");';
    const {code, consts, functions} = compile(testCode);
    const vmpHex = packToHexHardened(code, consts, functions);
    runHexHardened(vmpHex);
    console.log('✅ VMP保护测试通过\n');
} catch (e) {
    console.log('❌ VMP保护测试失败:', e.message, '\n');
}

// 测试9：篡改检测
console.log('9️⃣ 测试篡改检测:');
try {
    const testCode = 'print("tamper test");';
    const {code, consts, functions} = compile(testCode);
    const vmpHex = packToHexHardened(code, consts, functions);

    // 尝试篡改
    const tamperedHex = vmpHex.slice(0, -8) + '00000000';

    try {
        runHexHardened(tamperedHex);
        console.log('❌ 篡改检测失败 - 应该抛出错误\n');
    } catch (tamperError) {
        console.log('✅ 篡改检测测试通过:', tamperError.message, '\n');
    }
} catch (e) {
    console.log('❌ 篡改检测测试失败:', e.message, '\n');
}

console.log('🎯 所有测试完成！');
