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

	.globl	main
	.p2align	4, 0x90
	.type	main,@function
main:
	.cfi_startproc
	subq	$24, %rsp
	.cfi_def_cfa_offset 32
	movl	$2, 20(%rsp)
	movl	$3, 16(%rsp)
	movabsq	$add, %rax
	movl	$2, %edi
	movl	$3, %esi
	callq	*%rax
	movl	%eax, 12(%rsp)
	movabsq	$fmt_int, %rdi
	movabsq	$printf, %rcx
	movl	%eax, %esi
	xorl	%eax, %eax
	callq	*%rcx
	movl	12(%rsp), %eax
	addq	$24, %rsp
	.cfi_def_cfa_offset 8
	retq
.Lfunc_end1:
	.size	main, .Lfunc_end1-main
	.cfi_endproc

	.type	fmt_int,@object
	.section	.rodata,"a",@progbits
fmt_int:
	.asciz	"%d\n"
	.size	fmt_int, 4

	.section	".note.GNU-stack","",@progbits
