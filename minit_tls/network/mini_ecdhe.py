"""
ECDH（椭圆曲线迪菲-赫尔曼密钥交换）完整实现
基于 NIST P-256 曲线（secp256r1）

这个模块实现了：
1. 椭圆曲线点运算（加法、倍点、标量乘法）
2. ECDHE 密钥交换协议
3. HKDF 密钥派生函数
4. SEC1 标准的公钥编码/解码

安全特性：
- 使用加密安全的随机数生成器
- 支持点压缩以节省带宽
- 包含完整的点验证
- 抗侧信道攻击的标量乘法实现
"""

# ==================== P-256 椭圆曲线参数 ====================

# 素数域 p：定义椭圆曲线所在的有限域 F_p
# P-256 使用的是一个特殊的素数，形式为 2^256 - 2^224 + 2^192 + 2^96 - 1
p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF

# 椭圆曲线方程: y^2 = x^3 + a*x + b (mod p)
# P-256 曲线的参数 a 和 b

# 参数 a = -3 mod p（等价于 p-3）
# 选择 a=-3 是为了优化点加法运算的性能
a = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC  # 即 -3 mod p

# 参数 b：曲线的另一个定义参数，这个值是随机选择的
b = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B

# 基点 G = (Gx, Gy)：椭圆曲线的生成元
# 所有公钥都是基点 G 的标量倍数：公钥 = 私钥 × G
Gx = 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296
Gy = 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5
G = (Gx, Gy)

# 基点的阶 n：满足 n × G = O（无穷远点）的最小正整数
# 这也是私钥的取值范围 [1, n-1]
# P-256 的余因子 h=1，表示曲线上所有点都在主子群中
n = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551


# ==================== 有限域运算函数 ====================


def fadd(x, y):
    """有限域加法：(x + y) mod p"""
    return (x + y) % p


def fsub(x, y):
    """有限域减法：(x - y) mod p"""
    return (x - y) % p


def fmul(x, y):
    """有限域乘法：(x * y) mod p"""
    return (x * y) % p


def finv(x):
    """
    有限域求逆：计算 x 的模 p 逆元
    使用费马小定理：在素数域中，x^(-1) ≡ x^(p-2) (mod p)
    Python 3.8+ 支持 pow(x, -1, p) 直接计算模逆
    """
    return pow(x, -1, p)  # 或 pow(x, p-2, p)


# ==================== 椭圆曲线点运算 ====================

O = None  # 无穷远点（椭圆曲线群的单位元）


def is_on_curve(P):
    """
    验证点是否在椭圆曲线上

    Args:
        P: 椭圆曲线上的点 (x, y) 或无穷远点 None

    Returns:
        bool: 点是否满足曲线方程 y^2 = x^3 + ax + b (mod p)
    """
    if P is None:  # 无穷远点默认在曲线上
        return True
    x, y = P
    # 验证曲线方程：y^2 ≡ x^3 + ax + b (mod p)
    return (y * y - (x * x * x + a * x + b)) % p == 0


def negate(P):
    """
    计算点的负元：P 的负元是 (x, -y)
    几何意义：关于 x 轴的对称点

    Args:
        P: 椭圆曲线上的点

    Returns:
        点 P 的负元
    """
    if P is None:
        return None
    x, y = P
    return (x, (-y) % p)


def point_add(P1, P2):
    """
    椭圆曲线点加法运算
    这是椭圆曲线群的核心运算，定义了群结构

    几何解释：
    - 两个不同点：连接两点的直线与曲线的第三个交点，再关于 x 轴对称
    - 相同点（倍点）：在该点的切线与曲线的交点，再关于 x 轴对称

    Args:
        P1, P2: 椭圆曲线上的点

    Returns:
        P1 + P2 的结果点
    """
    # 单位元性质：P + O = O + P = P
    if P1 is None:
        return P2
    if P2 is None:
        return P1

    x1, y1 = P1
    x2, y2 = P2

    # 逆元性质：P + (-P) = O
    if x1 == x2 and (y1 + y2) % p == 0:
        return O

    if x1 == x2 and y1 == y2:
        # 倍点情况：P + P = 2P
        # 特殊情况：如果切点的 y 坐标为 0，则 2P = O
        if y1 % p == 0:
            return O
        # 切线斜率：m = (3x1² + a) / (2y1)
        m = (3 * x1 * x1 + a) * finv(2 * y1) % p
    else:
        # 一般情况：两个不同点相加
        # 连线斜率：m = (y2 - y1) / (x2 - x1)
        m = (y2 - y1) * finv((x2 - x1) % p) % p

    # 第三个交点的 x 坐标：x3 = m² - x1 - x2
    x3 = (m * m - x1 - x2) % p
    # 对称得到最终点：y3 = m(x1 - x3) - y1
    y3 = (m * (x1 - x3) - y1) % p
    return (x3, y3)


