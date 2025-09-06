from math import sin


def to_bytes(text:str):
    return text.encode('utf-8')


def md5_padding(message_bytes:bytes):
    original_len = len(message_bytes)
    message_bytes +=b'\x80'
    message_len = len(message_bytes)
    padding_len= 64-(8+message_len)%64
    if padding_len!=64:
        message_bytes +=b'\x00'*padding_len
    message_bytes+=(8*original_len).to_bytes(8,'little')
    return message_bytes


def group_64_bytes(message_bytes:bytes)->list:
    group_bytes=[]
    for i in range(0,len(message_bytes),64):
        group_bytes.append(message_bytes[i:i+64])
    return group_bytes

def md5_init():
    A = 0x67452301
    B = 0xefcdab89
    C = 0x98badcfe
    D = 0x10325476
    return A, B, C, D


def md5_block(block, A, B, C, D):
    AA, BB, CC, DD = A, B, C, D
    # 1. 把64字节分成16个32位
    X = [int.from_bytes(block[i:i+4], 'little') for i in range(0, 64, 4)]
    for i in range(64):
        if 0 <= i < 16:
            f = F(B, C, D)
            g = i
        elif 16 <= i < 32:
            f = G(B, C, D)
            g = (5 * i + 1) % 16
        elif 32 <= i < 48:
            f = H(B, C, D)
            g = (3 * i + 5) % 16
        else:
            f = I(B, C, D)
            g = (7 * i) % 16
        temp = (A + f + K[i] + X[g]) & 0xffffffff
        temp = left_rotate(temp, s[i])
        A, B, C, D = D, (B + temp) & 0xffffffff, B, C

    A = (A + AA) & 0xffffffff
    B = (B + BB) & 0xffffffff
    C = (C + CC) & 0xffffffff
    D = (D + DD) & 0xffffffff
    # 3. 返回新A, B, C, D
    return A, B, C, D

def F(B, C, D):
    return (B & C) | (~B & D)


def G(B,C,D):
    return (B & D) | (C & ~D)


def H(B,C,D):
    return B ^ C ^ D


def I(B,C,D):
    return C ^ (B | ~D)



K = [int((2**32) * abs(sin(i + 1))) & 0xffffffff for i in range(64)]
s = [
    7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,  7, 12, 17, 22,
    5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,  5,  9, 14, 20,
    4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,  4, 11, 16, 23,
    6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,  6, 10, 15, 21,
]




def left_rotate(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xffffffff



def md5_output(A, B, C, D):
    # 按照小端序拼接，和 hashlib 输出一致
    return (A.to_bytes(4, 'little') +
            B.to_bytes(4, 'little') +
            C.to_bytes(4, 'little') +
            D.to_bytes(4, 'little'))




def md5_text(text: str):
    # 1. 消息填充
    message_bytes = to_bytes(text)
    padding_bytes = md5_padding(message_bytes)
    # 2. 分块
    blocks = group_64_bytes(padding_bytes)
    # 3. 初始化寄存器
    A, B, C, D = md5_init()
    # 4. 分块处理（主循环）
    for block in blocks:
        A, B, C, D = md5_block(block, A, B, C, D)
    # 5. 拼接输出
    digest = md5_output(A, B, C, D)
    return digest


if __name__ == '__main__':
    text = "hello_world"
    message_bytes = to_bytes(text)
    padding_bytes = md5_padding(message_bytes)
    print(f"未加密str {padding_bytes.hex()}")
    blocks = group_64_bytes(padding_bytes)
    A, B, C, D = md5_init()
    for block in blocks:
        A, B, C, D = md5_block(block, A, B, C, D)

    digest = md5_output(A, B, C, D)
    print(digest.hex())
    #99b1ff8f11781541f7f89f9bd41c4a17


