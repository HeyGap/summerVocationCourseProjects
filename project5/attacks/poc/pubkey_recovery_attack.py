#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从签名中推导公钥攻击 PoC
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import hashlib
import random
from ecdsa import NIST256p, SigningKey, util
from ecdsa.ellipticcurve import Point
from Crypto.Util.number import inverse

class PublicKeyRecoveryAttack:
    def __init__(self):
        self.curve = NIST256p
        self.generator = self.curve.generator
        self.order = self.curve.order
        self.field_prime = self.curve.curve.p()
        
    def _hash_message(self, message):
        """计算消息哈希"""
        return hashlib.sha256(message.encode('utf-8')).digest()
    
    def _mod_inverse(self, a, m):
        """计算模逆"""
        return inverse(a, m)
    
    def _mod_sqrt(self, a, p):
        """计算模平方根（Tonelli-Shanks 算法）"""
        if pow(a, (p - 1) // 2, p) != 1:
            return None
        
        # 简化版：仅适用于 p ≡ 3 (mod 4)
        if p % 4 == 3:
            return pow(a, (p + 1) // 4, p)
        
        # 完整的 Tonelli-Shanks 算法（这里简化处理）
        return pow(a, (p + 1) // 4, p)
    
    def generate_keypair(self):
        """生成密钥对"""
        private_key = random.randint(1, self.order - 1)
        public_key_point = private_key * self.generator
        return private_key, public_key_point
    
    def ecdsa_sign(self, private_key, message):
        """ECDSA 签名"""
        k = random.randint(1, self.order - 1)
        message_hash = self._hash_message(message)
        e = int.from_bytes(message_hash, 'big') % self.order
        
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
            
        return (r, s), e
    
    def ecdsa_verify(self, public_key, message, signature):
        """ECDSA 签名验证"""
        r, s = signature
        if r <= 0 or r >= self.order or s <= 0 or s >= self.order:
            return False
        
        message_hash = self._hash_message(message)
        e = int.from_bytes(message_hash, 'big') % self.order
        
        try:
            s_inv = self._mod_inverse(s, self.order)
            u1 = (e * s_inv) % self.order
            u2 = (r * s_inv) % self.order
            
            point = u1 * self.generator + u2 * public_key
            return r == (point.x() % self.order)
        except:
            return False
    
    def recover_R_candidates(self, r):
        """从 r 值恢复候选 R 点"""
        candidates = []
        
        # 尝试 x = r
        x1 = r % self.field_prime
        y_squared = (pow(x1, 3, self.field_prime) + 
                    self.curve.curve.a() * x1 + 
                    self.curve.curve.b()) % self.field_prime
        
        y1 = self._mod_sqrt(y_squared, self.field_prime)
        if y1 is not None:
            candidates.append(Point(self.curve.curve, x1, y1, self.order))
            candidates.append(Point(self.curve.curve, x1, (-y1) % self.field_prime, self.order))
        
        # 尝试 x = r + n (如果在有限域内)
        x2 = (r + self.order) % self.field_prime
        if x2 != x1 and x2 < self.field_prime:
            y_squared = (pow(x2, 3, self.field_prime) + 
                        self.curve.curve.a() * x2 + 
                        self.curve.curve.b()) % self.field_prime
            
            y2 = self._mod_sqrt(y_squared, self.field_prime)
            if y2 is not None:
                candidates.append(Point(self.curve.curve, x2, y2, self.order))
                candidates.append(Point(self.curve.curve, x2, (-y2) % self.field_prime, self.order))
        
        return candidates
    
    def recover_public_key(self, signature, message, recovery_id=None):
        """从签名恢复公钥"""
        r, s = signature
        message_hash = self._hash_message(message)
        e = int.from_bytes(message_hash, 'big') % self.order
        
        # 获得 R 点的候选
        R_candidates = self.recover_R_candidates(r)
        
        recovered_pubkeys = []
        
        for i, R in enumerate(R_candidates):
            if R is None:
                continue
                
            try:
                # 计算公钥: P = r^(-1) * (s * R - e * G)
                r_inv = self._mod_inverse(r, self.order)
                P = r_inv * (s * R + (-e % self.order) * self.generator)
                
                # 验证恢复的公钥
                if self.ecdsa_verify(P, message, signature):
                    recovered_pubkeys.append((P, i))
            except:
                continue
        
        return recovered_pubkeys
    
    def demonstrate_basic_pubkey_recovery(self):
        """演示基础公钥恢复"""
        print("=== 基础公钥恢复演示 ===")
        
        # 生成密钥对
        private_key, original_public_key = self.generate_keypair()
        message = "This is a test message for public key recovery"
        
        print(f"原始私钥: {private_key}")
        print(f"原始公钥: ({original_public_key.x()}, {original_public_key.y()})")
        print(f"消息: {message}")
        
        # 创建签名
        signature, e = self.ecdsa_sign(private_key, message)
        print(f"签名: r={signature[0]}, s={signature[1]}")
        
        # 恢复公钥
        recovered_keys = self.recover_public_key(signature, message)
        
        print(f"\\n恢复到 {len(recovered_keys)} 个候选公钥:")
        for i, (pubkey, recovery_id) in enumerate(recovered_keys):
            print(f"候选 {i+1} (recovery_id={recovery_id}): ({pubkey.x()}, {pubkey.y()})")
            
            # 检查是否匹配原始公钥
            if pubkey.x() == original_public_key.x() and pubkey.y() == original_public_key.y():
                print(f"  ✓ 匹配原始公钥！")
            else:
                print(f"  ✗ 不匹配原始公钥")
        
        return recovered_keys, original_public_key
    
    def demonstrate_blockchain_address_recovery(self):
        """演示区块链地址恢复场景"""
        print("\\n=== 区块链地址恢复场景 ===")
        
        # 模拟比特币交易
        sender_key, sender_pubkey = self.generate_keypair()
        
        transaction = {
            'from': 'unknown_address',  # 攻击者不知道发送方地址
            'to': '1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2',
            'amount': '0.5 BTC',
            'fee': '0.0001 BTC'
        }
        
        # 创建交易消息
        tx_message = f"Transfer {transaction['amount']} to {transaction['to']} with fee {transaction['fee']}"
        
        print(f"交易消息: {tx_message}")
        print(f"发送方地址未知...")
        
        # 签名交易
        signature, e = self.ecdsa_sign(sender_key, tx_message)
        print(f"交易签名: r={signature[0]}, s={signature[1]}")
        
        # 攻击者从签名恢复公钥
        recovered_keys = self.recover_public_key(signature, tx_message)
        
        print(f"\\n从签名恢复的候选公钥:")
        for i, (pubkey, recovery_id) in enumerate(recovered_keys):
            # 模拟地址生成（简化版）
            pubkey_bytes = f"{pubkey.x():064x}{pubkey.y():064x}"
            address_hash = hashlib.sha256(pubkey_bytes.encode()).hexdigest()[:20]
            simulated_address = f"1{address_hash[:25]}..."
            
            print(f"候选 {i+1}: 地址 {simulated_address}")
            
            # 检查是否为实际发送方
            if pubkey == sender_pubkey:
                print(f"  ✓ 这是实际的发送方公钥和地址！")
                transaction['from'] = simulated_address
        
        print(f"\\n攻击结果:")
        print(f"攻击者成功识别发送方地址: {transaction['from']}")
        print(f"现在可以追踪该地址的所有交易历史")
        
        return recovered_keys, transaction
    
    def demonstrate_weak_authentication_bypass(self):
        """演示弱身份验证绕过"""
        print("\\n=== 弱身份验证系统绕过 ===")
        
        # 模拟一个弱身份验证系统
        legitimate_user_key, legitimate_user_pubkey = self.generate_keypair()
        attacker_key, attacker_pubkey = self.generate_keypair()
        
        print("场景：系统只验证签名有效性，不验证公钥身份")
        print(f"合法用户公钥: ({legitimate_user_pubkey.x()}, {legitimate_user_pubkey.y()})")
        print(f"攻击者公钥: ({attacker_pubkey.x()}, {attacker_pubkey.y()})")
        
        # 攻击者创建恶意消息和签名
        malicious_message = "TRANSFER: $10000 to attacker_account"
        attacker_signature, e = self.ecdsa_sign(attacker_key, malicious_message)
        
        print(f"\\n攻击者消息: {malicious_message}")
        print(f"攻击者签名: r={attacker_signature[0]}, s={attacker_signature[1]}")
        
        # 弱验证系统的验证过程
        def weak_auth_system(message, signature):
            """弱身份验证系统"""
            # 错误：从签名恢复公钥，但不验证身份
            recovered_keys = self.recover_public_key(signature, message)
            
            if recovered_keys:
                print(f"系统消息: 发现 {len(recovered_keys)} 个有效签名")
                for i, (pubkey, _) in enumerate(recovered_keys):
                    if self.ecdsa_verify(pubkey, message, signature):
                        print(f"  候选 {i+1}: 签名验证通过 ✓")
                        return True, pubkey
            return False, None
        
        # 执行弱验证
        auth_result, recovered_pubkey = weak_auth_system(malicious_message, attacker_signature)
        
        print(f"\\n弱验证系统结果: {'通过' if auth_result else '失败'}")
        if auth_result:
            print(f"系统错误地接受了攻击者的恶意交易！")
            print(f"恢复的公钥: ({recovered_pubkey.x()}, {recovered_pubkey.y()})")
        
        # 展示正确的验证方式
        def secure_auth_system(message, signature, expected_pubkey):
            """安全的身份验证系统"""
            # 1. 验证签名
            if not self.ecdsa_verify(expected_pubkey, message, signature):
                return False, "签名验证失败"
            
            # 2. 验证公钥恢复一致性
            recovered_keys = self.recover_public_key(signature, message)
            pubkey_match = any(
                pk.x() == expected_pubkey.x() and pk.y() == expected_pubkey.y() 
                for pk, _ in recovered_keys
            )
            
            if not pubkey_match:
                return False, "公钥不匹配"
            
            return True, "验证通过"
        
        print(f"\\n安全验证系统测试:")
        secure_result, secure_msg = secure_auth_system(
            malicious_message, attacker_signature, legitimate_user_pubkey
        )
        print(f"安全验证结果: {secure_msg}")
        
        return auth_result, recovered_pubkey
    
    def demonstrate_privacy_analysis_attack(self):
        """演示隐私分析攻击"""
        print("\\n=== 隐私分析攻击演示 ===")
        
        # 模拟用户的多个交易
        user_key, user_pubkey = self.generate_keypair()
        
        transactions = [
            "Payment to merchant A: $50",
            "Payment to merchant B: $30", 
            "Payment to friend C: $20",
            "Withdrawal from ATM: $100",
            "Online purchase: $75"
        ]
        
        signatures = []
        recovered_pubkeys = []
        
        print("收集用户的多个交易签名...")
        for i, tx in enumerate(transactions):
            sig, e = self.ecdsa_sign(user_key, tx)
            signatures.append((tx, sig))
            
            # 攻击者从每个签名恢复公钥
            recovered = self.recover_public_key(sig, tx)
            recovered_pubkeys.extend(recovered)
            
            print(f"交易 {i+1}: {tx}")
            print(f"  签名: r={sig[0]}, s={sig[1]}")
            print(f"  恢复公钥数: {len(recovered)}")
        
        # 分析公钥模式
        print(f"\\n隐私分析结果:")
        print(f"收集到 {len(signatures)} 个签名")
        print(f"恢复得到 {len(recovered_pubkeys)} 个候选公钥")
        
        # 找到真实公钥（出现频率最高的）
        pubkey_counts = {}
        for pubkey, _ in recovered_pubkeys:
            key_id = (pubkey.x(), pubkey.y())
            pubkey_counts[key_id] = pubkey_counts.get(key_id, 0) + 1
        
        if pubkey_counts:
            most_frequent = max(pubkey_counts.items(), key=lambda x: x[1])
            identified_pubkey = most_frequent[0]
            frequency = most_frequent[1]
            
            print(f"识别出的用户公钥: ({identified_pubkey[0]}, {identified_pubkey[1]})")
            print(f"出现频率: {frequency}/{len(signatures)}")
            
            # 验证识别正确性
            actual_key_id = (user_pubkey.x(), user_pubkey.y())
            if identified_pubkey == actual_key_id:
                print("✓ 成功识别用户真实公钥！")
                print("攻击者现在可以：")
                print("  1. 追踪用户的所有交易")
                print("  2. 分析消费模式")
                print("  3. 建立社交关系图谱")
                print("  4. 进行针对性攻击")
            else:
                print("✗ 公钥识别失败")
        
        return signatures, recovered_pubkeys
    
    def demonstrate_batch_analysis_attack(self):
        """演示批量分析攻击"""
        print("\\n=== 批量分析攻击演示 ===")
        
        # 生成多个用户的签名数据
        users = []
        all_signatures = []
        
        print("生成多用户签名数据集...")
        for i in range(5):
            user_key, user_pubkey = self.generate_keypair()
            users.append((f"User_{i+1}", user_key, user_pubkey))
            
            # 每个用户生成多个签名
            for j in range(3):
                message = f"Transaction from User_{i+1} #{j+1}"
                sig, e = self.ecdsa_sign(user_key, message)
                all_signatures.append((f"User_{i+1}", message, sig))
        
        print(f"数据集包含 {len(users)} 个用户，{len(all_signatures)} 个签名")
        
        # 攻击者的批量分析
        print(f"\\n执行批量公钥恢复分析...")
        
        user_pubkey_map = {}  # 用户名 -> 恢复的公钥列表
        pubkey_frequency = {}  # 公钥 -> 出现频率
        
        for user_name, message, signature in all_signatures:
            recovered_keys = self.recover_public_key(signature, message)
            
            if user_name not in user_pubkey_map:
                user_pubkey_map[user_name] = []
            
            for pubkey, recovery_id in recovered_keys:
                key_id = (pubkey.x(), pubkey.y())
                user_pubkey_map[user_name].append(key_id)
                pubkey_frequency[key_id] = pubkey_frequency.get(key_id, 0) + 1
        
        # 分析结果
        print(f"\\n批量分析结果:")
        for user_name, _, actual_pubkey in users:
            actual_key_id = (actual_pubkey.x(), actual_pubkey.y())
            
            # 找到该用户最频繁出现的公钥
            user_keys = user_pubkey_map.get(user_name, [])
            if user_keys:
                user_key_counts = {}
                for key_id in user_keys:
                    user_key_counts[key_id] = user_key_counts.get(key_id, 0) + 1
                
                identified_key = max(user_key_counts.items(), key=lambda x: x[1])[0]
                
                print(f"{user_name}:")
                print(f"  实际公钥: ({actual_key_id[0]}, {actual_key_id[1]})")
                print(f"  识别公钥: ({identified_key[0]}, {identified_key[1]})")
                print(f"  识别正确: {identified_key == actual_key_id}")
        
        return users, all_signatures, user_pubkey_map
    
    def demonstrate_attacks(self):
        """演示所有攻击场景"""
        print("从签名中推导公钥攻击演示")
        print("=" * 60)
        
        # 基础公钥恢复
        self.demonstrate_basic_pubkey_recovery()
        
        # 区块链地址恢复
        self.demonstrate_blockchain_address_recovery()
        
        # 弱身份验证绕过
        self.demonstrate_weak_authentication_bypass()
        
        # 隐私分析攻击
        self.demonstrate_privacy_analysis_attack()
        
        # 批量分析攻击
        self.demonstrate_batch_analysis_attack()
        
        print("\\n" + "=" * 60)
        print("公钥恢复攻击演示完成")
        print("\\n主要发现:")
        print("1. ECDSA 签名允许数学上的公钥恢复")
        print("2. 每个签名通常对应 2-4 个候选公钥")
        print("3. 批量分析可以准确识别用户公钥")
        print("4. 弱身份验证系统容易被绕过")
        print("5. 公钥恢复可用于隐私分析和追踪")
        print("\\n防护建议:")
        print("1. 身份验证时预先绑定公钥身份")
        print("2. 使用多因素认证机制")
        print("3. 考虑使用环签名或零知识证明")
        print("4. 实施交易混合和隐私保护技术")
        print("5. 定期轮换密钥以限制分析窗口")

def main():
    """主函数"""
    attack = PublicKeyRecoveryAttack()
    attack.demonstrate_attacks()

if __name__ == "__main__":
    main()
