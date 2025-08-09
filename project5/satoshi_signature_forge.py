#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中本聪数字签名伪造演示
基于SM2椭圆曲线密码算法的签名伪造技术研究

本模块用于教育和研究目的，演示椭圆曲线数字签名的潜在安全风险
以及如何在已知特定信息时构造有效的数字签名。

理论基础：
1. 椭圆曲线离散对数问题
2. 数字签名的数学结构
3. 已知信息下的签名构造
"""

import os
import hashlib
import secrets
from typing import Tuple, Optional
from ecdsa import SigningKey, VerifyingKey, NIST256p, ellipticcurve
from ecdsa.util import sigdecode_der, sigencode_der
from src.sm2 import SM2


class SatoshiSignatureForge:
    """
    中本聪数字签名伪造类
    
    这个类演示了在特定条件下如何构造看起来像中本聪签名的数字签名。
    注意：这仅用于教育和研究目的。
    """
    
    def __init__(self):
        self.sm2 = SM2()
        self.curve = NIST256p
        self.generator = self.curve.generator
        self.order = self.curve.order
        
    def forge_signature_known_k(self, message: bytes, k: int, 
                               target_r: Optional[int] = None) -> Tuple[int, int]:
        """
        已知随机数k的签名伪造
        
        数学原理：
        在ECDSA中，签名(r,s)满足：
        r = (k * G).x mod n
        s = k^(-1) * (e + d_A * r) mod n
        
        如果已知k，可以选择任意私钥d_fake，然后计算对应的s：
        s_fake = k^(-1) * (e + d_fake * r) mod n
        
        Args:
            message: 要签名的消息
            k: 已知的随机数
            target_r: 目标r值（可选）
            
        Returns:
            伪造的签名(r, s)
        """
        e = int.from_bytes(hashlib.sha256(message).digest(), 'big')
        
        # 计算r
        if target_r is None:
            point = k * self.generator
            r = point.x() % self.order
        else:
            r = target_r
            
        # 选择伪造的私钥
        d_fake = secrets.randbelow(self.order - 1) + 1
        
        # 计算对应的s
        k_inv = pow(k, -1, self.order)
        s = (k_inv * (e + d_fake * r)) % self.order
        
        return r, s
    
    def forge_signature_chosen_message(self, target_public_key: VerifyingKey) -> Tuple[bytes, Tuple[int, int]]:
        """
        选择消息攻击 - 构造特定的消息和签名对
        
        数学原理：
        选择随机数u, v，计算：
        R = u*G + v*Q (其中Q是目标公钥)
        r = R.x mod n
        e = r*u*v^(-1) mod n
        s = r*v^(-1) mod n
        
        构造消息m使得Hash(m) = e
        
        Returns:
            (构造的消息, 伪造的签名)
        """
        # 选择随机参数
        u = secrets.randbelow(self.order - 1) + 1
        v = secrets.randbelow(self.order - 1) + 1
        
        # 获取目标公钥点
        Q = target_public_key.pubkey.point
        
        # 计算R = u*G + v*Q
        R = u * self.generator + v * Q
        r = R.x() % self.order
        
        # 计算e和s
        v_inv = pow(v, -1, self.order)
        e = (r * u * v_inv) % self.order
        s = (r * v_inv) % self.order
        
        # 构造消息使得Hash(m) = e
        # 这在实践中很困难（需要找到hash原像），这里只是理论演示
        # 我们构造一个特殊的消息，其hash接近目标值
        target_hash = e.to_bytes(32, 'big')
        message = b"Forged message with specific hash: " + target_hash[:16]
        
        return message, (r, s)
    
    def simulate_satoshi_signature(self, bitcoin_message: str = "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks") -> dict:
        """
        模拟中本聪风格的签名
        
        这个函数创建一个模拟的"中本聪"签名，使用与比特币创世块相关的消息。
        注意：这不是真正的中本聪签名，只是为了演示目的。
        
        Args:
            bitcoin_message: 比特币相关的消息（默认为创世块中的消息）
            
        Returns:
            包含签名信息的字典
        """
        # 生成一个"中本聪"密钥对（仅用于演示）
        satoshi_sk, satoshi_pk = self.sm2.generate_keypair()
        
        message_bytes = bitcoin_message.encode('utf-8')
        
        # 使用SM2进行签名
        signature = self.sm2.sign(satoshi_sk, message_bytes)
        
        # 验证签名
        is_valid = self.sm2.verify(satoshi_pk, message_bytes, signature)
        
        # 解析签名获取r, s值
        try:
            r, s = sigdecode_der(signature, self.order)
        except:
            r, s = 0, 0
        
        return {
            "message": bitcoin_message,
            "message_hash": hashlib.sha256(message_bytes).hexdigest(),
            "signature": {
                "r": hex(r),
                "s": hex(s),
                "der_encoded": signature.hex()
            },
            "public_key": satoshi_pk.to_string().hex(),
            "verification": is_valid,
            "note": "This is a simulated signature for educational purposes only"
        }
    
    def analyze_signature_security(self, signature_data: dict) -> dict:
        """
        分析签名的安全性
        
        检查签名中可能存在的安全风险：
        1. 随机数重用
        2. 弱随机数
        3. 签名延展性
        
        Args:
            signature_data: 签名数据字典
            
        Returns:
            安全性分析结果
        """
        analysis = {
            "security_level": "UNKNOWN",
            "risks": [],
            "recommendations": []
        }
        
        try:
            r = int(signature_data["signature"]["r"], 16)
            s = int(signature_data["signature"]["s"], 16)
            
            # 检查签名规范性
            if s > self.order // 2:
                analysis["risks"].append("签名使用高s值，存在延展性风险")
                analysis["recommendations"].append("使用规范化签名（低s值）")
            
            # 检查r值的随机性
            if r < self.order // 10:
                analysis["risks"].append("r值较小，可能存在弱随机数")
            
            # 检查s值的随机性
            if s < self.order // 10:
                analysis["risks"].append("s值较小，需要检查随机数质量")
            
            if len(analysis["risks"]) == 0:
                analysis["security_level"] = "GOOD"
                analysis["recommendations"].append("签名看起来是安全的")
            elif len(analysis["risks"]) <= 2:
                analysis["security_level"] = "MODERATE"
            else:
                analysis["security_level"] = "WEAK"
                
        except Exception as e:
            analysis["risks"].append(f"分析过程中发生错误: {str(e)}")
            analysis["security_level"] = "ERROR"
        
        return analysis
    
    def demonstrate_forge_techniques(self) -> dict:
        """
        演示各种签名伪造技术
        
        Returns:
            包含所有演示结果的字典
        """
        results = {
            "timestamp": hashlib.sha256(str(os.urandom(16)).encode()).hexdigest()[:16],
            "techniques": []
        }
        
        # 技术1：已知k的伪造
        print("演示技术1：已知随机数k的签名伪造")
        message1 = b"Bitcoin: A Peer-to-Peer Electronic Cash System"
        k = secrets.randbelow(self.order - 1) + 1
        r1, s1 = self.forge_signature_known_k(message1, k)
        
        results["techniques"].append({
            "name": "已知随机数k的伪造",
            "message": message1.decode(),
            "forged_signature": {"r": hex(r1), "s": hex(s1)},
            "description": "当攻击者知道签名中使用的随机数k时，可以构造有效的伪造签名"
        })
        
        # 技术2：中本聪风格签名模拟
        print("演示技术2：中本聪风格签名模拟")
        satoshi_sim = self.simulate_satoshi_signature()
        results["techniques"].append({
            "name": "中本聪风格签名模拟",
            "result": satoshi_sim,
            "description": "模拟创建与中本聪相关的消息签名（仅用于教育目的）"
        })
        
        # 技术3：安全性分析
        print("演示技术3：签名安全性分析")
        security_analysis = self.analyze_signature_security(satoshi_sim)
        results["techniques"].append({
            "name": "签名安全性分析",
            "analysis": security_analysis,
            "description": "分析数字签名中可能存在的安全风险"
        })
        
        return results


def main():
    """主演示函数"""
    print("中本聪数字签名伪造演示")
    print("=" * 60)
    print("警告：本演示仅用于教育和研究目的")
    print("请勿用于非法活动")
    print("=" * 60)
    
    forge = SatoshiSignatureForge()
    
    # 运行完整演示
    results = forge.demonstrate_forge_techniques()
    
    print(f"\n演示完成 - 会话ID: {results['timestamp']}")
    print(f"共演示了 {len(results['techniques'])} 种技术")
    
    # 显示详细结果
    for i, tech in enumerate(results['techniques'], 1):
        print(f"\n技术 {i}: {tech['name']}")
        print(f"描述: {tech['description']}")
        
        if 'forged_signature' in tech:
            print(f"伪造签名 r: {tech['forged_signature']['r']}")
            print(f"伪造签名 s: {tech['forged_signature']['s']}")
        
        if 'result' in tech and 'verification' in tech['result']:
            print(f"签名验证: {'通过' if tech['result']['verification'] else '失败'}")
        
        if 'analysis' in tech:
            print(f"安全等级: {tech['analysis']['security_level']}")
            if tech['analysis']['risks']:
                print("发现的风险:")
                for risk in tech['analysis']['risks']:
                    print(f"  - {risk}")
    
    return results


if __name__ == "__main__":
    main()
