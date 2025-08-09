"""
加密原语测试
"""

import unittest
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crypto_primitives import EllipticCurveGroup, HashFunction, AdditiveHomomorphicEncryption


class TestCryptoPrimitives(unittest.TestCase):
    """
    加密原语测试类
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        self.group = EllipticCurveGroup()
        self.hash_func = HashFunction(self.group)
        self.ahe = AdditiveHomomorphicEncryption()
    
    def test_elliptic_curve_group(self):
        """
        测试椭圆曲线群
        """
        # 测试随机标量生成
        scalar1 = self.group.random_scalar()
        scalar2 = self.group.random_scalar()
        self.assertNotEqual(scalar1, scalar2)  # 很高概率不同
        
        # 测试点乘运算
        point = "test_point"
        result1 = self.group.point_multiply(point, scalar1)
        result2 = self.group.point_multiply(point, scalar2)
        self.assertNotEqual(result1, result2)
        
        # 测试哈希到群元素
        element1 = self.group.hash_to_group_element("test1")
        element2 = self.group.hash_to_group_element("test2")
        self.assertNotEqual(element1, element2)
    
    def test_hash_function(self):
        """
        测试哈希函数
        """
        # 测试确定性
        hash1 = self.hash_func.hash("identifier1")
        hash1_repeat = self.hash_func.hash("identifier1")
        self.assertEqual(hash1, hash1_repeat)
        
        # 测试不同输入产生不同输出
        hash2 = self.hash_func.hash("identifier2")
        self.assertNotEqual(hash1, hash2)
    
    def test_additive_homomorphic_encryption(self):
        """
        测试加性同态加密
        """
        # 生成密钥对
        public_key, private_key = self.ahe.generate_keypair()
        self.assertIsNotNone(public_key)
        self.assertIsNotNone(private_key)
        
        # 测试加密解密
        message = 42
        ciphertext = self.ahe.encrypt(public_key, message)
        decrypted = self.ahe.decrypt(private_key, ciphertext)
        self.assertEqual(message, decrypted)
        
        # 测试同态性
        m1, m2, m3 = 10, 20, 30
        c1 = self.ahe.encrypt(public_key, m1)
        c2 = self.ahe.encrypt(public_key, m2)
        c3 = self.ahe.encrypt(public_key, m3)
        
        c_sum = self.ahe.homomorphic_add([c1, c2, c3])
        decrypted_sum = self.ahe.decrypt(private_key, c_sum)
        self.assertEqual(decrypted_sum, m1 + m2 + m3)
        
        # 测试重新随机化
        c_refreshed = self.ahe.refresh(c1)
        decrypted_refreshed = self.ahe.decrypt(private_key, c_refreshed)
        self.assertEqual(decrypted_refreshed, m1)
        
        # 重新随机化后密文应该不同
        self.assertNotEqual(c1['ciphertext'], c_refreshed['ciphertext'])


if __name__ == '__main__':
    unittest.main()
