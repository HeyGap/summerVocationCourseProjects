#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
忽略消息校验与 DER 编码歧义攻击 PoC
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import hashlib
import random
import json
import xml.etree.ElementTree as ET
from ecdsa import NIST256p, SigningKey, util
from ecdsa.ellipticcurve import Point
from ecdsa.der import encode_sequence, encode_integer, remove_sequence, remove_integer
from Crypto.Util.number import inverse
import binascii

class MessageValidationDERAttack:
    def __init__(self):
        self.curve = NIST256p
        self.generator = self.curve.generator
        self.order = self.curve.order
        
    def _hash_message(self, message):
        """计算消息哈希"""
        if isinstance(message, str):
            message = message.encode('utf-8')
        return hashlib.sha256(message).digest()
    
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
        k_inv = inverse(k, self.order)
        s = (k_inv * (e + r * private_key)) % self.order
        if s == 0:
            raise ValueError("s cannot be zero")
            
        return (r, s)
    
    def ecdsa_verify(self, public_key, message, signature):
        """ECDSA 签名验证"""
        r, s = signature
        if r <= 0 or r >= self.order or s <= 0 or s >= self.order:
            return False
        
        message_hash = self._hash_message(message)
        e = int.from_bytes(message_hash, 'big') % self.order
        
        try:
            s_inv = inverse(s, self.order)
            u1 = (e * s_inv) % self.order
            u2 = (r * s_inv) % self.order
            
            point = u1 * self.generator + u2 * public_key
            return r == (point.x() % self.order)
        except:
            return False
    
    def weak_message_verify(self, public_key, message, signature):
        """易受攻击的消息验证（只验证前32字节）"""
        if len(message) >= 32:
            partial_message = message[:32]
        else:
            partial_message = message
        
        return self.ecdsa_verify(public_key, partial_message, signature)
    
    def create_der_signature(self, r, s):
        """创建标准 DER 编码签名"""
        r_bytes = encode_integer(r)
        s_bytes = encode_integer(s)
        return encode_sequence(r_bytes, s_bytes)
    
    def create_ambiguous_der_signature(self, r, s):
        """创建歧义 DER 编码签名"""
        # 添加不必要的前导零
        r_bytes = self._encode_integer_with_extra_zero(r)
        s_bytes = self._encode_integer_with_extra_zero(s)
        
        # 使用长形式长度编码
        ambiguous_der = self._encode_sequence_long_form(r_bytes, s_bytes)
        
        return ambiguous_der
    
    def _encode_integer_with_extra_zero(self, value):
        """编码整数时添加不必要的前导零"""
        # 标准编码
        standard = encode_integer(value)
        
        # 添加额外的零字节（在某些实现中可能被接受）
        if len(standard) >= 3 and standard[2] & 0x80 == 0:
            # 插入额外的零字节
            extra_zero = bytearray(standard)
            extra_zero[1] += 1  # 增加长度
            extra_zero.insert(2, 0x00)  # 插入零字节
            return bytes(extra_zero)
        
        return standard
    
    def _encode_sequence_long_form(self, *components):
        """使用长形式编码 SEQUENCE"""
        content = b''.join(components)
        length = len(content)
        
        # 如果长度小于127，故意使用长形式
        if length < 127:
            # 长形式：0x81 表示后面有1个字节表示长度
            length_bytes = bytes([0x81, length])
        else:
            # 正常的长形式编码
            length_bytes = encode_length(length)
        
        return bytes([0x30]) + length_bytes + content
    
    def parse_der_signature(self, der_bytes):
        """解析 DER 编码的签名"""
        try:
            # 简化的 DER 解析
            if der_bytes[0] != 0x30:
                raise ValueError("Not a SEQUENCE")
            
            # 解析长度
            length_info = self._parse_length(der_bytes[1:])
            length = length_info['length']
            length_bytes = length_info['bytes_used']
            
            content = der_bytes[1 + length_bytes:1 + length_bytes + length]
            
            # 解析 r
            r_info = self._parse_integer(content, 0)
            r = r_info['value']
            r_end = r_info['end_pos']
            
            # 解析 s  
            s_info = self._parse_integer(content, r_end)
            s = s_info['value']
            
            return (r, s)
        except:
            return None
    
    def _parse_length(self, data):
        """解析 DER 长度字段"""
        if data[0] & 0x80 == 0:
            # 短形式
            return {'length': data[0], 'bytes_used': 1}
        else:
            # 长形式
            length_bytes = data[0] & 0x7f
            if length_bytes == 0:
                raise ValueError("不定长度在 DER 中不允许")
            
            length = 0
            for i in range(1, 1 + length_bytes):
                length = (length << 8) + data[i]
            
            return {'length': length, 'bytes_used': 1 + length_bytes}
    
    def _parse_integer(self, data, offset):
        """解析 DER 整数"""
        if data[offset] != 0x02:
            raise ValueError("Not an INTEGER")
        
        length = data[offset + 1]
        value_bytes = data[offset + 2:offset + 2 + length]
        
        # 移除前导零（但保留一个零如果需要）
        while len(value_bytes) > 1 and value_bytes[0] == 0x00:
            value_bytes = value_bytes[1:]
        
        value = int.from_bytes(value_bytes, 'big')
        return {'value': value, 'end_pos': offset + 2 + length}
    
    def demonstrate_partial_message_attack(self):
        """演示部分消息验证攻击"""
        print("=== 部分消息验证攻击演示 ===")
        
        private_key, public_key = self.generate_keypair()
        
        # 合法消息（只有前32字节会被验证）
        legitimate_prefix = "TRANSFER:Alice->Bob:$100.00:ID"  # 32字节
        legitimate_message = legitimate_prefix + ":12345"
        
        print(f"合法消息: {legitimate_message}")
        print(f"消息长度: {len(legitimate_message)}")
        
        # 创建签名（基于完整消息）
        signature = self.ecdsa_sign(private_key, legitimate_message)
        print(f"签名: r={signature[0]}, s={signature[1]}")
        
        # 验证正常情况
        print(f"完整验证: {self.ecdsa_verify(public_key, legitimate_message, signature)}")
        print(f"部分验证: {self.weak_message_verify(public_key, legitimate_message, signature)}")
        
        # 攻击：构造恶意消息
        malicious_suffix = ":99999999999:HACKER_ACCOUNT"
        malicious_message = legitimate_prefix + malicious_suffix
        
        print(f"\\n恶意消息: {malicious_message}")
        print(f"恶意消息长度: {len(malicious_message)}")
        
        # 测试攻击效果
        print(f"完整验证恶意消息: {self.ecdsa_verify(public_key, malicious_message, signature)}")
        print(f"部分验证恶意消息: {self.weak_message_verify(public_key, malicious_message, signature)}")
        
        print("\\n攻击分析:")
        print("1. 系统只验证消息的前32字节")
        print("2. 攻击者可以在后面添加任意内容")
        print("3. 签名验证通过，但消息内容已被篡改")
        
        return legitimate_message, malicious_message, signature
    
    def demonstrate_unicode_normalization_attack(self):
        """演示 Unicode 规范化攻击"""
        print("\\n=== Unicode 规范化攻击演示 ===")
        
        private_key, public_key = self.generate_keypair()
        
        # 两种不同的 Unicode 编码表示相同字符
        message1 = "café"  # é = U+00E9 (预组合)
        message2 = "café"  # é = e + U+0301 (组合字符)
        
        print(f"消息1: {repr(message1)} (长度: {len(message1)})")
        print(f"消息2: {repr(message2)} (长度: {len(message2)})")
        print(f"视觉上相同: {message1 == message2}")
        print(f"字节级相同: {message1.encode('utf-8') == message2.encode('utf-8')}")
        
        # 计算哈希值
        hash1 = hashlib.sha256(message1.encode('utf-8')).hexdigest()
        hash2 = hashlib.sha256(message2.encode('utf-8')).hexdigest()
        
        print(f"哈希值1: {hash1}")
        print(f"哈希值2: {hash2}")
        print(f"哈希相同: {hash1 == hash2}")
        
        # 签名验证
        signature1 = self.ecdsa_sign(private_key, message1)
        
        print(f"\\n用消息1的签名验证消息2:")
        print(f"验证结果: {self.ecdsa_verify(public_key, message2, signature1)}")
        
        print("\\n攻击分析:")
        print("1. 两个消息视觉上相同但编码不同")
        print("2. 哈希值不同，签名验证失败")
        print("3. 但在某些系统中可能被误认为是相同消息")
        
        return message1, message2, signature1
    
    def demonstrate_json_structure_attack(self):
        """演示 JSON 结构攻击"""
        print("\\n=== JSON 结构攻击演示 ===")
        
        private_key, public_key = self.generate_keypair()
        
        # 原始 JSON 消息
        original_data = {
            "from": "Alice",
            "to": "Bob", 
            "amount": 100,
            "currency": "USD"
        }
        original_json = json.dumps(original_data, sort_keys=True)
        
        print(f"原始JSON: {original_json}")
        
        # 创建签名
        signature = self.ecdsa_sign(private_key, original_json)
        print(f"签名: r={signature[0]}, s={signature[1]}")
        
        # 攻击：添加重复字段（某些解析器可能使用最后一个值）
        malicious_data = {
            "from": "Alice",
            "to": "Bob",
            "amount": 100,
            "currency": "USD",
            "amount": 1000000  # 重复的 amount 字段
        }
        
        # 手动构造JSON字符串以包含重复字段
        malicious_json = '{"amount": 100, "amount": 1000000, "currency": "USD", "from": "Alice", "to": "Bob"}'
        
        print(f"\\n恶意JSON: {malicious_json}")
        
        # 验证结果
        original_valid = self.ecdsa_verify(public_key, original_json, signature)
        malicious_valid = self.ecdsa_verify(public_key, malicious_json, signature)
        
        print(f"原始JSON验证: {original_valid}")
        print(f"恶意JSON验证: {malicious_valid}")
        
        print("\\n攻击分析:")
        print("1. JSON 允许重复键，但解析行为未定义")
        print("2. 不同解析器可能有不同行为")
        print("3. 攻击者利用解析差异进行攻击")
        
        return original_json, malicious_json, signature
    
    def demonstrate_der_encoding_ambiguity(self):
        """演示 DER 编码歧义攻击"""
        print("\\n=== DER 编码歧义攻击演示 ===")
        
        private_key, public_key = self.generate_keypair()
        message = "Important transaction"
        
        # 创建签名
        signature = self.ecdsa_sign(private_key, message)
        r, s = signature
        
        print(f"签名: r={r}, s={s}")
        
        # 创建标准 DER 编码
        standard_der = self.create_der_signature(r, s)
        print(f"标准 DER: {binascii.hexlify(standard_der).decode()}")
        
        # 创建歧义 DER 编码
        ambiguous_der = self.create_ambiguous_der_signature(r, s)
        print(f"歧义 DER: {binascii.hexlify(ambiguous_der).decode()}")
        
        # 解析两种编码
        parsed_standard = self.parse_der_signature(standard_der)
        parsed_ambiguous = self.parse_der_signature(ambiguous_der)
        
        print(f"\\n解析标准DER: {parsed_standard}")
        print(f"解析歧义DER: {parsed_ambiguous}")
        
        if parsed_standard and parsed_ambiguous:
            print(f"解析结果相同: {parsed_standard == parsed_ambiguous}")
            
            # 验证两种编码的签名
            if parsed_standard == signature and parsed_ambiguous == signature:
                print("两种 DER 编码都表示相同的签名")
                print("这可能导致签名唯一性问题")
        
        print("\\n攻击分析:")
        print("1. 同一签名可以有多种 DER 编码表示")
        print("2. 严格的系统应该只接受规范编码")
        print("3. 编码差异可能导致重放攻击或缓存绕过")
        
        return standard_der, ambiguous_der, signature
    
    def demonstrate_length_extension_attack(self):
        """演示哈希长度扩展攻击概念"""
        print("\\n=== 哈希长度扩展攻击概念演示 ===")
        
        # 这是一个概念演示，实际的长度扩展攻击需要更复杂的实现
        original_message = "user=alice&role=user"
        secret_key = "super_secret_key"
        
        print(f"原始消息: {original_message}")
        print(f"密钥（攻击者未知）: {secret_key}")
        
        # 正常的 HMAC 计算
        legitimate_mac = hashlib.sha256((secret_key + original_message).encode()).hexdigest()
        print(f"合法MAC: {legitimate_mac}")
        
        # 攻击者尝试扩展消息
        # 注意：这只是概念演示，真实的长度扩展攻击更复杂
        extended_message = original_message + "&admin=true"
        
        print(f"\\n扩展消息: {extended_message}")
        print("注意：真实的长度扩展攻击需要：")
        print("1. 知道原始消息长度")
        print("2. 构造适当的填充")
        print("3. 计算扩展后的哈希值")
        print("4. 本例仅为概念演示")
        
        return original_message, extended_message, legitimate_mac
    
    def demonstrate_attacks(self):
        """演示所有攻击"""
        print("消息校验忽略与 DER 编码歧义攻击演示")
        print("=" * 60)
        
        # 部分消息验证攻击
        self.demonstrate_partial_message_attack()
        
        # Unicode 规范化攻击
        self.demonstrate_unicode_normalization_attack()
        
        # JSON 结构攻击
        self.demonstrate_json_structure_attack()
        
        # DER 编码歧义攻击
        self.demonstrate_der_encoding_ambiguity()
        
        # 长度扩展攻击概念
        self.demonstrate_length_extension_attack()
        
        print("\\n" + "=" * 60)
        print("攻击演示完成")
        print("\\n主要发现:")
        print("1. 不完整的消息验证可能被绕过")
        print("2. 编码差异可能导致安全漏洞")
        print("3. 结构化数据的解析歧义存在风险")
        print("4. DER 编码的规范性验证很重要")
        print("\\n防护建议:")
        print("1. 始终验证完整的消息内容")
        print("2. 使用标准化的编码和解析库")
        print("3. 实施严格的 DER 编码验证")
        print("4. 对结构化数据进行规范化处理")
        print("5. 使用 HMAC 而非简单的哈希拼接")

def main():
    """主函数"""
    attack = MessageValidationDERAttack()
    attack.demonstrate_attacks()

if __name__ == "__main__":
    main()
