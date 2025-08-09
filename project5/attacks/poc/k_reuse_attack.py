#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SM2 随机数 k 泄露和重用攻击 PoC
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import hashlib
import random
from ecdsa import NIST256p, SigningKey, util
from ecdsa.ellipticcurve import Point
from Crypto.Util.number import inverse

class SM2KAttack:
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
    
    def sign_with_k(self, private_key, message, k):
        """使用指定的 k 值进行签名（模拟 ECDSA 签名）"""
        e = int.from_bytes(self._hash_message(message), 'big') % self.order
        
        # 计算 r
        point = k * self.generator
        r = point.x() % self.order
        if r == 0:
            raise ValueError("r cannot be zero")
        
        # 计算 s
        k_inv = self._mod_inverse(k, self.order)
        s = (k_inv * (e + r * private_key)) % self.order
        if s == 0:
            raise ValueError("s cannot be zero")
            
        return (r, s), k, e
    
    def attack_leaked_k(self, signature, k, message_hash, public_key_point):
        """攻击场景1：已知随机数 k"""
        print("=== 攻击场景1：已知随机数 k ===")
        r, s = signature
        
        # 恢复私钥: d = r^(-1) * (k*s - e) mod n
        r_inv = self._mod_inverse(r, self.order)
        recovered_private_key = (r_inv * (k * s - message_hash)) % self.order
        
        # 验证恢复的私钥
        recovered_public_key = recovered_private_key * self.generator
        
        print(f"原始公钥点: ({public_key_point.x()}, {public_key_point.y()})")
        print(f"恢复公钥点: ({recovered_public_key.x()}, {recovered_public_key.y()})")
        print(f"私钥恢复成功: {recovered_public_key == public_key_point}")
        
        return recovered_private_key
    
    def attack_reused_k(self, sig1, sig2, msg1, msg2):
        """攻击场景2：重用随机数 k"""
        print("\n=== 攻击场景2：重用随机数 k ===")
        
        r1, s1 = sig1
        r2, s2 = sig2
        
        # 检查是否确实重用了 k (r 值相同)
        if r1 != r2:
            print("警告：两个签名的 r 值不同，可能没有重用 k")
            return None
        
        e1 = int.from_bytes(self._hash_message(msg1), 'big') % self.order
        e2 = int.from_bytes(self._hash_message(msg2), 'big') % self.order
        
        # 恢复 k: k = (e1 - e2) * (s1 - s2)^(-1) mod n
        if s1 == s2:
            print("签名 s 值相同，无法通过此方法恢复 k")
            return None
        
        s_diff_inv = self._mod_inverse((s1 - s2) % self.order, self.order)
        recovered_k = ((e1 - e2) * s_diff_inv) % self.order
        
        print(f"恢复的随机数 k: {recovered_k}")
        
        # 验证 k 是否正确
        test_point = recovered_k * self.generator
        if test_point.x() % self.order == r1:
            print("随机数 k 恢复成功！")
            
            # 使用恢复的 k 计算私钥
            r_inv = self._mod_inverse(r1, self.order)
            recovered_private_key = (r_inv * (recovered_k * s1 - e1)) % self.order
            
            return recovered_private_key, recovered_k
        else:
            print("随机数 k 恢复失败")
            return None
    
    def demonstrate_attack(self):
        """演示攻击过程"""
        print("SM2/ECDSA 随机数 k 攻击演示")
        print("=" * 50)
        
        # 生成受害者密钥对
        victim_private_key, victim_public_key = self.generate_keypair()
        print(f"受害者私钥: {victim_private_key}")
        print(f"受害者公钥: ({victim_public_key.x()}, {victim_public_key.y()})")
        
        # 场景1：泄露随机数 k
        message1 = "Hello, this is a test message"
        k_leaked = random.randint(1, self.order - 1)
        
        signature1, k_used, e1 = self.sign_with_k(victim_private_key, message1, k_leaked)
        print(f"\n消息1: {message1}")
        print(f"签名1: r={signature1[0]}, s={signature1[1]}")
        print(f"泄露的随机数 k: {k_leaked}")
        
        recovered_key1 = self.attack_leaked_k(signature1, k_leaked, e1, victim_public_key)
        print(f"恢复的私钥: {recovered_key1}")
        print(f"私钥恢复成功: {recovered_key1 == victim_private_key}")
        
        # 场景2：重用随机数 k
        print(f"\n{'-' * 50}")
        
        message2 = "Another message"
        message3 = "Yet another message"
        
        # 故意重用同一个随机数
        k_reused = random.randint(1, self.order - 1)
        signature2, _, e2 = self.sign_with_k(victim_private_key, message2, k_reused)
        signature3, _, e3 = self.sign_with_k(victim_private_key, message3, k_reused)
        
        print(f"消息2: {message2}")
        print(f"签名2: r={signature2[0]}, s={signature2[1]}")
        print(f"消息3: {message3}")
        print(f"签名3: r={signature3[0]}, s={signature3[1]}")
        print(f"重用的随机数 k: {k_reused}")
        
        result = self.attack_reused_k(signature2, signature3, message2, message3)
        if result:
            recovered_key2, recovered_k = result
            print(f"恢复的私钥: {recovered_key2}")
            print(f"私钥恢复成功: {recovered_key2 == victim_private_key}")
            print(f"随机数恢复成功: {recovered_k == k_reused}")

def main():
    """主函数"""
    attack = SM2KAttack()
    attack.demonstrate_attack()

if __name__ == "__main__":
    main()
