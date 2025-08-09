#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比特币风格签名伪造高级演示
专注于与比特币系统相关的签名伪造技术

本模块演示如何基于比特币早期交易数据和中本聪的公开信息
进行数字签名的分析和伪造技术研究。
"""

import hashlib
import secrets
import time
from typing import Dict, List, Tuple, Optional
from ecdsa import SigningKey, VerifyingKey, SECP256k1, ellipticcurve
from src.sm2 import SM2


class BitcoinStyleForger:
    """
    比特币风格签名伪造器
    
    模拟比特币系统中的签名生成和伪造技术
    使用 secp256k1 曲线（比特币标准）
    """
    
    def __init__(self):
        self.curve = SECP256k1  # 比特币使用的椭圆曲线
        self.generator = self.curve.generator
        self.order = self.curve.order
        
        # 比特币相关的历史消息
        self.historical_messages = [
            "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks",
            "Bitcoin: A Peer-to-Peer Electronic Cash System",
            "If you don't believe me or don't get it, I don't have time to try to convince you, sorry.",
            "Bitcoin v0.1 released",
            "Running bitcoin"
        ]
        
        # 模拟中本聪的一些"已知"特征
        self.satoshi_characteristics = {
            "timezone": "GMT",  # 基于论坛发帖时间推测
            "coding_style": "minimalist",
            "preferred_hex": "lowercase",
            "signature_style": "conservative"
        }
    
    def generate_satoshi_style_keypair(self) -> Tuple[SigningKey, VerifyingKey]:
        """
        生成"中本聪风格"的密钥对
        
        基于一些假设的特征来生成看起来像中本聪可能使用的密钥：
        - 使用特定的种子模式
        - 模拟早期比特币客户端的随机数生成
        """
        # 使用与比特币创世时间相关的种子
        genesis_time = "2009-01-03 18:15:05"  # 比特币创世块时间
        seed_material = f"satoshi_nakamoto_{genesis_time}".encode()
        
        # 生成确定性的"随机"私钥
        seed_hash = hashlib.sha256(seed_material).digest()
        private_key_int = int.from_bytes(seed_hash, 'big') % self.order
        
        # 创建密钥对
        sk = SigningKey.from_secret_exponent(private_key_int, curve=self.curve)
        vk = sk.verifying_key
        
        return sk, vk
    
    def forge_genesis_block_signature(self) -> Dict:
        """
        伪造创世块相关的签名
        
        创建一个看起来像是为比特币创世块创建的签名
        """
        message = self.historical_messages[0]  # 创世块中的消息
        message_bytes = message.encode('utf-8')
        
        # 生成"中本聪"密钥对
        sk, vk = self.generate_satoshi_style_keypair()
        
        # 创建签名
        signature = sk.sign(message_bytes, hashfunc=hashlib.sha256)
        
        # 解析签名
        r, s = self._decode_signature(signature)
        
        return {
            "message": message,
            "message_hash": hashlib.sha256(message_bytes).hexdigest(),
            "signature": {
                "r": hex(r),
                "s": hex(s),
                "der_bytes": signature.hex()
            },
            "public_key": {
                "hex": vk.to_string().hex(),
                "address_style": self._pubkey_to_bitcoin_address(vk)
            },
            "metadata": {
                "curve": "secp256k1",
                "hash_function": "SHA256",
                "timestamp": "2009-01-03T18:15:05Z",
                "block_height": 0
            }
        }
    
    def demonstrate_double_spending_attack(self) -> Dict:
        """
        演示双花攻击中的签名伪造
        
        展示如何通过签名延展性或重放攻击实现双花
        """
        # 创建原始交易
        original_tx = "From: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa To: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2 Amount: 50.00000000"
        
        sk, vk = self.generate_satoshi_style_keypair()
        
        # 签名原始交易
        original_sig = sk.sign(original_tx.encode(), hashfunc=hashlib.sha256)
        r_orig, s_orig = self._decode_signature(original_sig)
        
        # 创建延展性攻击签名
        s_malleable = self.order - s_orig  # 签名延展性：s' = -s mod n
        
        # 创建双花交易（相同输入，不同输出）
        double_spend_tx = "From: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa To: 1AttackerAddressXXXXXXXXXXXXXXXXXX Amount: 50.00000000"
        
        return {
            "attack_type": "Double Spending via Signature Malleability",
            "original_transaction": {
                "content": original_tx,
                "signature": {"r": hex(r_orig), "s": hex(s_orig)},
                "valid": True
            },
            "malleability_attack": {
                "malleable_signature": {"r": hex(r_orig), "s": hex(s_malleable)},
                "explanation": "使用相同的r值但计算s' = -s mod n创建另一个有效签名"
            },
            "double_spend_transaction": {
                "content": double_spend_tx,
                "attack_vector": "利用延展性创建不同的交易ID但使用相同的输入"
            }
        }
    
    def analyze_early_bitcoin_signatures(self) -> Dict:
        """
        分析早期比特币签名的模式
        
        模拟对早期比特币区块中签名的分析
        """
        analysis_results = {
            "analysis_period": "2009-01 to 2010-12",
            "signatures_analyzed": 1000,  # 模拟分析的签名数量
            "patterns_found": []
        }
        
        # 模拟发现的模式
        patterns = [
            {
                "pattern": "低随机数值",
                "description": "某些签名使用了较小的k值，可能表明早期随机数生成器的质量问题",
                "risk_level": "中等",
                "example_r": "0x123456789abcdef..."
            },
            {
                "pattern": "时间相关性",
                "description": "连续时间内的签名显示出相似的随机数模式",
                "risk_level": "低",
                "example": "GMT+0 时间段内的签名更规律"
            },
            {
                "pattern": "重复r值",
                "description": "发现了几个使用相同r值的签名，表明可能的k重用",
                "risk_level": "高",
                "count": 3
            }
        ]
        
        analysis_results["patterns_found"] = patterns
        
        return analysis_results
    
    def forge_forum_post_signature(self, post_content: str) -> Dict:
        """
        伪造论坛帖子的签名
        
        模拟为中本聪的论坛帖子创建数字签名
        """
        sk, vk = self.generate_satoshi_style_keypair()
        
        # 添加论坛帖子的典型元数据
        full_message = f"""
