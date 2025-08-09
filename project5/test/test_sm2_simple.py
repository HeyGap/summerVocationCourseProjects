#!/usr/bin/env python3
# test_sm2_simple.py
# SM2简化优化实现的测试用例

import unittest
import time
import os
import sys
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sm2 import SM2
from sm2_opt_simple import SM2OptimizedSimple

class TestSM2Simple(unittest.TestCase):
    def setUp(self):
        """测试前的初始化"""
        self.sm2_basic = SM2()
        self.sm2_opt = SM2OptimizedSimple(
            enable_cache=True,
            enable_batch=True,
            enable_parallel=True,
            thread_pool_size=4
        )
        self.test_data = [
            b"Hello, SM2 Simple!",
            b"This is a simple test for SM2 optimization.",
            b"",  # 空消息
            b"A" * 100,  # 长消息
            b"\x00\x01\x02\x03\xff\xfe\xfd",  # 二进制数据
            "Unicode test: 简单测试 🚀".encode('utf-8'),
        ]

    def test_simple_keypair_generation(self):
        """测试简化优化的密钥对生成"""
        print("\n=== 测试简化优化密钥对生成 ===")
        
        keypairs = []
        for i in range(5):
            sk, vk = self.sm2_opt.generate_keypair()
            self.assertIsNotNone(sk)
            self.assertIsNotNone(vk)
            
            keypairs.append((sk.to_string(), vk.to_string()))
            print(f"优化密钥对 {i+1}: 生成成功")
        
        # 确保生成的密钥对都不同
        unique_keys = set(kp[0] for kp in keypairs)
        self.assertEqual(len(unique_keys), 5)
        
        print(f"生成统计: {self.sm2_opt.stats['keypair_generated']}")

    def test_simple_encryption_decryption(self):
        """测试简化优化的加密解密"""
        print("\n=== 测试简化优化加密解密 ===")
        
        sk, vk = self.sm2_opt.generate_keypair()
        
        for i, data in enumerate(self.test_data):
            print(f"测试数据 {i+1}: 长度 {len(data)} bytes")
            
            # 加密
            start_time = time.time()
            ciphertext = self.sm2_opt.encrypt(vk, data)
            encrypt_time = time.time() - start_time
            
            self.assertIsInstance(ciphertext, bytes)
            self.assertGreater(len(ciphertext), len(data))
            
            # 解密
            start_time = time.time()
            decrypted = self.sm2_opt.decrypt(sk, ciphertext)
            decrypt_time = time.time() - start_time
            
            self.assertEqual(data, decrypted)
            print(f"  加密时间: {encrypt_time:.4f}s, 解密时间: {decrypt_time:.4f}s")

    def test_simple_signature_verification(self):
        """测试简化优化的签名验证"""
        print("\n=== 测试简化优化签名验证 ===")
        
        sk, vk = self.sm2_opt.generate_keypair()
        
        for i, data in enumerate(self.test_data):
            print(f"测试数据 {i+1}: 长度 {len(data)} bytes")
            
            # 签名
            start_time = time.time()
            signature = self.sm2_opt.sign(sk, data)
            sign_time = time.time() - start_time
            
            self.assertIsInstance(signature, bytes)
            self.assertGreater(len(signature), 0)
            
            # 验证
            start_time = time.time()
            is_valid = self.sm2_opt.verify(vk, data, signature)
            verify_time = time.time() - start_time
            
            self.assertTrue(is_valid)
            
            # 测试错误签名
            wrong_sig = b'wrong' + signature[5:]
            is_invalid = self.sm2_opt.verify(vk, data, wrong_sig)
            self.assertFalse(is_invalid)
            
            print(f"  签名时间: {sign_time:.4f}s, 验证时间: {verify_time:.4f}s")

    def test_simple_batch_verification(self):
        """测试简化批量验证功能"""
        print("\n=== 测试简化批量验证 ===")
        
        batch_size = 10
        keypairs = [self.sm2_opt.generate_keypair() for _ in range(batch_size)]
        test_message = b"Simple batch verification test"
        
        # 生成签名
        verifications = []
        for sk, vk in keypairs:
            signature = self.sm2_opt.sign(sk, test_message)
            verifications.append((vk, test_message, signature))
        
        # 批量验证
        start_time = time.time()
        results = self.sm2_opt.batch_verify(verifications)
        batch_time = time.time() - start_time
        
        # 验证结果
        self.assertEqual(len(results), batch_size)
        self.assertTrue(all(results))
        
        print(f"批量验证时间: {batch_time:.4f}s")
        print(f"平均每个验证: {batch_time/batch_size:.4f}s")

    def test_simple_performance_comparison(self):
        """测试简化版性能对比"""
        print("\n=== 简化版性能对比测试 ===")
        
        iterations = 10
        test_message = b"Performance test message"
        
        # 基础版本性能测试
        basic_times = {'keygen': [], 'encrypt': [], 'decrypt': [], 'sign': [], 'verify': []}
        
        print("测试基础版本...")
        for i in range(iterations):
            # 密钥生成
            start = time.time()
            sk_basic, vk_basic = self.sm2_basic.generate_keypair()
            basic_times['keygen'].append(time.time() - start)
            
            # 加密
            start = time.time()
            ct_basic = self.sm2_basic.encrypt(vk_basic, test_message)
            basic_times['encrypt'].append(time.time() - start)
            
            # 解密
            start = time.time()
            pt_basic = self.sm2_basic.decrypt(sk_basic, ct_basic)
            basic_times['decrypt'].append(time.time() - start)
            
            # 签名
            start = time.time()
            sig_basic = self.sm2_basic.sign(sk_basic, test_message)
            basic_times['sign'].append(time.time() - start)
            
            # 验证
            start = time.time()
            self.sm2_basic.verify(vk_basic, test_message, sig_basic)
            basic_times['verify'].append(time.time() - start)
        
        # 优化版本性能测试
        opt_times = {'keygen': [], 'encrypt': [], 'decrypt': [], 'sign': [], 'verify': []}
        
        print("测试简化优化版本...")
        for i in range(iterations):
            # 密钥生成
            start = time.time()
            sk_opt, vk_opt = self.sm2_opt.generate_keypair()
            opt_times['keygen'].append(time.time() - start)
            
            # 加密
            start = time.time()
            ct_opt = self.sm2_opt.encrypt(vk_opt, test_message)
            opt_times['encrypt'].append(time.time() - start)
            
            # 解密
            start = time.time()
            pt_opt = self.sm2_opt.decrypt(sk_opt, ct_opt)
            opt_times['decrypt'].append(time.time() - start)
            
            # 签名
            start = time.time()
            sig_opt = self.sm2_opt.sign(sk_opt, test_message)
            opt_times['sign'].append(time.time() - start)
            
            # 验证
            start = time.time()
            self.sm2_opt.verify(vk_opt, test_message, sig_opt)
            opt_times['verify'].append(time.time() - start)
        
        # 计算统计信息并打印结果
        print("\n简化版性能对比结果:")
        print("=" * 60)
        print(f"{'操作':<10} {'基础版本(ms)':<15} {'优化版本(ms)':<15} {'加速比':<10}")
        print("=" * 60)
        
        for op in ['keygen', 'encrypt', 'decrypt', 'sign', 'verify']:
            basic_avg = statistics.mean(basic_times[op]) * 1000
            opt_avg = statistics.mean(opt_times[op]) * 1000
            speedup = basic_avg / opt_avg if opt_avg > 0 else float('inf')
            
            print(f"{op:<10} {basic_avg:>10.2f} {opt_avg:>10.2f} {speedup:>8.2f}x")
        
        # 打印优化统计信息
        print("\n优化统计信息:")
        stats = self.sm2_opt.get_performance_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")

    def test_simple_correctness(self):
        """测试简化版正确性"""
        print("\n=== 简化版正确性验证 ===")
        
        test_messages = [
            b"Correctness test 1",
            b"Correctness test 2 with more data",
            b"",
            b"\x00\x01\x02\xff\xfe\xfd"
        ]
        
        for i, message in enumerate(test_messages):
            print(f"测试消息 {i+1}: 长度 {len(message)}")
            
            # 基础版本
            sk_basic, vk_basic = self.sm2_basic.generate_keypair()
            ct_basic = self.sm2_basic.encrypt(vk_basic, message)
            pt_basic = self.sm2_basic.decrypt(sk_basic, ct_basic)
            sig_basic = self.sm2_basic.sign(sk_basic, message)
            verify_basic = self.sm2_basic.verify(vk_basic, message, sig_basic)
            
            # 优化版本
            sk_opt, vk_opt = self.sm2_opt.generate_keypair()
            ct_opt = self.sm2_opt.encrypt(vk_opt, message)
            pt_opt = self.sm2_opt.decrypt(sk_opt, ct_opt)
            sig_opt = self.sm2_opt.sign(sk_opt, message)
            verify_opt = self.sm2_opt.verify(vk_opt, message, sig_opt)
            
            # 验证解密结果
            self.assertEqual(message, pt_basic, "基础版本解密失败")
            self.assertEqual(message, pt_opt, "优化版本解密失败")
            
            # 验证签名结果
            self.assertTrue(verify_basic, "基础版本验签失败")
            self.assertTrue(verify_opt, "优化版本验签失败")
            
            print(f"  正确性验证通过")

    def test_simple_concurrent_operations(self):
        """测试简化版并发操作"""
        print("\n=== 简化版并发操作测试 ===")
        
        def worker_task(worker_id: int) -> Tuple[int, bool]:
            """工作线程任务"""
            try:
                # 生成密钥对
                sk, vk = self.sm2_opt.generate_keypair()
                
                # 测试消息
                message = f"Worker {worker_id} test".encode()
                
                # 加密解密
                ciphertext = self.sm2_opt.encrypt(vk, message)
                decrypted = self.sm2_opt.decrypt(sk, ciphertext)
                
                if decrypted != message:
                    return worker_id, False
                
                # 签名验证
                signature = self.sm2_opt.sign(sk, message)
                is_valid = self.sm2_opt.verify(vk, message, signature)
                
                return worker_id, is_valid
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                return worker_id, False
        
        # 启动多个并发任务
        num_workers = 4
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_workers)]
            results = [future.result() for future in futures]
        
        # 验证所有任务都成功
        for worker_id, success in results:
            self.assertTrue(success, f"Worker {worker_id} failed")
            print(f"Worker {worker_id}: 成功")
        
        print(f"所有 {num_workers} 个并发任务都成功完成")

if __name__ == '__main__':
    # 设置测试参数
    unittest.TestLoader.sortTestMethodsUsing = None
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSM2Simple)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=True)
    result = runner.run(suite)
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n❌ {len(result.failures + result.errors)} 个测试失败")
        if result.failures:
            print("失败的测试:")
            for test, traceback in result.failures:
                print(f"- {test}")
        if result.errors:
            print("错误的测试:")
            for test, traceback in result.errors:
                print(f"- {test}")
        sys.exit(1)
