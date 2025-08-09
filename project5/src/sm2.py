# sm2.py
# 基于椭圆曲线的SM2基础实现（密钥生成、加密、解密、签名、验签）
# 依赖: ecdsa (pip install ecdsa)

from ecdsa import SigningKey, VerifyingKey, NIST256p
from hashlib import sha256
import os

class SM2:
    def __init__(self):
        self.curve = NIST256p  # SM2推荐曲线参数类似secp256r1/NIST256p

    def generate_keypair(self):
        sk = SigningKey.generate(curve=self.curve)
        vk = sk.verifying_key
        return sk, vk

    def encrypt(self, vk: VerifyingKey, plaintext: bytes) -> bytes:
        # 简化版：用ECC密钥做ECDH派生对称密钥，然后AES加密（实际SM2有C1C3C2结构）
        # 这里只做演示
        shared = vk.to_string()[:16]  # 取前16字节做对称密钥（不安全，仅演示）
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        iv = os.urandom(16)
        cipher = AES.new(shared, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(pad(plaintext, 16))
        return iv + ciphertext

    def decrypt(self, sk: SigningKey, ciphertext: bytes) -> bytes:
        shared = sk.verifying_key.to_string()[:16]
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        iv = ciphertext[:16]
        ct = ciphertext[16:]
        cipher = AES.new(shared, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), 16)

    def sign(self, sk: SigningKey, data: bytes) -> bytes:
        return sk.sign(data, hashfunc=sha256)

    def verify(self, vk: VerifyingKey, data: bytes, signature: bytes) -> bool:
        try:
            return vk.verify(signature, data, hashfunc=sha256)
        except Exception:
            return False

if __name__ == "__main__":
    sm2 = SM2()
    sk, vk = sm2.generate_keypair()
    msg = b"Hello, SM2!"
    print("原文:", msg)
    ct = sm2.encrypt(vk, msg)
    print("密文:", ct.hex())
    pt = sm2.decrypt(sk, ct)
    print("解密:", pt)
    sig = sm2.sign(sk, msg)
    print("签名:", sig.hex())
    print("验签:", sm2.verify(vk, msg, sig))
