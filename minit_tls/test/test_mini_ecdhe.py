"""
Test suite for mini_ecdhe module

This module contains comprehensive tests for the ECDHE implementation,
including unit tests, integration tests, and property-based tests.
"""

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False


    # Mock pytest decorators when pytest is not available
    class MockPytest:
        class mark:
            @staticmethod
            def unit(func):
                return func

            @staticmethod
            def integration(func):
                return func

        @staticmethod
        def raises(exception):
            class RaisesContext:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    return exc_type is not None and issubclass(exc_type, exception)

            return RaisesContext()

        @staticmethod
        def main(args):
            print(f"Pytest not available, running tests manually...")
            # Run tests manually
            import sys
            module = sys.modules[__name__]
            test_functions = [getattr(module, name) for name in dir(module)
                              if name.startswith('test_') and callable(getattr(module, name))]

            passed = 0
            failed = 0
            for test_func in test_functions:
                try:
                    print(f"Running {test_func.__name__}...")
                    test_func()
                    print(f"✅ {test_func.__name__} passed")
                    passed += 1
                except Exception as e:
                    print(f"❌ {test_func.__name__} failed: {e}")
                    failed += 1

            print(f"\nTest summary: {passed} passed, {failed} failed")
            return 0 if failed == 0 else 1


    pytest = MockPytest()

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minit_tls.network.mini_ecdhe import (
    # Key generation and ECDHE
    gen_keypair,
    ecdhe_shared,
    hkdf_sha256,

    # Point operations
    point_add,
    point_double,
    scalar_mult,
    negate,
    is_on_curve,

    # Encoding/decoding
    encode_point,
    decode_point,

    # Constants and utilities
    G,
    n,
    p,
    a,
    b,
    O,
)


# ==================== 测试和验证代码 ====================


@pytest.mark.unit
def test_fixed_case():
    """
    固定测试用例：验证 ECDHE 的正确性

    使用简单的私钥（1 和 2）进行测试，便于手工验证：
    - Alice 私钥 = 1，公钥 = 1×G = G
    - Bob 私钥 = 2，公钥 = 2×G
    - 共享密钥 = 1×(2×G) = 2×(1×G) = 2×G 的 x 坐标
    """
    print("🧪 执行固定测试用例...")

    a_sk = 1  # Alice 的私钥
    b_sk = 2  # Bob 的私钥

    # 计算公钥
    A = scalar_mult(a_sk, G)  # Alice 的公钥 = 1×G = G
    B = scalar_mult(b_sk, G)  # Bob 的公钥 = 2×G

    # 双方计算共享密钥的 x 坐标
    x1 = scalar_mult(a_sk, B)[0]  # Alice 计算：1 × (2×G) = 2×G
    x2 = scalar_mult(b_sk, A)[0]  # Bob 计算：2 × (1×G) = 2×G
    x2G = scalar_mult(2, G)[0]  # 直接计算 2×G 用于验证

    print(f"   Alice 共享密钥 x 坐标: {hex(x1)}")
    print(f"   Bob 共享密钥 x 坐标: {hex(x2)}")
    print(f"   2×G 的 x 坐标: {hex(x2G)}")
    print(f"   三者是否相等: {x1 == x2 == x2G}")

    assert x1 == x2 == x2G, "固定测试用例失败！"
    print("✅ 固定测试用例通过")


