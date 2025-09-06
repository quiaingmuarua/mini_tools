#!/usr/bin/env python3
"""
ECDHE 演示程序

展示如何使用 mini_tool 进行椭圆曲线 Diffie-Hellman 密钥交换
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_tool.minit_tls.network.mini_ecdhe import (
    decode_point,
    ecdhe_shared,
    encode_point,
    gen_keypair,
    hkdf_sha256,
)


def main():
    """ECDHE 密钥交换演示"""
    print("🔐 ECDHE 密钥交换演示")
    print("=" * 50)

    # 1. 生成 Alice 和 Bob 的密钥对
    print("\n📱 生成密钥对...")
    alice_sk, alice_pk = gen_keypair()
    bob_sk, bob_pk = gen_keypair()

    print(f"Alice 私钥: {alice_sk:064x}")
    print(f"Bob 私钥: {bob_sk:064x}")

    # 2. 编码公钥用于传输
    print("\n📡 编码公钥用于传输...")
    alice_pk_bytes = encode_point(alice_pk, compressed=True)
    bob_pk_bytes = encode_point(bob_pk, compressed=True)

    print(f"Alice 公钥 (压缩): {alice_pk_bytes.hex()}")
    print(f"Bob 公钥 (压缩): {bob_pk_bytes.hex()}")

    # 3. 模拟网络传输：解码公钥
    print("\n🌐 模拟网络传输...")
    alice_pk_received = decode_point(alice_pk_bytes)
    bob_pk_received = decode_point(bob_pk_bytes)

    # 4. 计算共享密钥
    print("\n🔑 计算共享密钥...")
    alice_shared = ecdhe_shared(alice_sk, bob_pk_received)
    bob_shared = ecdhe_shared(bob_sk, alice_pk_received)

    print(f"Alice 计算的共享密钥: {alice_shared.hex()}")
    print(f"Bob 计算的共享密钥: {bob_shared.hex()}")
    print(f"共享密钥是否匹配: {alice_shared == bob_shared}")

    # 5. 使用 HKDF 派生会话密钥
    print("\n🎯 派生会话密钥...")
    session_key = hkdf_sha256(
        ikm=alice_shared, salt=b"demo-salt", info=b"ecdhe-demo-session-key", length=32
    )

    print(f"会话密钥: {session_key.hex()}")

    # 6. 派生多个密钥
    print("\n🔐 派生多个专用密钥...")
    encrypt_key = hkdf_sha256(alice_shared, b"", b"encrypt", 32)
    mac_key = hkdf_sha256(alice_shared, b"", b"mac", 32)
    iv = hkdf_sha256(alice_shared, b"", b"iv", 16)

    print(f"加密密钥: {encrypt_key.hex()}")
    print(f"MAC 密钥: {mac_key.hex()}")
    print(f"初始向量: {iv.hex()}")

    print("\n✅ ECDHE 密钥交换完成！")


def size_comparison():
    """比较不同公钥编码格式的大小"""
    print("\n📏 公钥编码格式比较")
    print("=" * 30)

    _, pk = gen_keypair()

    # 压缩格式
    compressed = encode_point(pk, compressed=True)
    # 未压缩格式
    uncompressed = encode_point(pk, compressed=False)

    print(f"压缩格式: {len(compressed)} 字节")
    print(f"未压缩格式: {len(uncompressed)} 字节")
    print(f"压缩比: {len(compressed) / len(uncompressed):.1%}")
    print(f"节省空间: {len(uncompressed) - len(compressed)} 字节")


def security_demo():
    """安全性演示"""
    print("\n🛡️ 安全性演示")
    print("=" * 20)

    # 1. 不同密钥对产生不同共享密钥
    alice_sk1, alice_pk1 = gen_keypair()
    alice_sk2, alice_pk2 = gen_keypair()
    bob_sk, bob_pk = gen_keypair()

    shared1 = ecdhe_shared(alice_sk1, bob_pk)
    shared2 = ecdhe_shared(alice_sk2, bob_pk)

    print(f"不同私钥产生不同共享密钥: {shared1 != shared2}")

    # 2. 共享密钥熵验证
    shared_keys = set()
    for _ in range(100):
        sk1, pk1 = gen_keypair()
        sk2, pk2 = gen_keypair()
        shared = ecdhe_shared(sk1, pk2)
        shared_keys.add(shared)

    print(f"100次密钥交换产生 {len(shared_keys)} 个不同共享密钥")
    print(f"熵表现: {'良好' if len(shared_keys) > 95 else '需要检查'}")


if __name__ == "__main__":
    main()
    size_comparison()
    security_demo()
