#!/usr/bin/env python3
# test_sm2.py
# SM2基础实现的测试用例

import unittest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from sm2 import SM2

class TestSM2(unittest.TestCase):
    def setUp(self):
        """测试前的初始化"""
        self.sm2 = SM2()
        self.test_data = [
            b"Hello, SM2!",
            b"This is a test message for SM2 encryption and signature.",
            b"",  # 空消息
            b"A" * 100,  # 长消息
            b"\x00\x01\x02\x03\xff\xfe\xfd",  # 二进制数据
        ]

    def test_keypair_generation(self):
        """测试密钥对生成"""
        print("\n=== 测试密钥对生成 ===")
        
        # 生成多个密钥对，确保每次都不同
        keypairs = []
        for i in range(5):
            sk, vk = self.sm2.generate_keypair()
            self.assertIsNotNone(sk, "私钥不应为空")
            self.assertIsNotNone(vk, "公钥不应为空")
            
            # 验证密钥对的对应关系
            self.assertEqual(sk.verifying_key.to_string(), vk.to_string(), 
                           "私钥对应的公钥应与生成的公钥相同")
            
            keypairs.append((sk.to_string(), vk.to_string()))
            print(f"密钥对 {i+1}: 私钥长度={len(sk.to_string())}, 公钥长度={len(vk.to_string())}")
        
        # 确保生成的密钥对都不同
        unique_private_keys = set(kp[0] for kp in keypairs)
        unique_public_keys = set(kp[1] for kp in keypairs)
        self.assertEqual(len(unique_private_keys), 5, "生成的私钥应该都不同")
        self.assertEqual(len(unique_public_keys), 5, "生成的公钥应该都不同")

    def test_encryption_decryption(self):
        """测试加密解密功能"""
        print("\n=== 测试加密解密 ===")
        
        sk, vk = self.sm2.generate_keypair()
        
        for i, data in enumerate(self.test_data):
            with self.subTest(test_case=i, data_length=len(data)):
                print(f"测试数据 {i+1}: 长度={len(data)}")
                
                # 加密
                try:
                    ciphertext = self.sm2.encrypt(vk, data)
                    self.assertIsNotNone(ciphertext, "密文不应为空")
                    self.assertNotEqual(ciphertext, data, "密文不应等于原文")
                    print(f"  加密成功，密文长度: {len(ciphertext)}")
                    
                    # 解密
                    decrypted = self.sm2.decrypt(sk, ciphertext)
                    self.assertEqual(decrypted, data, "解密结果应等于原始数据")
                    print(f"  解密成功，原文匹配")
                    
                except Exception as e:
                    self.fail(f"加密/解密过程中出现异常: {e}")

    def test_encryption_with_different_keys(self):
        """测试使用不同密钥加密解密"""
        print("\n=== 测试不同密钥加密解密 ===")
        
        sk1, vk1 = self.sm2.generate_keypair()
        sk2, vk2 = self.sm2.generate_keypair()
        
        data = b"Test message for different keys"
        
        # 用第一个公钥加密
        ciphertext = self.sm2.encrypt(vk1, data)
        
        # 用对应的私钥解密应该成功
        decrypted1 = self.sm2.decrypt(sk1, ciphertext)
        self.assertEqual(decrypted1, data, "用对应私钥解密应该成功")
        print("用对应私钥解密: 成功")
        
        # 用不同的私钥解密应该失败或得到错误结果
        try:
            decrypted2 = self.sm2.decrypt(sk2, ciphertext)
            self.assertNotEqual(decrypted2, data, "用不同私钥解密应该得到不同结果")
            print("用不同私钥解密: 得到不同结果（预期）")
        except Exception as e:
            print(f"用不同私钥解密: 抛出异常（预期）- {type(e).__name__}")

    def test_signature_verification(self):
        """测试数字签名和验证"""
        print("\n=== 测试数字签名和验证 ===")
        
        sk, vk = self.sm2.generate_keypair()
        
        for i, data in enumerate(self.test_data):
            with self.subTest(test_case=i, data_length=len(data)):
                print(f"测试数据 {i+1}: 长度={len(data)}")
                
                # 签名
                try:
                    signature = self.sm2.sign(sk, data)
                    self.assertIsNotNone(signature, "签名不应为空")
                    self.assertGreater(len(signature), 0, "签名长度应大于0")
                    print(f"  签名成功，签名长度: {len(signature)}")
                    
                    # 验证签名
                    is_valid = self.sm2.verify(vk, data, signature)
                    self.assertTrue(is_valid, "签名验证应该成功")
                    print(f"  验签成功")
                    
                except Exception as e:
                    self.fail(f"签名/验签过程中出现异常: {e}")

    def test_signature_with_wrong_data(self):
        """测试篡改数据后的签名验证"""
        print("\n=== 测试数据篡改后的签名验证 ===")
        
        sk, vk = self.sm2.generate_keypair()
        original_data = b"Original message"
        tampered_data = b"Tampered message"
        
        # 对原始数据签名
        signature = self.sm2.sign(sk, original_data)
        
        # 验证原始数据的签名
        self.assertTrue(self.sm2.verify(vk, original_data, signature), 
                       "原始数据的签名验证应该成功")
        print("原始数据签名验证: 成功")
        
        # 验证篡改数据的签名
        self.assertFalse(self.sm2.verify(vk, tampered_data, signature), 
                        "篡改数据的签名验证应该失败")
        print("篡改数据签名验证: 失败（预期）")

    def test_signature_with_wrong_key(self):
        """测试使用错误密钥验证签名"""
        print("\n=== 测试错误密钥验证签名 ===")
        
        sk1, vk1 = self.sm2.generate_keypair()
        sk2, vk2 = self.sm2.generate_keypair()
        
        data = b"Test message for wrong key verification"
        
        # 用第一个私钥签名
        signature = self.sm2.sign(sk1, data)
        
        # 用对应公钥验证应该成功
        self.assertTrue(self.sm2.verify(vk1, data, signature), 
                       "用对应公钥验证应该成功")
        print("用对应公钥验证: 成功")
        
        # 用不同公钥验证应该失败
        self.assertFalse(self.sm2.verify(vk2, data, signature), 
                        "用不同公钥验证应该失败")
        print("用不同公钥验证: 失败（预期）")

    def test_signature_with_corrupted_signature(self):
        """测试损坏的签名"""
        print("\n=== 测试损坏的签名 ===")
        
        sk, vk = self.sm2.generate_keypair()
        data = b"Test message for corrupted signature"
        
        signature = self.sm2.sign(sk, data)
        
        # 损坏签名
        if len(signature) > 1:
            corrupted_signature = signature[:-1] + b'\x00'
        else:
            corrupted_signature = b'\x00'
        
        # 验证损坏的签名应该失败
        self.assertFalse(self.sm2.verify(vk, data, corrupted_signature), 
                        "损坏的签名验证应该失败")
        print("损坏签名验证: 失败（预期）")

    def test_consistency(self):
        """测试一致性：多次操作应得到一致结果"""
        print("\n=== 测试操作一致性 ===")
        
        sk, vk = self.sm2.generate_keypair()
        data = b"Consistency test message"
        
        # 多次签名同一数据
        signatures = []
        for i in range(3):
            sig = self.sm2.sign(sk, data)
            signatures.append(sig)
            # 每个签名都应该能够验证成功
            self.assertTrue(self.sm2.verify(vk, data, sig), 
                           f"第{i+1}次签名验证应该成功")
        
        print(f"生成了{len(signatures)}个签名，所有签名都验证成功")
        
        # 多次加密同一数据
        ciphertexts = []
        for i in range(3):
            ct = self.sm2.encrypt(vk, data)
            ciphertexts.append(ct)
            # 每个密文都应该能够解密成功
            pt = self.sm2.decrypt(sk, ct)
            self.assertEqual(pt, data, f"第{i+1}次加密的解密应该成功")
        
        print(f"生成了{len(ciphertexts)}个密文，所有密文都解密成功")

