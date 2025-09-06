; ModuleID = "minic"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

define i32 @"add"(i32 %"a.1", i32 %"b.1")
{
entry:
  %"a" = alloca i32
  %"b" = alloca i32
  store i32 %"b.1", i32* %"b"
  store i32 %"a.1", i32* %"a"
  br label %"body"
body:
  %"a.2" = load i32, i32* %"a"
  %"b.2" = load i32, i32* %"b"
  %"addtmp" = add i32 %"a.2", %"b.2"
  ret i32 %"addtmp"
}

define i32 @"main"()
{
entry:
  %"x" = alloca i32
  %"y" = alloca i32
  %"z" = alloca i32
  br label %"body"
body:
  store i32 2, i32* %"x"
  store i32 3, i32* %"y"
  %"x.1" = load i32, i32* %"x"
  %"y.1" = load i32, i32* %"y"
  %"calltmp" = call i32 @"add"(i32 %"x.1", i32 %"y.1")
  store i32 %"calltmp", i32* %"z"
  %"z.1" = load i32, i32* %"z"
  %".6" = getelementptr inbounds [4 x i8], [4 x i8]* @"fmt_int", i32 0, i32 0
  %".7" = call i32 (i8*, ...) @"printf"(i8* %".6", i32 %"z.1")
  %"z.2" = load i32, i32* %"z"
  ret i32 %"z.2"
}

declare i32 @"printf"(i8* %".1", ...)

@"fmt_int" = internal constant [4 x i8] c"%d\0a\00"