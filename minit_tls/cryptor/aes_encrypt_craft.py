# aes128_encrypt_block.py
# Minimal AES-128 single-block encrypt (FIPS-197 example), column-major state layout.

import pandas as pd

# ---------- S-Box ----------
S_BOX = [
    [0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76],
    [0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0],
    [0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15],
    [0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75],
    [0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84],
    [0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf],
    [0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8],
    [0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2],
    [0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73],
    [0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb],
    [0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79],
    [0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08],
    [0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a],
    [0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e],
    [0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf],
    [0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16]
]


# ---------- Utilities ----------
def to_hex_df(df_int: pd.DataFrame) -> pd.DataFrame:
    return df_int.applymap(lambda x: format(x, '02x'))


def from_hex_df(hex_matrix) -> pd.DataFrame:
    return pd.DataFrame(hex_matrix).applymap(lambda x: int(x, 16))


def add_round_key(hex_state: pd.DataFrame, hex_key: pd.DataFrame) -> pd.DataFrame:
    return to_hex_df(from_hex_df(hex_state) ^ from_hex_df(hex_key))


def sbox_lookup(byte_value: int) -> int:
    return S_BOX[byte_value >> 4][byte_value & 0x0F]


def substitute_hex_string(hex_str: str) -> str:
    return format(sbox_lookup(int(hex_str, 16)), '02x')


def sub_bytes_hex_df(hex_df: pd.DataFrame) -> pd.DataFrame:
    return hex_df.applymap(lambda x: substitute_hex_string(x))


def shift_rows_hex_df(hex_df: pd.DataFrame) -> pd.DataFrame:
    out = hex_df.copy()
    for r in range(1, 4):
        row_vals = list(out.iloc[r])
        out.iloc[r] = row_vals[r:] + row_vals[:r]
    return out


# ---------- GF(2^8) ----------
def gmul(a, b):
    res = 0
    for _ in range(8):
        if b & 1:
            res ^= a
        carry = a & 0x80
        a = (a << 1) & 0xFF
        if carry:
            a ^= 0x1b
        b >>= 1
    return res


def mix_single_column(col):
    a0, a1, a2, a3 = col
    return [
        gmul(a0, 2) ^ gmul(a1, 3) ^ gmul(a2, 1) ^ gmul(a3, 1),
        gmul(a0, 1) ^ gmul(a1, 2) ^ gmul(a2, 3) ^ gmul(a3, 1),
        gmul(a0, 1) ^ gmul(a1, 1) ^ gmul(a2, 2) ^ gmul(a3, 3),
        gmul(a0, 3) ^ gmul(a1, 1) ^ gmul(a2, 1) ^ gmul(a3, 2),
    ]


def mix_columns_hex_df(hex_df: pd.DataFrame) -> pd.DataFrame:
    int_df = hex_df.applymap(lambda x: int(x, 16))
    out = int_df.copy()
    for c in range(4):
        col_vals = list(int_df.iloc[:, c])
        mixed = mix_single_column(col_vals)
        for r in range(4):
            out.iat[r, c] = mixed[r]
    return to_hex_df(out)


# ---------- Key expansion (AES-128) ----------
RCON = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]


def sub_word(w): return [sbox_lookup(b) for b in w]


def rot_word(w): return w[1:] + w[:1]


def key_expansion_128(hex_key_matrix):
    key_bytes = []
    df = from_hex_df(hex_key_matrix)
    # collect bytes column-major
    for c in range(4):
        for r in range(4):
            key_bytes.append(int(df.iat[r, c]))
    words = [key_bytes[i * 4:(i + 1) * 4] for i in range(4)]
    for i in range(4, 44):
        temp = words[i - 1].copy()
        if i % 4 == 0:
            temp = sub_word(rot_word(temp))
            temp[0] ^= RCON[i // 4]
        words.append([(words[i - 4][j] ^ temp[j]) & 0xFF for j in range(4)])
    # 11 round keys in state layout (column-major)
    round_keys = []
    for rki in range(11):
        wblock = words[rki * 4:(rki + 1) * 4]  # 4 words
        key_state = [[wblock[c][r] for c in range(4)] for r in range(4)]
        round_keys.append(pd.DataFrame(key_state).applymap(lambda x: format(x, '02x')))
    return round_keys


# ---------- Encrypt one 16-byte block ----------
def encrypt_block(hex_plain_state, hex_key_state):
    # 扩展密钥
    rkeys = key_expansion_128(hex_key_state)
    # round0 AddRoundKey
    state = add_round_key(pd.DataFrame(hex_plain_state), rkeys[0])  # Round 0
    for r in range(1, 10):  # Rounds 1..9
        # SubBytes
        state = sub_bytes_hex_df(state)
        state = shift_rows_hex_df(state)
        state = mix_columns_hex_df(state)
        state = add_round_key(state, rkeys[r])
    # Final round (10): no MixColumns
    state = sub_bytes_hex_df(state)
    state = shift_rows_hex_df(state)
    state = add_round_key(state, rkeys[10])
    return state


# ---------- Demo (FIPS-197 example) ----------
if __name__ == "__main__":
    plaintext = [
        ['32', '88', '31', 'e0'],
        ['43', '5a', '31', '37'],
        ['f6', '30', '98', '07'],
        ['a8', '8d', 'a2', '34']
    ]
    matrix_key = [
        ['2b', '28', 'ab', '09'],
        ['7e', 'ae', 'f7', 'cf'],
        ['15', 'd2', '15', '4f'],
        ['16', 'a6', '88', '3c']
    ]

    final = encrypt_block(plaintext, matrix_key)
    # read out ciphertext in column-major order
    out = []
    for c in range(4):
        for r in range(4):
            out.append(final.iat[r, c])
    cipher_hex = ' '.join(out)
    print("Ciphertext:", cipher_hex)
    # Expected: 39 25 84 1d 02 dc 09 fb dc 11 85 97 19 6a 0b 32
