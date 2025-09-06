#!/usr/bin/env node

// Mini JSVMP 示例代码集合
// 用于展示各种功能和用法

// 1. 基础语法示例
const basicSyntax = `
  // 变量声明和基础运算
  let a = 10;
  let b = 20;
  let sum = a + b;
  print("a + b =");
  print(sum);
  
  // 字符串操作
  let name = "JSVMP";
  let greeting = "Hello " + name + "!";
  print(greeting);
`;

// 2. 函数和闭包示例
const closureExample = `
  // 闭包示例：计数器工厂
  function makeCounter(start) {
    let count = start;
    function counter() {
      count = count + 1;
      return count;
    }
    return counter;
  }
  
  // 使用闭包
  let counter1 = makeCounter(0);
  let counter2 = makeCounter(100);
  
  print("Counter1:");
  print(counter1()); // 1
  print(counter1()); // 2
  
  print("Counter2:");
  print(counter2()); // 101
  print(counter2()); // 102
`;

// 3. 递归函数示例
const recursionExample = `
  // 阶乘函数
  function factorial(n) {
    if (n == 0) {
      return 1;
    } else {
      return n * factorial(n - 1);
    }
  }
  
  print("5! =");
  print(factorial(5)); // 120
  
  // 斐波那契数列
  function fib(n) {
    if (n == 0) {
      return 0;
    } else {
      if (n == 1) {
        return 1;
      } else {
        return fib(n - 1) + fib(n - 2);
      }
    }
  }
  
  print("fib(7) =");
  print(fib(7)); // 13
`;

// 4. 条件控制流示例
const conditionalExample = `
  // 比较运算和条件语句
  function checkNumber(x) {
    if (x > 0) {
      print("正数");
    } else {
      if (x == 0) {
        print("零");
      } else {
        print("负数");
      }
    }
  }
  
  checkNumber(5);
  checkNumber(0);
  checkNumber(-3);
  
  // 复杂条件
  function gradeCheck(score) {
    if (score >= 90) {
      print("优秀");
    } else {
      if (score >= 70) {
        print("良好");
      } else {
        if (score >= 60) {
          print("及格");
        } else {
          print("不及格");
        }
      }
    }
  }
  
  gradeCheck(95);
  gradeCheck(75);
  gradeCheck(65);
  gradeCheck(45);
`;

// 5. 字符串处理示例
const stringExample = `
  // 字符串拼接和处理
  let firstName = "Zhang";
  let lastName = "San";
  let fullName = firstName + " " + lastName;
  print("全名: " + fullName);
  
  // 数字转字符串拼接
  let age = 25;
  let info = "我今年 " + age + " 岁";
  print(info);
  
  // 模板式字符串构建
  function buildMessage(name, score) {
    let result = name + " 的得分是 " + score;
    if (score >= 80) {
      result = result + " (优秀)";
    } else {
      result = result + " (需要努力)";
    }
    return result;
  }
  
  print(buildMessage("小明", 95));
  print(buildMessage("小红", 65));
`;

// 6. VMP保护示例
const vmpExample = `
  // 模拟加密算法
  let secret = 42;
  
  function encode(data) {
    return data * secret + 1337;
  }
  
  function decode(encoded) {
    return (encoded - 1337) / secret;
  }
  
  let original = 123;
  let encoded = encode(original);
  let decoded = decode(encoded);
  
  print("原始数据: " + original);
  print("加密后: " + encoded);
  print("解密后: " + decoded);
`;

// 7. 数学计算示例
const mathExample = `
  // 使用扩展的内置函数
  let a = 3;
  let b = 7;
  
  print("max(3, 7) =");
  print(max(a, b));
  
  print("max(100, 50) =");
  print(max(100, 50));
`;

// 8. 复杂嵌套示例
const complexExample = `
  // 复杂嵌套函数和作用域
  function createCalculator() {
    let memory = 0;
    
    function add(x) {
      memory = memory + x;
      return memory;
    }
    
    function multiply(x) {
      memory = memory * x;
      return memory;
    }
    
    function getMemory() {
      return memory;
    }
    
    function reset() {
      memory = 0;
      return memory;
    }
    
    // 返回计算器接口
    return {
      add: add,
      multiply: multiply,
      memory: getMemory,
      reset: reset
    };
  }
  
  // 注意：这个示例需要对象字面量支持，目前简化版本
  let calc = createCalculator();
  print("初始值:");
  print(calc.memory());
`;

// 简单演示（用于直接运行测试）
if (require.main === module) {
    console.log('🚀 Mini JSVMP 示例代码集合');
    console.log('='.repeat(50));
    console.log('这个文件包含了各种示例代码。');
    console.log('运行 test_examples.js 来执行所有示例。');
    console.log('或者 require() 这个模块来获取示例代码字符串。');
}

// 导出所有示例
module.exports = {
    basicSyntax,
    closureExample,
    recursionExample,
    conditionalExample,
    stringExample,
    vmpExample,
    mathExample,
    complexExample
};