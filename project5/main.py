#!/usr/bin/env python3
"""
SM2 密码算法实现项目主程序
提供命令行接口来演示和测试SM2算法功能
"""

import os
import sys
import argparse

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sm2 import SM2
from sm2_opt_simple import SM2OptimizedSimple

def demo_basic():
    """演示基础SM2功能"""
    print("SM2 基础实现演示")
    print("=" * 50)
    
    # 初始化
    sm2 = SM2()
    
    # 生成密钥对
    print("1. 生成密钥对...")
    sk, vk = sm2.generate_keypair()
    print(f"   私钥长度: {len(sk.to_string())} bytes")
    print(f"   公钥长度: {len(vk.to_string())} bytes")
    
    # 测试消息
    message = b"Hello, SM2 Cryptography!"
    print(f"\n2. 原始消息: {message}")
    
    # 加密演示
    print("\n3. 公钥加密...")
    ciphertext = sm2.encrypt(vk, message)
    print(f"   密文长度: {len(ciphertext)} bytes")
    print(f"   密文 (hex): {ciphertext.hex()[:64]}...")
    
    # 解密演示
    print("\n4. 私钥解密...")
    decrypted = sm2.decrypt(sk, ciphertext)
    print(f"   解密结果: {decrypted}")
    print(f"   解密成功: {decrypted == message}")
    
    # 签名演示
    print("\n5. 数字签名...")
    signature = sm2.sign(sk, message)
    print(f"   签名长度: {len(signature)} bytes")
    print(f"   签名 (hex): {signature.hex()}")
    
    # 验签演示
    print("\n6. 签名验证...")
    is_valid = sm2.verify(vk, message, signature)
    print(f"   验证结果: {is_valid}")
    
    # 篡改测试
    print("\n7. 篡改检测测试...")
    tampered_message = b"Tampered message!"
    is_tampered_valid = sm2.verify(vk, tampered_message, signature)
    print(f"   篡改消息验证: {is_tampered_valid} (应为False)")

def demo_optimized():
    """演示优化版SM2功能"""
    print("SM2 优化实现演示")
    print("=" * 50)
    
    # 初始化优化版本
    sm2_opt = SM2OptimizedSimple(
        enable_cache=True,
        enable_batch=True,
        enable_parallel=True
    )
    
    # 生成密钥对
    print("1. 生成密钥对...")
    sk, vk = sm2_opt.generate_keypair()
    print(f"   私钥长度: {len(sk.to_string())} bytes")
    print(f"   公钥长度: {len(vk.to_string())} bytes")
    
    # 测试消息
    message = b"Hello, Optimized SM2!"
    print(f"\n2. 原始消息: {message}")
    
    # 加密演示
    print("\n3. 优化加密...")
    ciphertext = sm2_opt.encrypt(vk, message)
    print(f"   密文长度: {len(ciphertext)} bytes")
    
    # 解密演示
    print("\n4. 优化解密...")
    decrypted = sm2_opt.decrypt(sk, ciphertext)
    print(f"   解密结果: {decrypted}")
    print(f"   解密成功: {decrypted == message}")
    
    # 签名演示
    print("\n5. 确定性签名...")
    signature = sm2_opt.sign(sk, message)
    print(f"   签名长度: {len(signature)} bytes")
    
    # 验签演示
    print("\n6. 签名验证...")
    is_valid = sm2_opt.verify(vk, message, signature)
    print(f"   验证结果: {is_valid}")
    
    # 批量验证演示
    print("\n7. 批量验证演示...")
    keypairs = [sm2_opt.generate_keypair() for _ in range(5)]
    verifications = []
    
    for i, (sk_i, vk_i) in enumerate(keypairs):
        test_msg = f"Batch message {i}".encode()
        sig_i = sm2_opt.sign(sk_i, test_msg)
        verifications.append((vk_i, test_msg, sig_i))
    
    batch_results = sm2_opt.batch_verify(verifications)
    print(f"   批量验证结果: {sum(batch_results)}/{len(batch_results)} 成功")
    
    # 性能统计
    print("\n8. 性能统计...")
    stats = sm2_opt.get_performance_stats()
    print(f"   密钥生成次数: {stats['keypair_generated']}")
    print(f"   加密次数: {stats['encryptions']}")
    print(f"   解密次数: {stats['decryptions']}")
    print(f"   签名次数: {stats['signatures']}")
    print(f"   验证次数: {stats['verifications']}")
    print(f"   总操作数: {stats['total_operations']}")

def run_tests():
    """运行所有测试"""
    print("运行SM2测试套件")
    print("=" * 50)
    
    test_files = [
        "test/test_sm2.py",
        "test/test_sm2_simple.py",
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n运行 {test_file}...")
            os.system(f"python {test_file}")
        else:
            print(f"测试文件 {test_file} 不存在")

def run_benchmark():
    """运行性能基准测试"""
    print("运行SM2性能基准测试")
    print("=" * 50)
    
    benchmark_file = "test/simple_benchmark.py"
    if os.path.exists(benchmark_file):
        os.system(f"python {benchmark_file}")
    else:
        print(f"基准测试文件 {benchmark_file} 不存在")

def main():
    parser = argparse.ArgumentParser(description="SM2密码算法实现项目")
    parser.add_argument("command", choices=["demo", "demo-opt", "test", "benchmark"], 
                       help="执行命令")
    
    args = parser.parse_args()
    
    if args.command == "demo":
        demo_basic()
    elif args.command == "demo-opt":
        demo_optimized()
    elif args.command == "test":
        run_tests()
    elif args.command == "benchmark":
        run_benchmark()

if __name__ == "__main__":
    main()
