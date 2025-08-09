"""
高级示例：演示协议的各种使用场景
"""

from src.pis_protocol import PISProtocol
import json


def advanced_example():
    """
    高级示例：模拟实际应用场景
    """
    print("=" * 80)
    print("基于DDH的私有交集求和协议 - 高级示例")
    print("=" * 80)
    
    # 场景1: 银行间反洗钱协作
    print("\n场景1: 银行间反洗钱协作")
    print("-" * 50)
    print("银行A想知道与银行B的可疑账户交集数量")
    print("银行B想知道共同可疑账户的风险评分总和")
    
    bank_a_accounts = ["acc_001", "acc_023", "acc_045", "acc_067", "acc_089"]
    bank_b_data = [
        ("acc_001", 85),  # 高风险
        ("acc_023", 65),  # 中等风险  
        ("acc_102", 45),  # 低风险
        ("acc_045", 90),  # 高风险
        ("acc_156", 30)   # 低风险
    ]
    
    protocol = PISProtocol()
    intersection_size, risk_score_sum = protocol.run_protocol(bank_a_accounts, bank_b_data)
    
    print(f"\n结果:")
    print(f"共同可疑账户数量: {intersection_size}")
    print(f"共同账户总风险评分: {risk_score_sum}")
    
    # 场景2: 广告投放交集分析
    print("\n" + "="*80)
    print("场景2: 广告平台用户交集分析")  
    print("-" * 50)
    print("平台A想知道与平台B的重叠用户数")
    print("平台B想知道重叠用户的总价值")
    
    platform_a_users = ["user_alice", "user_bob", "user_charlie", "user_david", 
                        "user_eve", "user_frank", "user_grace"]
    platform_b_data = [
        ("user_alice", 1250),    # 高价值用户
        ("user_bob", 800),       # 中等价值
        ("user_henry", 600),     # 中等价值  
        ("user_david", 1500),    # 高价值用户
        ("user_ian", 400),       # 低价值
        ("user_grace", 950)      # 中等价值
    ]
    
    protocol2 = PISProtocol()
    overlap_users, total_value = protocol2.run_protocol(platform_a_users, platform_b_data)
    
    print(f"\n结果:")
    print(f"重叠用户数: {overlap_users}")  
    print(f"重叠用户总价值: {total_value}")
    
    # 场景3: 大规模数据测试
    print("\n" + "="*80)
    print("场景3: 大规模数据性能测试")
    print("-" * 50)
    
    # 生成大量测试数据
    large_set_a = [f"item_{i:05d}" for i in range(1000)]
    large_set_b = [(f"item_{i:05d}", i * 10) for i in range(500, 1500)]
    
    print(f"集合A大小: {len(large_set_a)}")
    print(f"集合B大小: {len(large_set_b)}")
    
    import time
    start_time = time.time()
    
    protocol3 = PISProtocol()
    large_intersection_size, large_sum = protocol3.run_protocol(large_set_a, large_set_b)
    
    end_time = time.time()
    
    print(f"\n结果:")
    print(f"交集大小: {large_intersection_size}")
    print(f"交集总和: {large_sum}")
    print(f"执行时间: {end_time - start_time:.2f}秒")
    
    # 验证结果
    expected_intersection = set(large_set_a) & set([item[0] for item in large_set_b])
    expected_size = len(expected_intersection)
    expected_sum = sum(item[1] for item in large_set_b if item[0] in expected_intersection)
    
    print(f"验证 - 预期交集大小: {expected_size}")
    print(f"验证 - 预期交集总和: {expected_sum}")
    print(f"正确性: {'✓' if large_intersection_size == expected_size and large_sum == expected_sum else '✗'}")


def security_analysis():
    """
    安全性分析演示
    """
    print("\n" + "="*80)
    print("协议安全性分析")
    print("="*80)
    
    print("\n1. 隐私保护特性:")
    print("   • P1只知道交集大小，不知道具体的交集元素")
    print("   • P2只知道交集对应值的总和，不知道具体的交集元素")
    print("   • 双方都无法获得对方的完整数据集")
    
    print("\n2. 基于DDH假设的安全性:")
    print("   • 使用椭圆曲线群，DDH问题在该群上是困难的")
    print("   • 私有指数k1和k2确保了加密的安全性")
    print("   • 随机打乱顺序防止位置信息泄露")
    
    print("\n3. 加性同态加密的保护:")
    print("   • 数值始终以加密形式传输")
    print("   • 支持同态运算，无需解密即可求和")
    print("   • 重新随机化进一步增强安全性")
    
    print("\n4. 协议轮次优化:")
    print("   • 总共只需3轮通信")
    print("   • 第2轮并行发送两条消息提高效率")
    print("   • 最小化通信复杂度")


if __name__ == "__main__":
    advanced_example()
    security_analysis()
