"""
调试版本的协议，用于验证计算步骤
"""

from src.crypto_primitives import GROUP, HASH_FUNCTION, AHE_SCHEME
from src.utils import shuffle_list, find_common_elements


def debug_protocol():
    """
    调试协议执行过程
    """
    print("=== 调试模式 ===")
    
    # 简单示例
    p1_identifiers = ["alice", "bob"]
    p2_pairs = [("alice", 10), ("charlie", 20)]
    
    print(f"P1标识符: {p1_identifiers}")
    print(f"P2标识符-值对: {p2_pairs}")
    print()
    
    # 步骤0: 选择私钥
    k1 = GROUP.random_scalar()
    k2 = GROUP.random_scalar()
    
    print(f"k1 = {k1}")
    print(f"k2 = {k2}")
    print()
    
    # P1的计算
    print("=== P1的计算 ===")
    p1_encrypted = []
    p1_debug = {}
    
    for v in p1_identifiers:
        h_v = HASH_FUNCTION.hash(v)
        encrypted_v = GROUP.point_multiply(h_v, k1)
        p1_encrypted.append(encrypted_v)
        p1_debug[v] = {"h_v": h_v, "h_v_k1": encrypted_v}
        print(f"{v}: H({v}) = {h_v}")
        print(f"{v}: H({v})^k1 = {encrypted_v}")
    
    print()
    
    # P2的计算 - 消息A
    print("=== P2的计算 - 消息A ===")
    message_a = []
    
    for encrypted_v in p1_encrypted:
        double_encrypted = GROUP.point_multiply(encrypted_v, k2)
        message_a.append(double_encrypted)
        print(f"收到: {encrypted_v}")
        print(f"计算: {encrypted_v}^k2 = {double_encrypted}")
    
    print()
    
    # P2的计算 - 消息B
    print("=== P2的计算 - 消息B ===")
    message_b = []
    p2_debug = {}
    
    for w, t in p2_pairs:
        h_w = HASH_FUNCTION.hash(w)
        encrypted_w = GROUP.point_multiply(h_w, k2)
        message_b.append((encrypted_w, t))  # 简化，不加密t
        p2_debug[w] = {"h_w": h_w, "h_w_k2": encrypted_w}
        print(f"{w}: H({w}) = {h_w}")
        print(f"{w}: H({w})^k2 = {encrypted_w}")
    
    print()
    
    # P1的最终计算
    print("=== P1的最终计算 ===")
    p1_final_values = []
    
    for encrypted_w, t in message_b:
        final_value = GROUP.point_multiply(encrypted_w, k1)
        p1_final_values.append(final_value)
        print(f"收到: {encrypted_w}")
        print(f"计算: {encrypted_w}^k1 = {final_value}")
    
    print()
    
    # 查找交集
    print("=== 交集计算 ===")
    print(f"消息A: {message_a}")
    print(f"P1计算值: {p1_final_values}")
    
    intersection = find_common_elements(message_a, p1_final_values)
    print(f"交集: {intersection}")
    
    # 验证应有的结果
    print()
    print("=== 验证 ===")
    for v in p1_identifiers:
        for w in [pair[0] for pair in p2_pairs]:
            if v == w:
                h_v = HASH_FUNCTION.hash(v)
                h_w = HASH_FUNCTION.hash(w)
                should_match = GROUP.point_multiply(GROUP.point_multiply(h_v, k1), k2)
                print(f"匹配项 {v}={w}:")
                print(f"  应该产生: H({v})^(k1*k2) = {should_match}")
                
                # 验证k1*k2 = k2*k1
                alt_calc = GROUP.point_multiply(GROUP.point_multiply(h_w, k2), k1)
                print(f"  反向计算: H({w})^(k2*k1) = {alt_calc}")
                print(f"  是否匹配: {should_match == alt_calc}")


if __name__ == "__main__":
    debug_protocol()
