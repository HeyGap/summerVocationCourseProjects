"""
基于DDH的私有交集求和协议实现
"""

import random
from typing import List, Tuple, Dict, Any
from .crypto_primitives import GROUP, HASH_FUNCTION, AHE_SCHEME
from .utils import shuffle_list, find_common_elements, print_step, print_separator


class Participant1:
    """
    参与方1 (P1)
    持有标识符集合V = {v_i}
    """
    
    def __init__(self, identifiers: List[str]):
        """
        初始化参与方1
        :param identifiers: 标识符列表
        """
        self.identifiers = identifiers
        self.k1 = None  # 私有指数
        self.public_key = None  # P2的公钥
        self.intersection_size = 0  # 交集大小
    
    def step0_setup(self):
        """
        步骤0: 选择随机私有指数k1
        """
        self.k1 = GROUP.random_scalar()
        print_step(0, "P1", f"选择私有指数 k1")
        return self.k1
    
    def step0_receive_public_key(self, public_key):
        """
        步骤0: 接收P2的公钥
        """
        self.public_key = public_key
        print_step(0, "P1", "接收到P2的公钥")
    
    def step1_send_encrypted_identifiers(self):
        """
        步骤1: 发送加密后的标识符集合
        对每个v_i计算H(v_i)^k1，然后随机打乱发送
        """
        encrypted_identifiers = []
        
        for v_i in self.identifiers:
            # 计算H(v_i)
            h_vi = HASH_FUNCTION.hash(v_i)
            # 计算H(v_i)^k1
            encrypted_vi = GROUP.point_multiply(h_vi, self.k1)
            encrypted_identifiers.append(encrypted_vi)
        
        # 随机打乱顺序
        shuffled_encrypted = shuffle_list(encrypted_identifiers)
        
        print_step(1, "P1", f"发送{len(shuffled_encrypted)}个加密标识符（已打乱顺序）")
        return shuffled_encrypted
    
    def step3_compute_intersection_and_sum(self, message_a, message_b):
        """
        步骤3: 计算交集并发送加密的总和
        :param message_a: 集合Z（来自P2的消息A）
        :param message_b: 元组集合（来自P2的消息B）
        :return: 重新随机化后的密文
        """
        print_step(3, "P1", "开始计算交集...")
        
        # 对消息B中的每个元组(y_j, c_j)，计算y_j^k1
        p1_computed_values = []
        ciphertext_mapping = {}  # 映射: 计算值 -> 对应的密文
        
        for y_j, c_j in message_b:
            # 计算y_j^k1 = H(w_j)^(k1*k2)
            computed_value = GROUP.point_multiply(y_j, self.k1)
            p1_computed_values.append(computed_value)
            ciphertext_mapping[computed_value] = c_j
        
        # 找到集合Z和P1计算值之间的交集
        intersection_elements = find_common_elements(message_a, p1_computed_values)
        self.intersection_size = len(intersection_elements)
        
        print_step(3, "P1", f"发现交集大小: {self.intersection_size}")
        
        # 收集对应的密文
        intersection_ciphertexts = []
        for element in intersection_elements:
            if element in ciphertext_mapping:
                intersection_ciphertexts.append(ciphertext_mapping[element])
        
        if not intersection_ciphertexts:
            # 如果没有交集，发送0的加密
            ct_sum = AHE_SCHEME.encrypt(self.public_key, 0)
        else:
            # 计算所有交集密文的同态和
            ct_sum = AHE_SCHEME.homomorphic_add(intersection_ciphertexts)
        
        # 重新随机化
        ct_final = AHE_SCHEME.refresh(ct_sum)
        
        print_step(3, "P1", f"发送重新随机化后的密文")
        return ct_final
    
    def get_intersection_size(self):
        """
        获取交集大小
        """
        return self.intersection_size


