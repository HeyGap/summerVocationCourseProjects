#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SM2/ECDSA 签名延展性 (Malleability) 攻击 PoC
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import hashlib
import random
from ecdsa import NIST256p, SigningKey, util
from ecdsa.ellipticcurve import Point
from Crypto.Util.number import inverse

class MalleabilityAttack:
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
            
        return (r, s), e
    
    def ecdsa_verify(self, public_key, message, signature):
        """ECDSA 签名验证"""
        r, s = signature
        if r <= 0 or r >= self.order or s <= 0 or s >= self.order:
            return False
        
        e = int.from_bytes(self._hash_message(message), 'big') % self.order
        
        try:
            s_inv = self._mod_inverse(s, self.order)
            u1 = (e * s_inv) % self.order
            u2 = (r * s_inv) % self.order
            
            point = u1 * self.generator + u2 * public_key
            return r == (point.x() % self.order)
        except:
            return False
    
    def create_malleable_signature(self, original_signature):
        """创建延展签名"""
        r, s = original_signature
        
        # 基本延展性：(r, s) -> (r, n - s)
        s_malleable = (self.order - s) % self.order
        
        return (r, s_malleable)
    
    def is_canonical_signature(self, signature):
        """检查签名是否为规范形式（低 s 值）"""
        r, s = signature
        return s <= self.order // 2
    
    def canonicalize_signature(self, signature):
        """将签名规范化为低 s 值形式"""
        r, s = signature
        if s > self.order // 2:
            s = self.order - s
        return (r, s)
    
    def demonstrate_basic_malleability(self):
        """演示基本签名延展性"""
        print("=== 基本签名延展性攻击 ===")
        
        # 生成密钥对
        private_key, public_key = self.generate_keypair()
        message = "Important transaction: Transfer 100 BTC to Alice"
        
        print(f"消息: {message}")
        
        # 创建原始签名
        original_sig, e = self.ecdsa_sign(private_key, message)
        print(f"原始签名: r={original_sig[0]}, s={original_sig[1]}")
        print(f"原始签名验证: {self.ecdsa_verify(public_key, message, original_sig)}")
        print(f"原始签名是否规范: {self.is_canonical_signature(original_sig)}")
        
        # 创建延展签名
        malleable_sig = self.create_malleable_signature(original_sig)
        print(f"延展签名: r={malleable_sig[0]}, s={malleable_sig[1]}")
        print(f"延展签名验证: {self.ecdsa_verify(public_key, message, malleable_sig)}")
        print(f"延展签名是否规范: {self.is_canonical_signature(malleable_sig)}")
        
        # 验证数学关系
        s_sum = (original_sig[1] + malleable_sig[1]) % self.order
        print(f"\\n数学验证:")
        print(f"s + s' mod n = {s_sum}")
        print(f"应该等于 0: {s_sum == 0}")
        
        # 展示攻击影响
        print(f"\\n攻击影响分析:")
        print(f"1. 同一消息存在两个有效签名")
        print(f"2. 可能导致交易ID变化")
        print(f"3. 绕过重复签名检测")
        
        return original_sig, malleable_sig
    
    def demonstrate_transaction_malleability(self):
        """演示交易延展性攻击场景"""
        print("\\n=== 交易延展性攻击场景 ===")
        
        # 模拟比特币交易
        sender_key, sender_pubkey = self.generate_keypair()
        
        # 原始交易
        transaction_data = {
            'from': 'Alice',
            'to': 'Bob', 
            'amount': 1.5,
            'fee': 0.001,
            'nonce': 12345
        }
        
        # 创建交易消息
        tx_message = f"From:{transaction_data['from']},To:{transaction_data['to']},Amount:{transaction_data['amount']},Fee:{transaction_data['fee']},Nonce:{transaction_data['nonce']}"
        print(f"交易消息: {tx_message}")
        
        # 签名交易
        original_sig, e = self.ecdsa_sign(sender_key, tx_message)
        
        # 计算原始交易ID（基于交易内容和签名）
        original_tx_content = tx_message + f",r={original_sig[0]},s={original_sig[1]}"
        original_tx_id = hashlib.sha256(original_tx_content.encode()).hexdigest()[:16]
        
        print(f"原始签名: r={original_sig[0]}, s={original_sig[1]}")
        print(f"原始交易ID: {original_tx_id}")
        
        # 攻击者创建延展签名
        malleable_sig = self.create_malleable_signature(original_sig)
        
        # 计算延展交易ID
        malleable_tx_content = tx_message + f",r={malleable_sig[0]},s={malleable_sig[1]}"
        malleable_tx_id = hashlib.sha256(malleable_tx_content.encode()).hexdigest()[:16]
        
        print(f"延展签名: r={malleable_sig[0]}, s={malleable_sig[1]}")
        print(f"延展交易ID: {malleable_tx_id}")
        
        # 验证两个签名都有效
        print(f"\\n验证结果:")
        print(f"原始签名有效: {self.ecdsa_verify(sender_pubkey, tx_message, original_sig)}")
        print(f"延展签名有效: {self.ecdsa_verify(sender_pubkey, tx_message, malleable_sig)}")
        print(f"交易ID不同: {original_tx_id != malleable_tx_id}")
        
        # 攻击场景分析
        print(f"\\n攻击场景:")
        print(f"1. Alice 发送交易给 Bob，使用原始签名")
        print(f"2. 攻击者截获交易，创建延展版本")
        print(f"3. 攻击者广播延展交易，可能先于原始交易被确认")
        print(f"4. 原始交易可能因为'双花'而被拒绝")
        print(f"5. Alice 的钱包可能显示交易失败，实际已成功")
        
        return original_tx_id, malleable_tx_id, original_sig, malleable_sig
    
    def demonstrate_canonical_signatures(self):
        """演示规范签名防护"""
        print("\\n=== 规范签名防护演示 ===")
        
        private_key, public_key = self.generate_keypair()
        message = "Protected transaction"
        
        # 创建多个签名，寻找高 s 值的签名
        high_s_sig = None
        attempts = 0
        
        while high_s_sig is None and attempts < 100:
            sig, e = self.ecdsa_sign(private_key, message)
            if not self.is_canonical_signature(sig):
                high_s_sig = sig
                break
            attempts += 1
        
        if high_s_sig is None:
            print("未找到高 s 值签名，创建一个演示用例...")
            # 手动创建一个高 s 值签名用于演示
            normal_sig, e = self.ecdsa_sign(private_key, message)
            high_s_sig = (normal_sig[0], self.order - normal_sig[1])
        
        print(f"高 s 值签名: r={high_s_sig[0]}, s={high_s_sig[1]}")
        print(f"签名验证: {self.ecdsa_verify(public_key, message, high_s_sig)}")
        print(f"是否规范: {self.is_canonical_signature(high_s_sig)}")
        
        # 规范化签名
        canonical_sig = self.canonicalize_signature(high_s_sig)
        print(f"规范化后: r={canonical_sig[0]}, s={canonical_sig[1]}")
        print(f"规范签名验证: {self.ecdsa_verify(public_key, message, canonical_sig)}")
        print(f"是否规范: {self.is_canonical_signature(canonical_sig)}")
        
        # 防护效果
        print(f"\\n防护效果:")
        print(f"1. 只接受规范签名（低 s 值）")
        print(f"2. 拒绝高 s 值签名")
        print(f"3. 消除签名延展性")
        print(f"4. 确保签名唯一性")
        
        return high_s_sig, canonical_sig
    
    def batch_malleability_detection(self):
        """批量延展性检测"""
        print("\\n=== 批量延展性检测 ===")
        
        # 生成多个签名，包括一些延展对
        private_key, public_key = self.generate_keypair()
        signatures = []
        
        # 生成正常签名
        for i in range(5):
            message = f"Message {i}"
            sig, e = self.ecdsa_sign(private_key, message)
            signatures.append((sig, message, f"msg_{i}"))
        
        # 添加一些延展签名
        original_sig = signatures[1][0]  # 使用第二个签名
        malleable_sig = self.create_malleable_signature(original_sig)
        signatures.append((malleable_sig, signatures[1][1], "malleable_of_msg_1"))
        
        print("生成的签名列表:")
        for i, (sig, msg, label) in enumerate(signatures):
            print(f"{i}: {label} -> r={sig[0]}, s={sig[1]}, canonical={self.is_canonical_signature(sig)}")
        
        # 检测延展性
        print("\\n延展性检测结果:")
        malleable_pairs = []
        
        for i in range(len(signatures)):
            for j in range(i + 1, len(signatures)):
                sig1, msg1, label1 = signatures[i]
                sig2, msg2, label2 = signatures[j]
                
                # 检查是否为延展对
                if (sig1[0] == sig2[0] and 
                    (sig1[1] + sig2[1]) % self.order == 0 and
                    msg1 == msg2):
                    malleable_pairs.append((i, j, label1, label2))
                    print(f"发现延展对: {label1} 和 {label2}")
        
        if not malleable_pairs:
            print("未发现延展签名对")
        
        return signatures, malleable_pairs
    
    def demonstrate_attacks(self):
        """演示所有延展性攻击"""
        print("SM2/ECDSA 签名延展性攻击演示")
        print("=" * 60)
        
        # 基本延展性
        self.demonstrate_basic_malleability()
        
        # 交易延展性
        self.demonstrate_transaction_malleability()
        
        # 规范签名防护
        self.demonstrate_canonical_signatures()
        
        # 批量检测
        self.batch_malleability_detection()
        
        print("\\n" + "=" * 60)
        print("延展性攻击演示完成")
        print("\\n主要发现:")
        print("1. 每个 ECDSA 签名都存在数学上的延展版本")
        print("2. 延展性可能导致交易ID变化和系统混乱")
        print("3. 规范化签名可以有效防护延展性攻击")
        print("4. 批量检测可以识别系统中的延展签名")
        print("\\n防护建议:")
        print("1. 强制使用规范签名（低 s 值）")
        print("2. 在协议层面拒绝高 s 值签名")
        print("3. 使用确定性签名生成 (RFC 6979)")
        print("4. 实施签名唯一性验证")

def main():
    """主函数"""
    attack = MalleabilityAttack()
    attack.demonstrate_attacks()

if __name__ == "__main__":
    main()