def run_performance_test():
    """简单的性能测试"""
    print("\n" + "="*50)
    print("性能测试")
    print("="*50)
    
    import time
    
    sm2 = SM2()
    data = b"Performance test message" * 10  # 更长的测试数据
    
    # 密钥生成性能
    start_time = time.time()
    keypairs = []
    for i in range(10):
        keypairs.append(sm2.generate_keypair())
    keygen_time = time.time() - start_time
    print(f"密钥生成: 10次耗时 {keygen_time:.4f}秒, 平均 {keygen_time/10:.4f}秒/次")
    
    sk, vk = keypairs[0]
    
    # 加密性能
    start_time = time.time()
    ciphertexts = []
    for i in range(100):
        ciphertexts.append(sm2.encrypt(vk, data))
    encrypt_time = time.time() - start_time
    print(f"加密: 100次耗时 {encrypt_time:.4f}秒, 平均 {encrypt_time/100:.6f}秒/次")
    
    # 解密性能
    start_time = time.time()
    for ct in ciphertexts:
        sm2.decrypt(sk, ct)
    decrypt_time = time.time() - start_time
    print(f"解密: 100次耗时 {decrypt_time:.4f}秒, 平均 {decrypt_time/100:.6f}秒/次")
    
    # 签名性能
    start_time = time.time()
    signatures = []
    for i in range(100):
        signatures.append(sm2.sign(sk, data))
    sign_time = time.time() - start_time
    print(f"签名: 100次耗时 {sign_time:.4f}秒, 平均 {sign_time/100:.6f}秒/次")
    
    # 验签性能
    start_time = time.time()
    for sig in signatures:
        sm2.verify(vk, data, sig)
    verify_time = time.time() - start_time
    print(f"验签: 100次耗时 {verify_time:.4f}秒, 平均 {verify_time/100:.6f}秒/次")

if __name__ == '__main__':
    print("SM2 基础实现测试")
    print("="*50)
    
    # 检查依赖
    try:
        import ecdsa
        from Crypto.Cipher import AES
        print("✓ 所需依赖库已安装")
    except ImportError as e:
        print(f"✗ 缺少依赖库: {e}")
        print("请运行: pip install ecdsa pycryptodome")
        sys.exit(1)
    
    # 运行单元测试
    unittest.main(verbosity=2, exit=False)
    
    # 运行性能测试
    try:
        run_performance_test()
    except Exception as e:
        print(f"性能测试失败: {e}")
    
    print("\n测试完成!")
