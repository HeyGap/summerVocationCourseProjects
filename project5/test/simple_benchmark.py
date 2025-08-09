#!/usr/bin/env python3
# simple_benchmark.py
# SM2简化版本性能基准测试脚本

import os
import sys
import time
import statistics
import json
from typing import Dict, List

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sm2 import SM2
from sm2_opt_simple import SM2OptimizedSimple

class SimpleBenchmark:
    def __init__(self):
        self.sm2_basic = SM2()
        self.sm2_opt = SM2OptimizedSimple(
            enable_cache=True,
            enable_batch=True,
            enable_parallel=True
        )
        
    def benchmark_operation(self, sm2_instance, operation: str, iterations: int = 50) -> List[float]:
        """基准测试单个操作"""
        times = []
        test_message = b"Benchmark test message for SM2 optimization"
        
        # 预生成密钥对以避免每次都生成
        if operation != 'keygen':
            sk, vk = sm2_instance.generate_keypair()
            if operation in ['decrypt', 'verify']:
                # 预生成密文和签名
                ciphertext = sm2_instance.encrypt(vk, test_message)
                signature = sm2_instance.sign(sk, test_message)
        
        for _ in range(iterations):
            start = time.perf_counter()
            
            if operation == 'keygen':
                sm2_instance.generate_keypair()
            elif operation == 'encrypt':
                sm2_instance.encrypt(vk, test_message)
            elif operation == 'decrypt':
                sm2_instance.decrypt(sk, ciphertext)
            elif operation == 'sign':
                sm2_instance.sign(sk, test_message)
            elif operation == 'verify':
                sm2_instance.verify(vk, test_message, signature)
            
            times.append(time.perf_counter() - start)
            
        return times
    
    def run_comprehensive_benchmark(self, iterations: int = 50):
        """运行综合基准测试"""
        print("SM2 简化优化版本性能基准测试")
        print("="*60)
        print(f"测试迭代次数: {iterations}")
        print()
        
        operations = ['keygen', 'encrypt', 'decrypt', 'sign', 'verify']
        results = {}
        
        # 测试基础版本
        print("测试基础版本...")
        basic_results = {}
        for op in operations:
            print(f"  测试 {op}...", end=" ")
            times = self.benchmark_operation(self.sm2_basic, op, iterations)
            basic_results[op] = {
                'mean': statistics.mean(times),
                'std': statistics.stdev(times) if len(times) > 1 else 0,
                'min': min(times),
                'max': max(times),
            }
            print(f"完成 ({basic_results[op]['mean']*1000:.2f}ms)")
        
        results['basic'] = basic_results
        
        # 测试优化版本
        print("\n测试简化优化版本...")
        opt_results = {}
        for op in operations:
            print(f"  测试 {op}...", end=" ")
            times = self.benchmark_operation(self.sm2_opt, op, iterations)
            opt_results[op] = {
                'mean': statistics.mean(times),
                'std': statistics.stdev(times) if len(times) > 1 else 0,
                'min': min(times),
                'max': max(times),
                'speedup': basic_results[op]['mean'] / statistics.mean(times)
            }
            print(f"完成 ({opt_results[op]['mean']*1000:.2f}ms, {opt_results[op]['speedup']:.2f}x)")
        
        results['optimized'] = opt_results
        
        return results
    
    def print_detailed_results(self, results: Dict):
        """打印详细结果"""
        print("\n" + "="*80)
        print("详细性能对比结果")
        print("="*80)
        
        # 表头
        print(f"{'操作':<12} {'基础版本':<20} {'优化版本':<20} {'加速比':<10} {'改善':<10}")
        print("-" * 80)
        
        operations = ['keygen', 'encrypt', 'decrypt', 'sign', 'verify']
        total_basic_time = 0
        total_opt_time = 0
        
        for op in operations:
            basic = results['basic'][op]
            opt = results['optimized'][op]
            
            basic_ms = basic['mean'] * 1000
            opt_ms = opt['mean'] * 1000
            speedup = opt['speedup']
            improvement = ((basic['mean'] - opt['mean']) / basic['mean']) * 100
            
            total_basic_time += basic['mean']
            total_opt_time += opt['mean']
            
            print(f"{op:<12} {basic_ms:>8.2f}±{basic['std']*1000:>5.2f}ms "
                  f"{opt_ms:>8.2f}±{opt['std']*1000:>5.2f}ms "
                  f"{speedup:>8.2f}x {improvement:>8.1f}%")
        
        print("-" * 80)
        overall_speedup = total_basic_time / total_opt_time
        overall_improvement = ((total_basic_time - total_opt_time) / total_basic_time) * 100
        
        print(f"{'总体':<12} {total_basic_time*1000:>16.2f}ms "
              f"{total_opt_time*1000:>16.2f}ms "
              f"{overall_speedup:>8.2f}x {overall_improvement:>8.1f}%")
        
        # 优化统计
        print("\n优化技术统计:")
        stats = self.sm2_opt.get_performance_stats()
        print(f"  缓存启用: {stats['cache_enabled']}")
        print(f"  批量处理启用: {stats['batch_enabled']}")
        print(f"  并行处理启用: {stats['parallel_enabled']}")
        print(f"  线程池大小: {stats['thread_pool_size']}")
        print(f"  总操作数: {stats['total_operations']}")
    
    def test_batch_performance(self, batch_sizes: List[int] = [1, 5, 10, 20]):
        """测试批量操作性能"""
        print("\n" + "="*60)
        print("批量验证性能测试")
        print("="*60)
        
        test_message = b"Batch performance test message"
        
        print(f"{'批量大小':<10} {'单独验证(ms)':<15} {'批量验证(ms)':<15} {'加速比':<10}")
        print("-" * 60)
        
        for batch_size in batch_sizes:
            # 准备测试数据
            keypairs = [self.sm2_opt.generate_keypair() for _ in range(batch_size)]
            verifications = []
            
            for sk, vk in keypairs:
                signature = self.sm2_opt.sign(sk, test_message)
                verifications.append((vk, test_message, signature))
            
            # 测试单独验证
            start = time.perf_counter()
            individual_results = []
            for vk, data, sig in verifications:
                individual_results.append(self.sm2_opt.verify(vk, data, sig))
            individual_time = time.perf_counter() - start
            
            # 测试批量验证
            start = time.perf_counter()
            batch_results = self.sm2_opt.batch_verify(verifications)
            batch_time = time.perf_counter() - start
            
            # 验证结果一致性
            assert individual_results == batch_results, "批量验证结果不一致"
            
            speedup = individual_time / batch_time if batch_time > 0 else float('inf')
            
            print(f"{batch_size:<10} {individual_time*1000:>12.2f} {batch_time*1000:>12.2f} {speedup:>8.2f}x")
    
    def save_results(self, results: Dict, filename: str = "simple_benchmark_results.json"):
        """保存结果到文件"""
        # 转换为可序列化格式
        serializable = {}
        for version, version_results in results.items():
            serializable[version] = {}
            for op, op_results in version_results.items():
                serializable[version][op] = {
                    key: float(value) for key, value in op_results.items()
                }
        
        with open(filename, 'w') as f:
            json.dump(serializable, f, indent=2)
        
        print(f"\n结果已保存到: {filename}")

def main():
    print("启动 SM2 简化优化版本基准测试...")
    
    benchmark = SimpleBenchmark()
    
    # 运行主要基准测试
    results = benchmark.run_comprehensive_benchmark(iterations=30)
    
    # 打印详细结果
    benchmark.print_detailed_results(results)
    
    # 测试批量性能
    benchmark.test_batch_performance()
    
    # 保存结果
    benchmark.save_results(results)
    
    print("\n基准测试完成! 🎉")
    print("\n主要优化效果:")
    ops = ['keygen', 'encrypt', 'decrypt', 'sign', 'verify']
    avg_speedup = statistics.mean([results['optimized'][op]['speedup'] for op in ops])
    print(f"  平均加速比: {avg_speedup:.2f}x")
    
    best_op = max(ops, key=lambda x: results['optimized'][x]['speedup'])
    print(f"  最佳优化操作: {best_op} ({results['optimized'][best_op]['speedup']:.2f}x)")
    
    print(f"  优化技术: 缓存机制 + 并行处理 + 确定性签名 + 批量操作")

if __name__ == "__main__":
    main()
