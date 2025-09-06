class SHA256Craft:
    def __init__(self):
        # 初始化 register magic number
        self.H = [
            0x6A09E667,
            0xBB67AE85,
            0x3C6EF372,
            0xA54FF53A,
            0x510E527F,
            0x9B05688C,
            0x1F83D9AB,
            0x5BE0CD19,
        ]
        # init K常量表
        self.K = [
            0x428A2F98,
            0x71374491,
            0xB5C0FBCF,
            0xE9B5DBA5,
            0x3956C25B,
            0x59F111F1,
            0x923F82A4,
            0xAB1C5ED5,
            0xD807AA98,
            0x12835B01,
            0x243185BE,
            0x550C7DC3,
            0x72BE5D74,
            0x80DEB1FE,
            0x9BDC06A7,
            0xC19BF174,
            0xE49B69C1,
            0xEFBE4786,
            0x0FC19DC6,
            0x240CA1CC,
            0x2DE92C6F,
            0x4A7484AA,
            0x5CB0A9DC,
            0x76F988DA,
            0x983E5152,
            0xA831C66D,
            0xB00327C8,
            0xBF597FC7,
            0xC6E00BF3,
            0xD5A79147,
            0x06CA6351,
            0x14292967,
            0x27B70A85,
            0x2E1B2138,
            0x4D2C6DFC,
            0x53380D13,
            0x650A7354,
            0x766A0ABB,
            0x81C2C92E,
            0x92722C85,
            0xA2BFE8A1,
            0xA81A664B,
            0xC24B8B70,
            0xC76C51A3,
            0xD192E819,
            0xD6990624,
            0xF40E3585,
            0x106AA070,
            0x19A4C116,
            0x1E376C08,
            0x2748774C,
            0x34B0BCB5,
            0x391C0CB3,
            0x4ED8AA4A,
            0x5B9CCA4F,
            0x682E6FF3,
            0x748F82EE,
            0x78A5636F,
            0x84C87814,
            0x8CC70208,
            0x90BEFFFA,
            0xA4506CEB,
            0xBEF9A3F7,
            0xC67178F2,
        ]

    def encrypt(self, text: str):
        message_bytes = self.to_bytes(text)
        padding_bytes = self.padding_bytes(message_bytes)
        blocks = self.group_64_bytes(padding_bytes)
        for block in blocks:
            self.encrypt_block(block)
        return self.output()

    def encrypt_block(self, block):
        W = [int.from_bytes(block[i : i + 4], "big") for i in range(0, 64, 4)]
        for i in range(16, 64):
            s0 = (
                self.right_rotate(W[i - 15], 7)
                ^ self.right_rotate(W[i - 15], 18)
                ^ (W[i - 15] >> 3)
            )
            s1 = (
                self.right_rotate(W[i - 2], 17)
                ^ self.right_rotate(W[i - 2], 19)
                ^ (W[i - 2] >> 10)
            )
            W.append((W[i - 16] + s0 + W[i - 7] + s1) & 0xFFFFFFFF)
        a, b, c, d, e, f, g, h = self.H
        for i in range(64):
            S1 = (
                self.right_rotate(e, 6)
                ^ self.right_rotate(e, 11)
                ^ self.right_rotate(e, 25)
            )
            ch = (e & f) ^ (~e & g)
            temp1 = (h + S1 + ch + self.K[i] + W[i]) & 0xFFFFFFFF
            S0 = (
                self.right_rotate(a, 2)
                ^ self.right_rotate(a, 13)
                ^ self.right_rotate(a, 22)
            )
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (S0 + maj) & 0xFFFFFFFF
            h = g
            g = f
            f = e
            e = (d + temp1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xFFFFFFFF

        self.H = [
            (x + y) & 0xFFFFFFFF for x, y in zip(self.H, [a, b, c, d, e, f, g, h])
        ]

    def output(self):
        a, b, c, d, e, f, g, h = self.H
        return (
            a.to_bytes(4, "big")
            + b.to_bytes(4, "big")
            + c.to_bytes(4, "big")
            + d.to_bytes(4, "big")
            + e.to_bytes(4, "big")
            + f.to_bytes(4, "big")
            + g.to_bytes(4, "big")
            + h.to_bytes(4, "big")
        )

    @staticmethod
    def to_bytes(text):
        return text.encode("utf-8")

    @staticmethod
    def padding_bytes(message_bytes: bytes):
        original_len = len(message_bytes)
        message_bytes += b"\x80"
        padding_len = 64 - (8 + len(message_bytes)) % 64
        if padding_len != 64:
            message_bytes += b"\x00" * padding_len
        message_bytes += (8 * original_len).to_bytes(8, "big")
        return message_bytes

    @staticmethod
    def group_64_bytes(message_bytes: bytes) -> list:
        group_bytes = []
        for i in range(0, len(message_bytes), 64):
            group_bytes.append(message_bytes[i : i + 64])
        return group_bytes

    @staticmethod
    def right_rotate(x, n):
        return ((x << (32 - n)) | (x >> n)) & 0xFFFFFFFF


if __name__ == "__main__":
    sha256_craft = SHA256Craft()
    text = "hello_world"
    print(sha256_craft.encrypt(text).hex())
    # 35072c1ae546350e0bfa7ab11d49dc6f129e72ccd57ec7eb671225bbd197c8f1
