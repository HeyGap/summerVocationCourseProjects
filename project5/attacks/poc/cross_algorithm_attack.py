#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨算法重用密钥和随机数攻击 PoC
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import hashlib
import random
from ecdsa import NIST256p, SigningKey, util
from ecdsa.ellipticcurve import Point
from Crypto.Util.number import inverse
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

class CrossAlgorithmAttack:
    def __init__(self):
        self.curve = NIST256p
        self.generator = self.curve.generator
        self.order = self.curve.order
        
    def _hash_message(self, message):
        """计算消息哈希"""
        return hashlib.sha256(message.encode('utf-8')).digest()
    
    def _mod_inverse(self, a, m):
        """计算模逆"""
        return inverse(a, m)
    
    def generate_keypair(self):
        """生成密钥对"""
        private_key = random.randint(1, self.order - 1)
        public_key_point = private_key * self.generator
        return private_key, public_key_point
    
    def ecdsa_sign(self, private_key, message, k=None):
        """ECDSA 签名"""
        if k is None:
            k = random.randint(1, self.order - 1)
            
        e = int.from_bytes(self._hash_message(message), 'big') % self.order
        
        # 计算 r
        point = k * self.generator
        r = point.x() % self.order
        if r == 0:
            raise ValueError("r cannot be zero")
        
        # 计算 s = k^(-1) * (e + r * d) mod n
        k_inv = self._mod_inverse(k, self.order)
        s = (k_inv * (e + r * private_key)) % self.order
        if s == 0:
            raise ValueError("s cannot be zero")
            
        return (r, s), k, e
    
    def sm2_like_sign(self, private_key, message, k=None):
        """SM2 风格的签名（简化版）"""
        if k is None:
            k = random.randint(1, self.order - 1)
            
        e = int.from_bytes(self._hash_message(message), 'big') % self.order
        
        # 计算点
        point = k * self.generator
        x1 = point.x() % self.order
        
        # SM2: r = (e + x1) mod n
        r = (e + x1) % self.order
        if r == 0 or (r + k) % self.order == 0:
            raise ValueError("Invalid r or r+k")
        
        # SM2: s = d^(-1) * (k - r * d) mod n
        d_inv = self._mod_inverse(private_key, self.order)
        s = (d_inv * (k - r * private_key)) % self.order
        if s == 0:
            raise ValueError("s cannot be zero")
            
        return (r, s), k, e, x1
    
    def ec_encrypt(self, public_key, message, k=None):
        """椭圆曲线加密（简化的 ECIES 类似）"""
        if k is None:
            k = random.randint(1, self.order - 1)
            
        # C1 = kG
        C1 = k * self.generator
        
        # 共享密钥 = kP
        shared_point = k * public_key
        shared_key = hashlib.sha256(
            str(shared_point.x()).encode() + str(shared_point.y()).encode()
        ).digest()[:16]  # 取前16字节作为AES密钥
        
        # 使用 AES 加密消息
        cipher = AES.new(shared_key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(message.encode())
        
        return {
            'C1': C1,
            'ciphertext': ciphertext,
            'nonce': cipher.nonce,
            'tag': tag
        }, k, shared_key
    
    def attack_key_reuse_across_algorithms(self):
        """攻击场景1：跨算法密钥重用"""
        print("=== 攻击场景1：跨算法密钥重用 ===")
        
        # 受害者在 ECDSA 和 SM2 中使用相同私钥
        victim_private_key, victim_public_key = self.generate_keypair()
        message = "Important message"
        
        print(f"受害者私钥: {victim_private_key}")
        print(f"消息: {message}")
        
        # 获得 ECDSA 签名
        ecdsa_sig, k1, e1 = self.ecdsa_sign(victim_private_key, message)
        print(f"ECDSA 签名: r={ecdsa_sig[0]}, s={ecdsa_sig[1]}")
        
        # 获得 SM2 签名（使用不同的 k）
        sm2_sig, k2, e2, x1 = self.sm2_like_sign(victim_private_key, message)
        print(f"SM2 签名: r={sm2_sig[0]}, s={sm2_sig[1]}")
        
        # 尝试分析两种签名的相关性
        print(f"\\n分析：")
        print(f"ECDSA 和 SM2 使用相同私钥，但签名格式不同")
        print(f"攻击者可以通过多个签名样本进行统计分析")
        print(f"或利用算法实现的差异进行侧信道攻击")
        
        return victim_private_key, ecdsa_sig, sm2_sig
    
    def attack_nonce_reuse_across_operations(self):
        """攻击场景2：跨操作随机数重用"""
        print("\\n=== 攻击场景2：跨操作随机数重用 ===")
        
        victim_private_key, victim_public_key = self.generate_keypair()
        message1 = "Message to be signed"
        message2 = "Message to be encrypted"
        
        # 危险：在签名和加密中重用相同的随机数
        dangerous_k = random.randint(1, self.order - 1)
        
        print(f"重用的随机数 k: {dangerous_k}")
        
        # 获得签名（使用 dangerous_k）
        signature, _, e = self.ecdsa_sign(victim_private_key, message1, dangerous_k)
        print(f"签名消息: {message1}")
        print(f"签名: r={signature[0]}, s={signature[1]}")
        
        # 获得加密（使用相同的 dangerous_k）
        encryption_result, _, shared_key = self.ec_encrypt(victim_public_key, message2, dangerous_k)
        print(f"加密消息: {message2}")
        print(f"加密结果 C1: ({encryption_result['C1'].x()}, {encryption_result['C1'].y()})")
        
        # 攻击分析
        print(f"\\n攻击分析：")
        print(f"1. 从签名中获得 r = (kG).x = {signature[0]}")
        print(f"2. 从加密中获得 C1 = kG = ({encryption_result['C1'].x()}, {encryption_result['C1'].y()})")
        print(f"3. 验证一致性: C1.x mod n = {encryption_result['C1'].x() % self.order}")
        print(f"4. 一致性检查: {signature[0] == encryption_result['C1'].x() % self.order}")
        
        if signature[0] == encryption_result['C1'].x() % self.order:
            print("✓ 检测到随机数重用！")
            print("攻击者现在可以：")
            print("- 确认签名和加密使用了相同的随机数")
            print("- 利用已知的 kG 进行进一步攻击")
            print("- 如果获得更多使用相同 k 的操作，可能恢复私钥")
            
            return True, dangerous_k, signature, encryption_result
        
        return False, None, None, None
    
    def attack_multi_signature_nonce_reuse(self):
        """攻击场景3：多重签名中的随机数重用"""
        print("\\n=== 攻击场景3：多重签名随机数重用 ===")
        
        # 两个用户，但错误地重用了随机数
        private_key1, public_key1 = self.generate_keypair()
        private_key2, public_key2 = self.generate_keypair()
        
        message1 = "Transaction 1"
        message2 = "Transaction 2"
        shared_k = random.randint(1, self.order - 1)  # 危险的共享随机数
        
        print(f"用户1私钥: {private_key1}")
        print(f"用户2私钥: {private_key2}")
        print(f"共享随机数 k: {shared_k}")
        
        # 两个用户使用相同的 k 进行签名
        sig1, _, e1 = self.ecdsa_sign(private_key1, message1, shared_k)
        sig2, _, e2 = self.ecdsa_sign(private_key2, message2, shared_k)
        
        print(f"用户1签名: r={sig1[0]}, s={sig1[1]} (消息: {message1})")
        print(f"用户2签名: r={sig2[0]}, s={sig2[1]} (消息: {message2})")
        
        # 攻击：利用相同的 r 值
        if sig1[0] == sig2[0]:  # r 值相同，确认使用了相同的 k
            print("\\n检测到相同的 r 值，确认随机数重用！")
            
            # 计算私钥差值
            # s1 = k^(-1) * (e1 + r * d1)
            # s2 = k^(-1) * (e2 + r * d2)
            # s1 - s2 = k^(-1) * ((e1 - e2) + r * (d1 - d2))
            
            s_diff = (sig1[1] - sig2[1]) % self.order
            e_diff = (e1 - e2) % self.order
            r = sig1[0]
            
            if s_diff != 0:
                # 如果我们知道一个私钥，可以计算另一个
                print("攻击分析：")
                print(f"s1 - s2 = {s_diff}")
                print(f"e1 - e2 = {e_diff}")
                print(f"理论上可以通过以下关系获取信息：")
                print(f"(s1 - s2) = k^(-1) * ((e1 - e2) + r * (d1 - d2))")
                print("如果攻击者知道其中一个私钥，可以计算另一个")
                
                # 假设攻击者通过其他方式获得了 private_key1
                print(f"\\n假设攻击者已知用户1的私钥...")
                known_private_key = private_key1
                
                # 恢复共享的 k
                k_inv_times_factor = s_diff * self._mod_inverse(e_diff + r * (known_private_key - private_key2), self.order) % self.order
                
                # 这里的计算比较复杂，但原理是通过方程组求解
                print("攻击者可以利用这些信息进行进一步分析")
        
        return private_key1, private_key2, sig1, sig2
    
    def demonstrate_attacks(self):
        """演示所有攻击场景"""
        print("跨算法重用密钥和随机数攻击演示")
        print("=" * 60)
        
        # 攻击场景1
        self.attack_key_reuse_across_algorithms()
        
        # 攻击场景2
        self.attack_nonce_reuse_across_operations()
        
        # 攻击场景3
        self.attack_multi_signature_nonce_reuse()
        
        print("\\n" + "=" * 60)
        print("攻击演示完成")
        print("主要风险：")
        print("1. 跨算法密钥重用降低整体安全性")
        print("2. 随机数重用可能暴露密钥信息")
        print("3. 多系统间的关联攻击")
        print("\\n防护建议：")
        print("1. 为不同算法使用不同的密钥")
        print("2. 确保随机数的唯一性和随机性")
        print("3. 实施密钥隔离和生命周期管理")

def main():
    """主函数"""
    attack = CrossAlgorithmAttack()
    attack.demonstrate_attacks()

if __name__ == "__main__":
    main()
