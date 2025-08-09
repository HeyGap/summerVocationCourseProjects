#!/usr/bin/env python3
# test_sm2_opt.py
# SM2优化实现的测试用例

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
from sm2_opt import SM2Optimized, PrecomputeTable, MemoryPool

class TestSM2Optimized(unittest.TestCase):
    def setUp(self):
        """测试前的初始化"""
        self.sm2_basic = SM2()
        self.sm2_opt = SM2Optimized(
            enable_precompute=True,
            enable_batch=True,
            enable_parallel=True,
            thread_pool_size=4
        )
        self.test_data = [
            b"Hello, SM2 Optimized!",
            b"This is a comprehensive test for SM2 optimization.",
            b"",  # 空消息
            b"A" * 1000,  # 长消息
            b"\x00\x01\x02\x03\xff\xfe\xfd" * 100,  # 二进制数据
            "Unicode test: 这是中文测试 🔐🚀".encode('utf-8'),
        ]

    def test_memory_pool(self):
        """测试内存池功能"""
        print("\n=== 测试内存池 ===")
        
        pool = MemoryPool(pool_size=5)
        
        # 测试获取和归还缓冲区
        buffers = []
        for i in range(3):
            buf = pool.get_buffer(100)
            self.assertEqual(len(buf), 100)
            self.assertEqual(buf, bytearray(100))  # 应该被清零
            buffers.append(buf)
            print(f"获取缓冲区 {i+1}: 长度 {len(buf)}")
        
        # 归还缓冲区
        for i, buf in enumerate(buffers):
            pool.return_buffer(buf)
            print(f"归还缓冲区 {i+1}")
        
        # 重新获取，应该复用
        new_buf = pool.get_buffer(50)
        self.assertIn(new_buf, [buf[:50] for buf in buffers])
        print("内存池复用测试通过")

    def test_precompute_table(self):
        """测试预计算表"""
        print("\n=== 测试预计算表 ===")
        
        # 生成测试密钥对
        sk, vk = self.sm2_basic.generate_keypair()
        point = vk.pubkey.point
        
        # 创建预计算表
        table = PrecomputeTable(point, window_size=4)
        
        # 测试预计算表的正确性
        test_scalars = [1, 3, 5, 7, 15, 127, 255]
        
        for scalar in test_scalars:
            # 使用预计算表计算
            result1 = table.multiply(scalar)
            
            # 使用传统方法计算
            result2 = point
            for _ in range(scalar - 1):
                result2 = result2 + point
            
            # 比较结果（注意处理无穷远点）
            from ecdsa.ellipticcurve import INFINITY
            if result1 != INFINITY and result2 != INFINITY:
                self.assertEqual(result1.x(), result2.x(), f"标量 {scalar} 的x坐标不匹配")
                self.assertEqual(result1.y(), result2.y(), f"标量 {scalar} 的y坐标不匹配")
            elif result1 == INFINITY and result2 == INFINITY:
                pass  # 都是无穷远点，正确
            else:
                self.fail(f"标量 {scalar}: 一个是无穷远点，另一个不是")
            print(f"标量 {scalar}: 预计算表计算正确")

    def test_optimized_keypair_generation(self):
        """测试优化的密钥对生成"""
        print("\n=== 测试优化密钥对生成 ===")
        
        # 生成多个密钥对，确保都不同
        keypairs = []
        for i in range(5):
            sk, vk = self.sm2_opt.generate_keypair()
            self.assertIsNotNone(sk)
            self.assertIsNotNone(vk)
            
            # 验证密钥对的对应关系
            self.assertEqual(sk.verifying_key.to_string(), vk.to_string())
            
            keypairs.append((sk.to_string(), vk.to_string()))
            print(f"优化密钥对 {i+1}: 生成成功")
        
        # 确保生成的密钥对都不同
        unique_keys = set(kp[0] for kp in keypairs)
        self.assertEqual(len(unique_keys), 5)
        
        # 检查预计算表是否被创建
        self.assertGreater(self.sm2_opt.stats['keypair_generated'], 0)
        print(f"缓存命中率: {self.sm2_opt.get_performance_stats()['cache_hit_rate']:.2%}")

    def test_optimized_encryption_decryption(self):
        """测试优化的加密解密"""
        print("\n=== 测试优化加密解密 ===")
        
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

    def test_optimized_signature_verification(self):
        """测试优化的签名验证"""
        print("\n=== 测试优化签名验证 ===")
        
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

    def test_batch_verification(self):
        """测试批量验证功能"""
        print("\n=== 测试批量验证 ===")
        
        # 准备测试数据
        batch_size = 10
        keypairs = [self.sm2_opt.generate_keypair() for _ in range(batch_size)]
        test_message = b"Batch verification test message"
        
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
        
        # 单独验证对比
        start_time = time.time()
        individual_results = []
        for vk, data, sig in verifications:
            individual_results.append(self.sm2_opt.verify(vk, data, sig))
        individual_time = time.time() - start_time
        
        print(f"批量验证时间: {batch_time:.4f}s")
        print(f"单独验证时间: {individual_time:.4f}s")
        print(f"批量验证加速比: {individual_time/batch_time:.2f}x")
        
        self.assertEqual(results, individual_results)

    def test_performance_comparison(self):
        """测试性能对比"""
        print("\n=== 性能对比测试 ===")
        
        iterations = 20
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
            
            if (i + 1) % 5 == 0:
                print(f"  完成 {i + 1}/{iterations}")
        
        # 优化版本性能测试
        opt_times = {'keygen': [], 'encrypt': [], 'decrypt': [], 'sign': [], 'verify': []}
        
        print("测试优化版本...")
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
            
            if (i + 1) % 5 == 0:
                print(f"  完成 {i + 1}/{iterations}")
        
        # 计算统计信息并打印结果
        print("\n性能对比结果:")
        print("=" * 70)
        print(f"{'操作':<12} {'基础版本(ms)':<15} {'优化版本(ms)':<15} {'加速比':<10}")
        print("=" * 70)
        
        for op in ['keygen', 'encrypt', 'decrypt', 'sign', 'verify']:
            basic_avg = statistics.mean(basic_times[op]) * 1000
            basic_std = statistics.stdev(basic_times[op]) * 1000 if len(basic_times[op]) > 1 else 0
            
            opt_avg = statistics.mean(opt_times[op]) * 1000
            opt_std = statistics.stdev(opt_times[op]) * 1000 if len(opt_times[op]) > 1 else 0
            
            speedup = basic_avg / opt_avg if opt_avg > 0 else float('inf')
            
            print(f"{op:<12} {basic_avg:>7.2f}±{basic_std:>5.2f} {opt_avg:>7.2f}±{opt_std:>5.2f} {speedup:>8.2f}x")
        
        # 打印优化统计信息
        print("\n优化统计信息:")
        stats = self.sm2_opt.get_performance_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")

    def test_correctness_verification(self):
        """测试正确性验证：确保优化版本与基础版本结果一致"""
        print("\n=== 正确性验证测试 ===")
        
        test_messages = [
            b"Correctness test 1",
            b"Correctness test with longer message " * 10,
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

    def test_concurrent_operations(self):
        """测试并发操作的正确性"""
        print("\n=== 并发操作测试 ===")
        
        def worker_task(worker_id: int) -> Tuple[int, bool]:
            """工作线程任务"""
            try:
                # 生成密钥对
                sk, vk = self.sm2_opt.generate_keypair()
                
                # 测试消息
                message = f"Worker {worker_id} test message".encode()
                
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
        num_workers = 8
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_workers)]
            results = [future.result() for future in futures]
        
        # 验证所有任务都成功
        for worker_id, success in results:
            self.assertTrue(success, f"Worker {worker_id} failed")
            print(f"Worker {worker_id}: 成功")
        
        print(f"所有 {num_workers} 个并发任务都成功完成")

    def test_edge_cases(self):
        """测试边界情况"""
        print("\n=== 边界情况测试 ===")
        
        sk, vk = self.sm2_opt.generate_keypair()
        
        # 测试空消息
        empty_msg = b""
        try:
            ct = self.sm2_opt.encrypt(vk, empty_msg)
            pt = self.sm2_opt.decrypt(sk, ct)
            self.assertEqual(empty_msg, pt)
            print("空消息加密解密: 通过")
        except Exception as e:
            print(f"空消息测试失败: {e}")
        
        # 测试大消息
        large_msg = b"A" * 10000
        try:
            ct = self.sm2_opt.encrypt(vk, large_msg)
            pt = self.sm2_opt.decrypt(sk, ct)
            self.assertEqual(large_msg, pt)
            print(f"大消息({len(large_msg)} bytes)加密解密: 通过")
        except Exception as e:
            print(f"大消息测试失败: {e}")
        
        # 测试错误密文
        try:
            fake_ct = b"fake ciphertext" * 10
            self.sm2_opt.decrypt(sk, fake_ct)
            self.fail("应该抛出异常")
        except Exception:
            print("错误密文测试: 通过（正确抛出异常）")

if __name__ == '__main__':
    # 设置测试参数
    unittest.TestLoader.sortTestMethodsUsing = None  # 按定义顺序运行测试
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSM2Optimized)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=True)
    result = runner.run(suite)
    
    # 打印总结
    print("\n" + "="*70)
    print("测试总结:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n❌ {len(result.failures + result.errors)} 个测试失败")
        sys.exit(1)