class Participant2:
    """
    参与方2 (P2)
    持有标识符-值对集合W = {(w_i, t_i)}
    """
    
    def __init__(self, identifier_value_pairs: List[Tuple[str, int]]):
        """
        初始化参与方2
        :param identifier_value_pairs: 标识符-值对列表
        """
        self.identifier_value_pairs = identifier_value_pairs
        self.k2 = None  # 私有指数
        self.public_key = None  # 公钥
        self.private_key = None  # 私钥
        self.intersection_sum = 0  # 交集总和
    
    def step0_setup(self):
        """
        步骤0: 选择随机私有指数k2并生成AHE密钥对
        """
        # 选择私有指数
        self.k2 = GROUP.random_scalar()
        
        # 生成AHE密钥对
        self.public_key, self.private_key = AHE_SCHEME.generate_keypair()
        
        print_step(0, "P2", f"选择私有指数k2并生成AHE密钥对")
        return self.public_key
    
    def step2_prepare_messages(self, p1_encrypted_identifiers):
        """
        步骤2: 准备两条消息A和B
        :param p1_encrypted_identifiers: 来自P1的加密标识符
        :return: (消息A, 消息B)
        """
        print_step(2, "P2", "准备消息A和B...")
        
        # 消息A: 对P1的数据进行处理
        message_a = []
        for x in p1_encrypted_identifiers:
            # x = H(v_i)^k1，计算x^k2 = H(v_i)^(k1*k2)
            double_encrypted = GROUP.point_multiply(x, self.k2)
            message_a.append(double_encrypted)
        
        # 随机打乱消息A
        message_a = shuffle_list(message_a)
        
        # 消息B: 基于P2自己的数据
        message_b = []
        for w_j, t_j in self.identifier_value_pairs:
            # 计算H(w_j)^k2
            h_wj = HASH_FUNCTION.hash(w_j)
            encrypted_wj = GROUP.point_multiply(h_wj, self.k2)
            
            # 加密t_j
            encrypted_tj = AHE_SCHEME.encrypt(self.public_key, t_j)
            
            message_b.append((encrypted_wj, encrypted_tj))
        
        # 随机打乱消息B
        message_b = shuffle_list(message_b)
        
        print_step(2, "P2", f"发送消息A({len(message_a)}个元素)和消息B({len(message_b)}个元组)")
        return message_a, message_b
    
    def step4_decrypt_final_sum(self, final_ciphertext):
        """
        步骤4: 解密最终密文得到交集总和
        :param final_ciphertext: 最终密文
        :return: 交集总和
        """
        self.intersection_sum = AHE_SCHEME.decrypt(self.private_key, final_ciphertext)
        print_step(4, "P2", f"解密得到交集总和: {self.intersection_sum}")
        return self.intersection_sum
    
    def get_intersection_sum(self):
        """
        获取交集总和
        """
        return self.intersection_sum


class PISProtocol:
    """
    私有交集求和协议主类
    """
    
    def __init__(self):
        self.p1 = None
        self.p2 = None
    
    def run_protocol(self, p1_identifiers: List[str], 
                     p2_identifier_value_pairs: List[Tuple[str, int]]):
        """
        运行完整的私有交集求和协议
        
        :param p1_identifiers: P1的标识符列表
        :param p2_identifier_value_pairs: P2的标识符-值对列表
        :return: (交集大小, 交集总和)
        """
        print("=" * 60)
        print("开始执行基于DDH的私有交集求和协议")
        print("=" * 60)
        
        # 初始化参与方
        self.p1 = Participant1(p1_identifiers)
        self.p2 = Participant2(p2_identifier_value_pairs)
        
        print(f"P1持有{len(p1_identifiers)}个标识符")
        print(f"P2持有{len(p2_identifier_value_pairs)}个标识符-值对")
        print_separator()
        
        # 步骤0: 初始设置
        print("步骤 0: 初始设置")
        self.p1.step0_setup()
        public_key = self.p2.step0_setup()
        self.p1.step0_receive_public_key(public_key)
        print_separator()
        
        # 步骤1: P1发送加密标识符
        print("步骤 1: P1 → P2")
        encrypted_identifiers = self.p1.step1_send_encrypted_identifiers()
        print_separator()
        
        # 步骤2: P2发送两条消息
        print("步骤 2: P2 → P1")
        message_a, message_b = self.p2.step2_prepare_messages(encrypted_identifiers)
        print_separator()
        
        # 步骤3: P1计算交集并发送加密总和
        print("步骤 3: P1 → P2")
        final_ciphertext = self.p1.step3_compute_intersection_and_sum(message_a, message_b)
        print_separator()
        
        # 步骤4: P2解密最终结果
        print("步骤 4: 最终输出")
        intersection_sum = self.p2.step4_decrypt_final_sum(final_ciphertext)
        intersection_size = self.p1.get_intersection_size()
        
        print_separator()
        print("协议执行完毕!")
        print(f"P1得知交集大小: {intersection_size}")
        print(f"P2得知交集总和: {intersection_sum}")
        print("=" * 60)
        
        return intersection_size, intersection_sum
    
    def verify_correctness(self, p1_identifiers: List[str], 
                          p2_identifier_value_pairs: List[Tuple[str, int]]):
        """
        验证协议正确性
        """
        # 直接计算真实的交集和总和
        p1_set = set(p1_identifiers)
        p2_dict = dict(p2_identifier_value_pairs)
        
        true_intersection = p1_set.intersection(set(p2_dict.keys()))
        true_intersection_size = len(true_intersection)
        true_intersection_sum = sum(p2_dict[identifier] for identifier in true_intersection)
        
        print("\n正确性验证:")
        print(f"真实交集: {sorted(list(true_intersection))}")
        print(f"真实交集大小: {true_intersection_size}")
        print(f"真实交集总和: {true_intersection_sum}")
        
        return true_intersection_size, true_intersection_sum