Author: satoshi
Date: 2009-01-09 02:54:25
Subject: Bitcoin v0.1 released

{post_content}

--
Satoshi Nakamoto
        """.strip()
        
        signature = sk.sign(full_message.encode(), hashfunc=hashlib.sha256)
        r, s = self._decode_signature(signature)
        
        return {
            "post_metadata": {
                "author": "satoshi",
                "date": "2009-01-09 02:54:25",
                "forum": "bitcointalk.org (predecessor)"
            },
            "content": post_content,
            "full_signed_message": full_message,
            "signature": {
                "r": hex(r),
                "s": hex(s),
                "verification": vk.verify(signature, full_message.encode(), hashfunc=hashlib.sha256)
            },
            "authenticity_note": "This is a forged signature for educational purposes"
        }
    
    def _decode_signature(self, signature: bytes) -> Tuple[int, int]:
        """解析DER编码的签名"""
        try:
            from ecdsa.util import sigdecode_der
            return sigdecode_der(signature, self.order)
        except:
            return 0, 0
    
    def _pubkey_to_bitcoin_address(self, vk: VerifyingKey) -> str:
        """将公钥转换为比特币地址格式（简化版）"""
        pubkey_bytes = vk.to_string()
        pubkey_hash = hashlib.sha256(pubkey_bytes).digest()[:20]
        return f"1{pubkey_hash.hex()[:27]}..."  # 简化的地址格式
    
    def comprehensive_demonstration(self) -> Dict:
        """
        综合演示所有伪造技术
        """
        print("比特币风格签名伪造综合演示")
        print("=" * 50)
        
        results = {
            "timestamp": int(time.time()),
            "demonstrations": []
        }
        
        # 1. 创世块签名伪造
        print("\n1. 创世块签名伪造...")
        genesis_forge = self.forge_genesis_block_signature()
        results["demonstrations"].append({
            "name": "创世块签名伪造",
            "result": genesis_forge
        })
        
        # 2. 双花攻击演示
        print("\n2. 双花攻击签名演示...")
        double_spend = self.demonstrate_double_spending_attack()
        results["demonstrations"].append({
            "name": "双花攻击演示",
            "result": double_spend
        })
        
        # 3. 早期签名模式分析
        print("\n3. 早期比特币签名分析...")
        signature_analysis = self.analyze_early_bitcoin_signatures()
        results["demonstrations"].append({
            "name": "早期签名分析",
            "result": signature_analysis
        })
        
        # 4. 论坛帖子签名伪造
        print("\n4. 论坛帖子签名伪造...")
        forum_post = "Bitcoin is still very much an experimental system. Don't put more money into Bitcoin than you can afford to lose."
        forum_forge = self.forge_forum_post_signature(forum_post)
        results["demonstrations"].append({
            "name": "论坛帖子签名",
            "result": forum_forge
        })
        
        return results


def main():
    """主演示函数"""
    print("比特币风格数字签名伪造高级演示")
    print("=" * 60)
    print("基于 secp256k1 曲线的签名分析与伪造技术")
    print("警告：仅用于教育和研究目的")
    print("=" * 60)
    
    forger = BitcoinStyleForger()
    
    # 运行综合演示
    results = forger.comprehensive_demonstration()
    
    # 显示摘要
    print(f"\n演示完成！")
    print(f"时间戳: {results['timestamp']}")
    print(f"完成演示: {len(results['demonstrations'])} 个")
    
    # 显示关键发现
    print("\n关键发现:")
    for demo in results['demonstrations']:
        print(f"- {demo['name']}: 成功创建伪造签名")
    
    print("\n技术要点:")
    print("- 使用 secp256k1 椭圆曲线（比特币标准）")
    print("- 演示了签名延展性攻击")
    print("- 分析了早期签名的潜在弱点")
    print("- 展示了确定性密钥生成的风险")
    
    print("\n防护建议:")
    print("- 使用 RFC 6979 确定性签名")
    print("- 实施签名规范化（低s值）")
    print("- 加强随机数生成器")
    print("- 定期进行签名安全性审计")
    
    return results


if __name__ == "__main__":
    main()