def point_double(P):
    """
    椭圆曲线点倍乘：计算 2P
    这是 point_add(P, P) 的优化版本

    Args:
        P: 椭圆曲线上的点

    Returns:
        2P 的结果
    """
    # 也可直接调用 return point_add(P, P)，但独立实现更清晰
    if P is None:
        return O
    x1, y1 = P
    # 特殊情况：如果 y1 = 0，则切线垂直，2P = O
    if y1 % p == 0:
        return O

    # 切线斜率：m = (3x1² + a) / (2y1)
    m = (3 * x1 * x1 + a) * finv(2 * y1) % p
    # 计算 2P 的坐标
    x3 = (m * m - 2 * x1) % p
    y3 = (m * (x1 - x3) - y1) % p
    return (x3, y3)


def scalar_mult(k, P):
    """
    椭圆曲线标量乘法：计算 k × P
    这是椭圆曲线密码学中最重要的运算

    使用 Montgomery 阶梯算法，具有以下优点：
    - 抗简单能量分析攻击（SPA）
    - 每一位都执行相同的操作模式
    - 时间复杂度 O(log k)

    Args:
        k: 标量（私钥）
        P: 椭圆曲线上的点（通常是基点 G）

    Returns:
        k × P 的结果点（公钥）
    """
    if P is None:
        return O

    # 将标量规约到 [0, n-1] 范围内
    k = k % n
    if k == 0:
        return O

    # Montgomery 阶梯算法
    # R0 和 R1 始终满足：R1 = R0 + P
    R0, R1 = O, P

    # 从最高位开始处理每一位
    for i in reversed(range(k.bit_length())):
        bit = (k >> i) & 1
        if bit == 0:
            # 当前位为 0：R1 = R0 + R1, R0 = 2*R0
            R1 = point_add(R0, R1)
            R0 = point_double(R0)
        else:
            # 当前位为 1：R0 = R0 + R1, R1 = 2*R1
            R0 = point_add(R0, R1)
            R1 = point_double(R1)
    return R0


# ==================== 密钥生成与 ECDHE ====================

import hashlib
import hmac
import secrets


def gen_keypair():
    """
    生成 ECDHE 密钥对

    密钥生成过程：
    1. 生成随机私钥 sk ∈ [1, n-1]
    2. 计算公钥 pk = sk × G
    3. 验证公钥的有效性

    Returns:
        tuple: (私钥, 公钥)

    安全注意事项：
    - 使用密码学安全的随机数生成器 secrets
    - 私钥范围严格控制在 [1, n-1]
    - 生成后验证公钥有效性
    """
    # 生成随机私钥，范围 [1, n-1]
    sk = secrets.randbelow(n - 1) + 1
    # 计算对应的公钥：pk = sk × G
    pk = scalar_mult(sk, G)

    # 安全验证：确保公钥在曲线上且不是无穷远点
    assert is_on_curve(pk) and pk is not O
    return sk, pk


def ecdhe_shared(my_sk, peer_pk):
    """
    ECDHE 共享密钥计算

    ECDHE 协议核心：
    - Alice 有密钥对 (a, A = a×G)
    - Bob 有密钥对 (b, B = b×G)
    - 交换公钥后，双方都能计算相同的共享密钥：
      * Alice 计算：a × B = a × (b×G) = ab×G
      * Bob 计算：b × A = b × (a×G) = ba×G
    - 共享密钥是椭圆曲线点的 x 坐标

    Args:
        my_sk: 自己的私钥
        peer_pk: 对方的公钥

    Returns:
        bytes: 32字节的共享密钥（x 坐标的大端序表示）

    安全特性：
    - 计算不可行性：攻击者难以从公钥推出私钥（ECDLP 困难性）
    - 完美前向安全：临时密钥用完即丢弃
    """
    # 安全验证：确保对方公钥有效
    # P-256 的余因子 h=1，简化了子群检查
    assert peer_pk is not O and is_on_curve(peer_pk)

    # 计算共享点：S = my_sk × peer_pk
    S = scalar_mult(my_sk, peer_pk)  # S = (x, y)

    # 共享点不应为无穷远点（极低概率事件）
    assert S is not O

    # 提取共享密钥：使用 x 坐标作为密钥材料
    xS, _ = S

    # 转换为 32 字节大端序格式，符合标准约定
    return xS.to_bytes(32, "big")


# ==================== 密钥派生函数 HKDF ====================


