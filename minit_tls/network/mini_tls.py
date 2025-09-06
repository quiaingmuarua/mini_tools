import os
import struct
import socket
import ssl

def create_client_hello(hostname):
    # TLS 记录层头部：握手协议（0x16），版本 TLS 1.0（0x0301）
    record_header = b'\x16'  # Content Type: Handshake
    record_version = b'\x03\x01'  # Record Layer Version (TLS 1.0 for backward compat)

    # ClientHello 消息体（我们先构造，再计算长度）
    handshake_type = b'\x01'  # 1 = ClientHello
    # 随机数：32 字节
    import time
    gmt_unix_time = int(time.time())
    random_bytes = struct.pack('!I', gmt_unix_time) + bytes([0x42] * 28)  # 简化随机数

    session_id = b'\x00'  # 空会话 ID
    cipher_suites = b'\xC0\x2F\x00\x35'  # 支持 ECDHE-RSA-AES128-GCM-SHA256, TLS_RSA_WITH_AES128_CBC_SHA
    compression_methods = b'\x01\x00'  # null compression

    # 扩展：SNI（Server Name Indication）
    sni_name = hostname.encode('utf-8')
    sni_ext = (
            b'\x00\x00' +  # Extension type: server_name (0)
            struct.pack('!H', len(sni_name) + 3) +  # Extension length
            struct.pack('!H', len(sni_name) + 1) +  # List length
            b'\x00' +  # Name type: host_name (0)
            struct.pack('!H', len(sni_name)) +  # Name length
            sni_name
    )

    # 其他扩展（可选）：支持的群组（ECDHE 曲线）
    ec_points_format_ext = b'\x00\x0b\x00\x02\x01\x00'  # ec_point_formats: uncompressed
    supported_groups_ext = b'\x00\x0a\x00\x0a\x00\x08\x00\x1d\x00\x17\x00\x18'  # secp256r1, etc.

    extensions = sni_ext + ec_points_format_ext + supported_groups_ext

    # 计算 ClientHello 消息体长度
    client_hello_body = (
            b'\x03\x03' +  # 版本：TLS 1.2
            random_bytes +
            session_id +
            struct.pack('!H', len(cipher_suites)) + cipher_suites +
            compression_methods +
            struct.pack('!H', len(extensions)) + extensions
    )

    handshake_length = len(client_hello_body)
    handshake_header = struct.pack('!I', (handshake_type[0] << 24) + handshake_length)[1:]

    # 完整的握手消息
    message = handshake_header + client_hello_body

    # 记录层总长度
    record_length = len(message)
    record = record_header + record_version + struct.pack('!H', record_length) + message

    return record


if __name__ == '__main__':
    hostname = 'example.com'
    port = 443

    # 1. 创建 TCP 连接
    sock = socket.create_connection((hostname, port))

    # 2. 构造并发送 ClientHello
    client_hello = create_client_hello(hostname)
    sock.send(client_hello)

    # 3. 现在，我们让 ssl 模块“接管”这个 socket，继续完成握手
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_REQUIRED

    # ⚠️ 关键：我们已经发了 ClientHello，但 ssl 模块会继续处理后续握手
    # 它会接收 ServerHello、证书、ServerKeyExchange、Finished 等
    ssock = context.wrap_socket(sock, server_hostname=hostname)

    # ✅ 握手成功！现在可以发送 HTTP 请求
    request = f"GET /get HTTP/1.1\r\nHost: {hostname}\r\nConnection: close\r\n\r\n"
    ssock.send(request.encode('utf-8'))

    # 接收响应
    response = b""
    while True:
        data = ssock.recv(4096)
        if not data:
            break
        response += data

    print(response.decode('utf-8', errors='ignore'))

    ssock.close()