@pytest.mark.integration
def test_run_comprehensive():
    """运行全面的测试套件"""
    print("🚀 开始椭圆曲线密码学综合测试")
    print("=" * 60)

    # 1. 基础数学属性测试
    print("\n📐 测试基础数学属性...")
    assert is_on_curve(G), "基点不在曲线上！"
    assert is_on_curve(point_double(G)), "2G 不在曲线上！"
    assert point_add(G, O) == G and point_add(O, G) == G, "单位元性质失败！"
    assert point_add(G, negate(G)) is O, "逆元性质失败！"
    assert scalar_mult(n, G) is O, "基点阶验证失败！"
    print("✅ 基础数学属性测试通过")

    # 2. 固定测试用例
    test_fixed_case()

    # 3. 随机密钥对测试
    print("\n🔐 测试随机密钥对生成和 ECDHE...")
    a_sk, a_pk = gen_keypair()
    b_sk, b_pk = gen_keypair()

    # 交换公钥，计算共享秘密
    a_shared = ecdhe_shared(a_sk, b_pk)
    b_shared = ecdhe_shared(b_sk, a_pk)
    assert a_shared == b_shared, "ECDHE 共享密钥不匹配！"

    # 用 HKDF 派生会话密钥
    session_key = hkdf_sha256(a_shared, salt=b"", info=b"demo-ecdhe", length=32)

    print(f"   共享密钥 X 坐标: {a_shared.hex()}")
    print(f"   派生的会话密钥: {session_key.hex()}")
    print("✅ ECDHE 和密钥派生测试通过")

    # 4. SEC1 编码解码测试
    print("\n📦 测试 SEC1 公钥编码/解码...")

    # 测试压缩格式
    enc_compressed = encode_point(G, compressed=True)
    dec_compressed = decode_point(enc_compressed)
    assert dec_compressed == G, "压缩格式编码/解码失败！"

    # 测试未压缩格式
    enc_uncompressed = encode_point(G, compressed=False)
    dec_uncompressed = decode_point(enc_uncompressed)
    assert dec_uncompressed == G, "未压缩格式编码/解码失败！"

    print(f"   压缩公钥长度: {len(enc_compressed)} 字节")
    print(f"   未压缩公钥长度: {len(enc_uncompressed)} 字节")
    print("✅ SEC1 编码/解码测试通过")

    # 5. 端到端互操作测试
    print("\n🌐 测试端到端互操作...")
    a_sk, a_pk = gen_keypair()
    b_sk, b_pk = gen_keypair()

    # 模拟网络传输：编码公钥
    a_pk_wire = encode_point(a_pk, compressed=True)  # 压缩传输
    b_pk_wire = encode_point(b_pk, compressed=False)  # 未压缩传输

    # 接收方解码公钥并计算共享密钥
    a_shared = ecdhe_shared(a_sk, decode_point(b_pk_wire))
    b_shared = ecdhe_shared(b_sk, decode_point(a_pk_wire))

    print(f"   Alice 共享密钥: {a_shared.hex()}")
    print(f"   Bob 共享密钥: {b_shared.hex()}")
    print(f"   传输后密钥是否匹配: {a_shared == b_shared}")
    assert a_shared == b_shared, "传输后共享密钥不匹配！"
    print("✅ 端到端互操作测试通过")

    print(f"\n🎉 所有测试通过！ECDHE 实现正确且安全。")
    print("=" * 60)


# ==================== 单独的单元测试 ====================


@pytest.mark.unit
def test_curve_parameters():
    """测试椭圆曲线参数的正确性"""
    # 验证基点在曲线上
    assert is_on_curve(G), "基点不在曲线上"

    # 验证基点的阶
    assert scalar_mult(n, G) is O, "基点阶验证失败"

    # 验证曲线参数
    x, y = G
    assert (y * y - (x * x * x + a * x + b)) % p == 0, "基点不满足曲线方程"


@pytest.mark.unit
def test_point_operations():
    """测试椭圆曲线点运算的基本性质"""
    # 单位元性质
    assert point_add(G, O) == G, "P + O != P"
    assert point_add(O, G) == G, "O + P != P"

    # 逆元性质
    neg_G = negate(G)
    assert point_add(G, neg_G) is O, "P + (-P) != O"

    # 结合律 (P + Q) + R = P + (Q + R)
    P = scalar_mult(2, G)
    Q = scalar_mult(3, G)
    R = scalar_mult(5, G)

    left = point_add(point_add(P, Q), R)
    right = point_add(P, point_add(Q, R))
    assert left == right, "结合律失败"

    # 交换律 P + Q = Q + P
    assert point_add(P, Q) == point_add(Q, P), "交换律失败"


@pytest.mark.unit
def test_scalar_multiplication():
    """测试标量乘法的性质"""
    # 分配律: k(P + Q) = kP + kQ
    k = 7
    P = scalar_mult(2, G)
    Q = scalar_mult(3, G)

    left = scalar_mult(k, point_add(P, Q))
    right = point_add(scalar_mult(k, P), scalar_mult(k, Q))
    assert left == right, "标量乘法分配律失败"

    # 结合律: (k1 * k2) * P = k1 * (k2 * P)
    k1, k2 = 7, 11
    left = scalar_mult((k1 * k2) % n, G)
    right = scalar_mult(k1, scalar_mult(k2, G))
    assert left == right, "标量乘法结合律失败"


