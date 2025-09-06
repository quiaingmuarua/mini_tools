	.text
	.file	"<string>"
	.globl	add
	.p2align	4, 0x90
	.type	add,@function
add:
	.cfi_startproc
	movl	%esi, -8(%rsp)
	movl	%edi, -4(%rsp)
	movl	-4(%rsp), %eax
	addl	-8(%rsp), %eax
	retq
.Lfunc_end0:
	.size	add, .Lfunc_end0-add
	.cfi_endproc

	.globl	loop
	.p2align	4, 0x90
	.type	loop,@function
loop:
	.cfi_startproc
	movl	$-3, -4(%rsp)
	xorl	%eax, %eax
	testb	%al, %al
	jne	.LBB1_2
	addl	$10, -4(%rsp)
	movl	-4(%rsp), %eax
	retq
.LBB1_2:
	movl	$0, -4(%rsp)
	movl	-4(%rsp), %eax
	retq
.Lfunc_end1:
	.size	loop, .Lfunc_end1-loop
	.cfi_endproc

	.globl	main
	.p2align	4, 0x90
	.type	main,@function
main:
	.cfi_startproc
	subq	$24, %rsp
	.cfi_def_cfa_offset 32
	movl	$2, 12(%rsp)
	movabsq	$loop, %rax
	callq	*%rax
	movl	%eax, 20(%rsp)
	movl	12(%rsp), %edi
	movabsq	$add, %rcx
	movl	%eax, %esi
	callq	*%rcx
	movl	%eax, 16(%rsp)
	addq	$24, %rsp
	.cfi_def_cfa_offset 8
	retq
.Lfunc_end2:
	.size	main, .Lfunc_end2-main
	.cfi_endproc

	.section	".note.GNU-stack","",@progbits
