TOP, EVEN, ODD = "Top", "Even", "Odd"


def plus(a, b):
    if a == EVEN and b == EVEN:
        return EVEN
    if a == ODD and b == ODD:
        return EVEN
    if a in (EVEN, ODD) and b in (EVEN, ODD):
        return ODD
    return TOP


def mul(a, b):
    if a == EVEN or b == EVEN:
        return EVEN
    if a == ODD and b == ODD:
        return ODD
    return TOP


def mod2(a):
    if a in (EVEN, ODD):
        return a
    return TOP


def and1(a):
    if a == EVEN:
        return EVEN
    if a == ODD:
        return ODD
    return TOP


def check_pred(expr, xval):
    """expr: 'case1' or 'case2'"""
    if expr == "case1":  # (x*x)%2 == (x&1)
        t = mul(xval, xval)
        left = mod2(t)
        right = and1(xval)
    elif expr == "case2":  # (x*x+1)%2 == (x&1)
        t = mul(xval, xval)
        t = plus(t, ODD)  # +1 flips parity
        left = mod2(t)
        right = and1(xval)
    return left == right if left != TOP and right != TOP else TOP


for expr in ["case1", "case2"]:
    print("=== Checking", expr, "===")
    for xv in [EVEN, ODD]:
        print(f"x={xv} →", check_pred(expr, xv))
    print("x=Top →", check_pred(expr, TOP))