@pytest.mark.unit
def test_key_generation():
    """测试密钥生成"""
    for _ in range(10):  # 测试多次生成
        sk, pk = gen_keypair()

        # 私钥范围检查
        assert 1 <= sk < n, f"私钥超出范围: {sk}"

        # 公钥验证
        assert is_on_curve(pk), "生成的公钥不在曲线上"
        assert pk is not O, "公钥不能是无穷远点"

        # 验证公钥是私钥的标量乘法结果
        expected_pk = scalar_mult(sk, G)
        assert pk == expected_pk, "公钥与私钥不匹配"


@pytest.mark.unit
def test_sec1_encoding():
    """测试 SEC1 编码/解码"""
    # 测试多个随机点
    for _ in range(5):
        _, pk = gen_keypair()

        # 测试压缩格式
        compressed = encode_point(pk, compressed=True)
        assert len(compressed) == 33, f"压缩格式长度错误: {len(compressed)}"
        assert compressed[0] in (0x02, 0x03), f"压缩格式前缀错误: {compressed[0]}"

        decoded_compressed = decode_point(compressed)
        assert decoded_compressed == pk, "压缩格式解码失败"

        # 测试未压缩格式
        uncompressed = encode_point(pk, compressed=False)
        assert len(uncompressed) == 65, f"未压缩格式长度错误: {len(uncompressed)}"
        assert uncompressed[0] == 0x04, f"未压缩格式前缀错误: {uncompressed[0]}"

        decoded_uncompressed = decode_point(uncompressed)
        assert decoded_uncompressed == pk, "未压缩格式解码失败"


@pytest.mark.unit
def test_hkdf():
    """测试 HKDF 密钥派生函数"""
    ikm = b"input key material"
    salt = b"optional salt"
    info = b"application info"

    # 基本功能测试
    key1 = hkdf_sha256(ikm, salt, info, 32)
    assert len(key1) == 32, "HKDF 输出长度错误"

    # 确定性测试
    key2 = hkdf_sha256(ikm, salt, info, 32)
    assert key1 == key2, "HKDF 不是确定性的"

    # 不同输入产生不同输出
    key3 = hkdf_sha256(ikm + b"x", salt, info, 32)
    assert key1 != key3, "不同输入产生相同输出"

    # 不同长度测试
    key4 = hkdf_sha256(ikm, salt, info, 16)
    assert len(key4) == 16, "HKDF 输出长度错误"
    # HKDF 的特性：相同参数下，短输出应该等于长输出的前缀
    assert key4 == key1[:16], "HKDF 长度一致性检查失败"

    # 不同 info 参数产生不同输出
    key5 = hkdf_sha256(ikm, salt, b"different info", 16)
    assert key5 != key4, "不同 info 参数应产生不同输出"


@pytest.mark.unit
def test_ecdhe_basic():
    """测试基本的 ECDHE 功能"""
    # 生成两对密钥
    alice_sk, alice_pk = gen_keypair()
    bob_sk, bob_pk = gen_keypair()

    # 执行密钥交换
    alice_shared = ecdhe_shared(alice_sk, bob_pk)
    bob_shared = ecdhe_shared(bob_sk, alice_pk)

    # 验证共享密钥相等
    assert alice_shared == bob_shared, "ECDHE 共享密钥不匹配"

    # 验证输出格式
    assert len(alice_shared) == 32, "共享密钥长度错误"
    assert isinstance(alice_shared, bytes), "共享密钥类型错误"


@pytest.mark.unit
def test_invalid_inputs():
    """测试无效输入的处理"""
    # 测试无效点解码
    with pytest.raises(ValueError):
        decode_point(b"invalid")

    with pytest.raises(ValueError):
        decode_point(b"\x05" + b"\x00" * 32)  # 无效前缀

    # 测试无穷远点编码
    with pytest.raises(ValueError):
        encode_point(O)


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v"])