def hkdf_sha256(ikm: bytes, salt: bytes = b"", info: bytes = b"", length: int = 32) -> bytes:
    """
    HMAC-based Key Derivation Function (HKDF) - RFC 5869

    HKDF 是一个安全的密钥派生函数，广泛用于现代密码学协议：
    - TLS 1.3、Signal 协议、Noise 协议等都使用 HKDF
    - 将输入密钥材料"拉伸"为所需长度的密钥

    两阶段设计：
    1. Extract 阶段：从输入密钥材料中提取随机性
    2. Expand 阶段：将提取的随机性扩展为所需长度

    Args:
        ikm: 输入密钥材料（Input Key Material），如 ECDHE 共享密钥
        salt: 盐值，增强安全性（可选）
        info: 上下文信息，绑定特定用途（可选）
        length: 输出密钥长度

    Returns:
        派生的密钥
    """
    # HKDF-Extract: PRK = HMAC-Hash(salt, IKM)
    # 如果没有提供盐值，使用全零盐值
    if salt is None or len(salt) == 0:
        salt = b"\x00" * hashlib.sha256().digest_size  # 32 字节的零盐值

    # 提取阶段：生成伪随机密钥 PRK
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()

    # HKDF-Expand: OKM = HMAC-Hash(PRK, info || counter)
    okm = b""  # 输出密钥材料
    t = b""  # 前一轮的输出
    ctr = 1  # 计数器

    # 扩展阶段：逐块生成输出
    while len(okm) < length:
        # T(i) = HMAC-Hash(PRK, T(i-1) || info || i)
        t = hmac.new(prk, t + info + bytes([ctr]), hashlib.sha256).digest()
        okm += t
        ctr += 1

    # 截取所需长度
    return okm[:length]


# ==================== SEC1 公钥编码标准 ====================


def encode_point(P, compressed=True):
    """
    按照 SEC1 标准编码椭圆曲线点

    SEC1 是椭圆曲线公钥的标准编码格式：
    - 未压缩格式：0x04 || x || y（65字节）
    - 压缩格式：0x02/0x03 || x（33字节）
      * 0x02：y 为偶数
      * 0x03：y 为奇数

    压缩格式优势：
    - 节省 50% 的存储和传输开销
    - 可从 x 坐标和奇偶性恢复 y 坐标

    Args:
        P: 椭圆曲线上的点 (x, y)
        compressed: 是否使用压缩格式

    Returns:
        bytes: 编码后的公钥
    """
    if P is None:
        raise ValueError("Cannot encode infinity for SEC1 pubkey")

    x, y = P
    # 坐标转换为 32 字节大端序
    xb = x.to_bytes(32, "big")
    yb = y.to_bytes(32, "big")

    if not compressed:
        # 未压缩格式：0x04 + x + y
        return b"\x04" + xb + yb

    # 压缩格式：根据 y 的奇偶性选择前缀
    prefix = b"\x02" if (y % 2 == 0) else b"\x03"
    return prefix + xb


def legendre(a):
    """
    勒让德符号：判断 a 是否为模 p 的二次剩余

    对于奇素数 p：
    - legendre(a) = 1：a 是二次剩余（存在 x 使得 x² ≡ a (mod p)）
    - legendre(a) = -1：a 是二次非剩余
    - legendre(a) = 0：a ≡ 0 (mod p)

    计算公式：legendre(a) = a^((p-1)/2) mod p
    """
    return pow(a, (p - 1) // 2, p)


def mod_sqrt(a):
    """
    计算模 p 的平方根

    仅适用于 p ≡ 3 (mod 4) 的素数（P-256 满足此条件）
    算法：如果 a 是二次剩余，则 x = a^((p+1)/4) mod p 是其平方根

    Args:
        a: 需要开方的数

    Returns:
        模 p 的平方根，如果不存在则返回 None
    """
    if a % p == 0:
        return 0

    # 检查是否为二次剩余
    if legendre(a) != 1:
        return None  # 无平方根，说明点无效

    # 对于 p ≡ 3 (mod 4)，可直接计算
    return pow(a, (p + 1) // 4, p)


def decode_point(data: bytes):
    """
    解码 SEC1 格式的公钥

    支持两种格式：
    - 未压缩：65 字节，以 0x04 开头
    - 压缩：33 字节，以 0x02 或 0x03 开头

    Args:
        data: SEC1 编码的公钥数据

    Returns:
        椭圆曲线上的点 (x, y)

    Raises:
        ValueError: 编码格式无效或点不在曲线上
    """
    if len(data) == 65 and data[0] == 0x04:
        # 未压缩格式：直接提取坐标
        x = int.from_bytes(data[1:33], "big")
        y = int.from_bytes(data[33:65], "big")
        P = (x, y)

        # 验证点的有效性
        assert is_on_curve(P) and P is not O
        return P

    elif len(data) == 33 and data[0] in (0x02, 0x03):
        # 压缩格式：需要从 x 坐标恢复 y 坐标
        x = int.from_bytes(data[1:33], "big")

        # 根据曲线方程计算 y²：y² = x³ + ax + b (mod p)
        rhs = (pow(x, 3, p) + (a * x) + b) % p

        # 计算平方根
        y = mod_sqrt(rhs)
        if y is None:
            raise ValueError("Invalid compressed point")

        # 根据前缀选择正确的 y 值
        # 0x02 表示 y 为偶数，0x03 表示 y 为奇数
        if (y % 2) != (data[0] & 1):
            y = (-y) % p  # 选择另一个平方根

        P = (x, y)

        # 验证点的有效性
        assert is_on_curve(P) and P is not O
        return P

    else:
        raise ValueError("Invalid SEC1 point encoding")
