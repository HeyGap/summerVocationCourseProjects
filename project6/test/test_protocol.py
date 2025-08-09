"""
协议正确性测试
"""

import unittest
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pis_protocol import PISProtocol


class TestPISProtocol(unittest.TestCase):
    """
    私有交集求和协议测试类
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        self.protocol = PISProtocol()
    
    def test_basic_functionality(self):
        """
        测试基本功能
        """
        p1_identifiers = ["a", "b", "c", "d"]
        p2_pairs = [("a", 10), ("b", 20), ("e", 30), ("f", 40)]
        
        # 运行协议
        computed_size, computed_sum = self.protocol.run_protocol(p1_identifiers, p2_pairs)
        
        # 验证正确性
        true_size, true_sum = self.protocol.verify_correctness(p1_identifiers, p2_pairs)
        
        self.assertEqual(computed_size, true_size)
        self.assertEqual(computed_sum, true_sum)
        self.assertEqual(computed_size, 2)  # a, b
        self.assertEqual(computed_sum, 30)  # 10 + 20
    
    def test_empty_intersection(self):
        """
        测试空交集情况
        """
        p1_identifiers = ["a", "b", "c"]
        p2_pairs = [("d", 10), ("e", 20), ("f", 30)]
        
        computed_size, computed_sum = self.protocol.run_protocol(p1_identifiers, p2_pairs)
        true_size, true_sum = self.protocol.verify_correctness(p1_identifiers, p2_pairs)
        
        self.assertEqual(computed_size, true_size)
        self.assertEqual(computed_sum, true_sum)
        self.assertEqual(computed_size, 0)
        self.assertEqual(computed_sum, 0)
    
    def test_full_intersection(self):
        """
        测试完全交集情况
        """
        p1_identifiers = ["x", "y", "z"]
        p2_pairs = [("x", 100), ("y", 200), ("z", 300)]
        
        computed_size, computed_sum = self.protocol.run_protocol(p1_identifiers, p2_pairs)
        true_size, true_sum = self.protocol.verify_correctness(p1_identifiers, p2_pairs)
        
        self.assertEqual(computed_size, true_size)
        self.assertEqual(computed_sum, true_sum)
        self.assertEqual(computed_size, 3)
        self.assertEqual(computed_sum, 600)  # 100 + 200 + 300
    
    def test_single_element_intersection(self):
        """
        测试单元素交集
        """
        p1_identifiers = ["unique"]
        p2_pairs = [("unique", 42), ("other", 10)]
        
        computed_size, computed_sum = self.protocol.run_protocol(p1_identifiers, p2_pairs)
        true_size, true_sum = self.protocol.verify_correctness(p1_identifiers, p2_pairs)
        
        self.assertEqual(computed_size, true_size)
        self.assertEqual(computed_sum, true_sum)
        self.assertEqual(computed_size, 1)
        self.assertEqual(computed_sum, 42)
    
    def test_negative_values(self):
        """
        测试负值情况
        """
        p1_identifiers = ["a", "b", "c"]
        p2_pairs = [("a", -10), ("b", 20), ("d", -30)]
        
        computed_size, computed_sum = self.protocol.run_protocol(p1_identifiers, p2_pairs)
        true_size, true_sum = self.protocol.verify_correctness(p1_identifiers, p2_pairs)
        
        self.assertEqual(computed_size, true_size)
        self.assertEqual(computed_sum, true_sum)
        self.assertEqual(computed_size, 2)
        self.assertEqual(computed_sum, 10)  # -10 + 20


if __name__ == '__main__':
    unittest.main()
