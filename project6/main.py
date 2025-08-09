"""
基于DDH的私有交集求和协议 - 主程序示例
"""

from src.pis_protocol import PISProtocol


def main():
    """
    主函数：演示私有交集求和协议的使用
    """
    # 示例数据
    print("构造示例数据...")
    
    # P1的标识符集合
    p1_identifiers = ["alice", "bob", "charlie", "david", "eve"]
    
    # P2的标识符-值对集合
    p2_identifier_value_pairs = [
        ("alice", 10),
        ("bob", 20), 
        ("frank", 15),
        ("grace", 25),
        ("david", 30)
    ]
    
    print(f"P1标识符集合: {p1_identifiers}")
    print(f"P2标识符-值对: {p2_identifier_value_pairs}")
    
    # 创建协议实例
    protocol = PISProtocol()
    
    # 先验证正确性
    true_size, true_sum = protocol.verify_correctness(p1_identifiers, p2_identifier_value_pairs)
    
    print("\n" + "="*60)
    print("运行协议...")
    
    # 运行协议
    computed_size, computed_sum = protocol.run_protocol(p1_identifiers, p2_identifier_value_pairs)
    
    # 验证结果
    print("\n" + "="*60)
    print("结果验证:")
    print(f"协议计算的交集大小: {computed_size}")
    print(f"真实的交集大小: {true_size}")
    print(f"大小匹配: {'✓' if computed_size == true_size else '✗'}")
    
    print(f"协议计算的交集总和: {computed_sum}")
    print(f"真实的交集总和: {true_sum}")  
    print(f"总和匹配: {'✓' if computed_sum == true_sum else '✗'}")
    
    if computed_size == true_size and computed_sum == true_sum:
        print("\n🎉 协议执行成功！结果完全正确！")
    else:
        print("\n❌ 协议执行结果不正确！")


def test_edge_cases():
    """
    测试边界情况
    """
    print("\n" + "="*60)
    print("测试边界情况...")
    
    protocol = PISProtocol()
    
    # 测试1: 空交集
    print("\n测试1: 空交集")
    p1_empty = ["a", "b", "c"]
    p2_empty = [("d", 10), ("e", 20), ("f", 30)]
    
    true_size, true_sum = protocol.verify_correctness(p1_empty, p2_empty)
    computed_size, computed_sum = protocol.run_protocol(p1_empty, p2_empty)
    
    print(f"空交集测试: {'✓' if computed_size == true_size == 0 and computed_sum == true_sum == 0 else '✗'}")
    
    # 测试2: 完全重叠
    print("\n测试2: 完全重叠")
    p1_full = ["x", "y", "z"]
    p2_full = [("x", 100), ("y", 200), ("z", 300)]
    
    true_size, true_sum = protocol.verify_correctness(p1_full, p2_full)
    computed_size, computed_sum = protocol.run_protocol(p1_full, p2_full)
    
    print(f"完全重叠测试: {'✓' if computed_size == true_size == 3 and computed_sum == true_sum == 600 else '✗'}")


if __name__ == "__main__":
    main()
    test_edge_cases()
