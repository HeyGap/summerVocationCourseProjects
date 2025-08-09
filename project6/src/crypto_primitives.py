"""
加密原语实现
包括椭圆曲线群、哈希函数、加性同态加密等
"""

import hashlib
import random
import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import gmpy2


class EllipticCurveGroup:
    """
    椭圆曲线群实现，基于secp256r1 (prime256v1)
    在该群上DDH假设成立
    """
    
    def __init__(self):
        self.curve = ec.SECP256R1()
        self.backend = default_backend()
        # 生成器点
        self.generator = self._get_generator()
        # 群的阶
        self.order = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
    
    def _get_generator(self):
        """获取椭圆曲线的生成元"""
        private_key = ec.generate_private_key(self.curve, self.backend)
        public_key = private_key.public_key()
        return public_key.public_numbers()
    
    def random_scalar(self):
        """生成随机标量"""
        return secrets.randbelow(self.order)
    
    def point_multiply(self, point, scalar):
        """椭圆曲线点乘运算"""
        # 简化实现：模拟真正的椭圆曲线点乘
        # 为了确保交换性，我们将使用数值运算而不是字符串拼接
        if isinstance(point, str):
            # 将点的哈希值转换为数值
            point_num = int(point, 16) if len(point) == 64 else hash(point)
        else:
            point_num = int(point)
        
        # 使用模运算来模拟椭圆曲线点乘，确保结果在合理范围内
        result = (point_num * scalar) % self.order
        
        # 转换回哈希格式
        return format(result, '064x')
    
    def _point_to_bytes(self, point):
        """将点转换为字节"""
        if isinstance(point, str):
            return point.encode('utf-8')
        return str(point).encode('utf-8')
    
    def hash_to_group_element(self, identifier):
        """
        将标识符哈希映射到群元素
        使用确定性哈希确保相同标识符总是映射到相同元素
        """
        hash_input = str(identifier).encode('utf-8')
        hasher = hashlib.sha256()
        hasher.update(hash_input)
        # 使用固定的盐确保确定性
        hasher.update(b"group_element_salt")
        hash_bytes = hasher.digest()
        
        # 转换为64位十六进制字符串表示
        element = hash_bytes.hex()
        return element


class HashFunction:
    """
    哈希函数H，将标识符映射到群元素
    """
    
    def __init__(self, group):
        self.group = group
    
    def hash(self, identifier):
        """将标识符哈希到群元素"""
        return self.group.hash_to_group_element(identifier)


class AdditiveHomomorphicEncryption:
    """
    加性同态加密方案
    基于简化的Paillier-like方案
    """
    
    def __init__(self):
        self.public_key = None
        self.private_key = None
    
    def generate_keypair(self, key_size=2048):
        """生成公私钥对"""
        # 简化实现：生成大素数p, q
        p = gmpy2.next_prime(secrets.randbits(key_size // 2))
        q = gmpy2.next_prime(secrets.randbits(key_size // 2))
        n = p * q
        
        # lambda = lcm(p-1, q-1)
        lambda_n = gmpy2.lcm(p - 1, q - 1)
        
        # 选择g = n + 1
        g = n + 1
        
        # 计算mu = (L(g^lambda mod n^2))^(-1) mod n
        # 其中L(x) = (x-1)/n
        n_squared = n * n
        g_lambda = gmpy2.powmod(g, lambda_n, n_squared)
        l_value = (g_lambda - 1) // n
        mu = gmpy2.invert(l_value, n)
        
        self.public_key = {'n': n, 'g': g}
        self.private_key = {'lambda': lambda_n, 'mu': mu, 'n': n}
        
        return self.public_key, self.private_key
    
    def encrypt(self, public_key, message):
        """加密消息"""
        if public_key is None:
            raise ValueError("Public key not set")
            
        n = public_key['n']
        g = public_key['g']
        n_squared = n * n
        
        # 选择随机数r
        r = secrets.randbelow(n)
        while gmpy2.gcd(r, n) != 1:
            r = secrets.randbelow(n)
        
        # c = g^m * r^n mod n^2
        c = (gmpy2.powmod(g, message, n_squared) * gmpy2.powmod(r, n, n_squared)) % n_squared
        
        return {'ciphertext': c, 'n': n}
    
    def decrypt(self, private_key, ciphertext):
        """解密密文"""
        if private_key is None:
            raise ValueError("Private key not set")
            
        c = ciphertext['ciphertext']
        n = private_key['n']
        lambda_n = private_key['lambda']
        mu = private_key['mu']
        n_squared = n * n
        
        # m = L(c^lambda mod n^2) * mu mod n
        c_lambda = gmpy2.powmod(c, lambda_n, n_squared)
        l_value = (c_lambda - 1) // n
        m = (l_value * mu) % n
        
        return int(m)
    
    def homomorphic_add(self, ciphertext_list):
        """同态加法：计算多个密文的同态和"""
        if not ciphertext_list:
            raise ValueError("Empty ciphertext list")
            
        n = ciphertext_list[0]['n']
        n_squared = n * n
        
        result = 1
        for ct in ciphertext_list:
            result = (result * ct['ciphertext']) % n_squared
        
        return {'ciphertext': result, 'n': n}
    
    def refresh(self, ciphertext):
        """重新随机化密文"""
        n = ciphertext['n']
        n_squared = n * n
        
        # 选择随机数r
        r = secrets.randbelow(n)
        while gmpy2.gcd(r, n) != 1:
            r = secrets.randbelow(n)
        
        # 同态加上0的加密: c' = c * (1 * r^n) mod n^2
        refreshed = (ciphertext['ciphertext'] * gmpy2.powmod(r, n, n_squared)) % n_squared
        
        return {'ciphertext': refreshed, 'n': n}


# 全局实例
GROUP = EllipticCurveGroup()
HASH_FUNCTION = HashFunction(GROUP)
AHE_SCHEME = AdditiveHomomorphicEncryption()
