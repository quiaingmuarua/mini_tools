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

define i32 @"loop"()
{
entry:
  %"x" = alloca i32
  br label %"body"
body:
  %"negtmp" = sub i32 0, 3
  store i32 %"negtmp", i32* %"x"
  %"x.1" = load i32, i32* %"x"
  %"negtmp.1" = sub i32 0, %"x.1"
  %"cmptmp" = icmp eq i32 %"negtmp.1", 3
  br i1 %"cmptmp", label %"then", label %"else"
then:
  %"x.2" = load i32, i32* %"x"
  %"addtmp" = add i32 %"x.2", 10
  store i32 %"addtmp", i32* %"x"
  br label %"merge"
else:
  store i32 0, i32* %"x"
  br label %"merge"
merge:
  %"x.3" = load i32, i32* %"x"
  ret i32 %"x.3"
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
  %"calltmp" = call i32 @"loop"()
  store i32 %"calltmp", i32* %"y"
  %"x.1" = load i32, i32* %"x"
  %"y.1" = load i32, i32* %"y"
  %"calltmp.1" = call i32 @"add"(i32 %"x.1", i32 %"y.1")
  store i32 %"calltmp.1", i32* %"z"
  %"z.1" = load i32, i32* %"z"
  ret i32 %"z.1"
}
