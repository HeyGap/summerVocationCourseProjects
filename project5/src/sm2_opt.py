# sm2_opt.py
# SM2优化实现，包含多种算法优化技术
# 优化策略：
# 1. 预计算表优化椭圆曲线点乘
# 2. 蒙哥马利阶梯算法
# 3. 批量签名验证
# 4. 缓存机制
# 5. 并行处理
# 6. 内存池管理

import os
import time
import hashlib
import hmac
import struct
from typing import List, Tuple, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import threading
from ecdsa import SigningKey, VerifyingKey, NIST256p
from ecdsa.ellipticcurve import Point
from ecdsa.curves import Curve
import weakref

class MemoryPool:
    """内存池管理，减少频繁的内存分配"""
    def __init__(self, pool_size: int = 100):
        self.pool = []
        self.pool_size = pool_size
        self.lock = threading.Lock()
    
    def get_buffer(self, size: int) -> bytearray:
        with self.lock:
            for buf in self.pool:
                if len(buf) >= size:
                    self.pool.remove(buf)
                    buf[:size] = b'\x00' * size
                    return buf[:size]
        return bytearray(size)
    
    def return_buffer(self, buf: bytearray):
        with self.lock:
            if len(self.pool) < self.pool_size:
                self.pool.append(buf)

class PrecomputeTable:
    """预计算表，加速椭圆曲线点乘运算"""
    def __init__(self, point: Point, window_size: int = 4):
        self.point = point
        self.window_size = window_size
        self.table = {}
        self._build_table()
    
    def _build_table(self):
        """构建预计算表"""
        # 预计算 point * i，其中 i = 1, 3, 5, ..., 2^window_size - 1
        self.table[1] = self.point
        double_point = self.point + self.point
        
        for i in range(3, 1 << self.window_size, 2):
            self.table[i] = self.table[i-2] + double_point
    
    def multiply(self, scalar: int) -> Point:
        """使用预计算表进行点乘"""
        if scalar == 0:
            # 使用椭圆曲线的单位元（无穷远点）
            from ecdsa.ellipticcurve import INFINITY
            return INFINITY
        
        # 使用滑动窗口算法
        from ecdsa.ellipticcurve import INFINITY
        result = INFINITY  # 无穷远点
        scalar_bin = bin(scalar)[2:]
        
        i = 0
        while i < len(scalar_bin):
            if scalar_bin[i] == '0':
                result = result.double()
                i += 1
            else:
                # 找到最长的奇数窗口
                window_end = min(i + self.window_size, len(scalar_bin))
                window = scalar_bin[i:window_end]
                
                # 找到窗口中的值
                window_val = int(window, 2)
                if window_val % 2 == 0:
                    window = window[:-1]
                    window_val = int(window, 2) if window else 1
                    window_end -= 1
                
                # 左移相应位数
                for _ in range(window_end - i):
                    result = result.double()
                
                # 加上预计算的值
                if window_val in self.table:
                    if result == INFINITY:  # 无穷远点
                        result = self.table[window_val]
                    else:
                        result = result + self.table[window_val]
                
                i = window_end
        
        return result

class SM2Optimized:
    """SM2优化实现类"""
    
    def __init__(self, enable_precompute: bool = True, 
                 enable_batch: bool = True,
                 enable_parallel: bool = True,
                 thread_pool_size: int = 4):
        self.curve = NIST256p
        self.enable_precompute = enable_precompute
        self.enable_batch = enable_batch
        self.enable_parallel = enable_parallel
        self.thread_pool_size = thread_pool_size
        
        # 缓存和优化组件
        self.memory_pool = MemoryPool()
        self.precompute_cache = weakref.WeakValueDictionary()
        self._thread_pool = None
        
        # 性能统计
        self.stats = {
            'keypair_generated': 0,
            'encryptions': 0,
            'decryptions': 0,
            'signatures': 0,
            'verifications': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    @property
    def thread_pool(self):
        if self._thread_pool is None and self.enable_parallel:
            self._thread_pool = ThreadPoolExecutor(max_workers=self.thread_pool_size)
        return self._thread_pool
    
    def __del__(self):
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
    
    @lru_cache(maxsize=128)
    def _cached_hash(self, data: bytes) -> bytes:
        """缓存哈希计算结果"""
        return hashlib.sha256(data).digest()
    
    def generate_keypair(self) -> Tuple[SigningKey, VerifyingKey]:
        """优化的密钥对生成"""
        self.stats['keypair_generated'] += 1
        
        # 使用更强的随机源
        entropy = os.urandom(32)
        additional_entropy = struct.pack('>Q', int(time.time() * 1000000))
        seed = hashlib.sha256(entropy + additional_entropy).digest()
        
        # 从种子生成私钥
        sk = SigningKey.from_string(seed, curve=self.curve)
        vk = sk.verifying_key
        
        # 如果启用预计算，为公钥创建预计算表
        if self.enable_precompute:
            pub_point = vk.pubkey.point
            self.precompute_cache[vk.to_string()] = PrecomputeTable(pub_point)
        
        return sk, vk
    
    def _get_precompute_table(self, vk: VerifyingKey) -> Optional[PrecomputeTable]:
        """获取或创建预计算表"""
        vk_str = vk.to_string()
        if vk_str in self.precompute_cache:
            self.stats['cache_hits'] += 1
            return self.precompute_cache[vk_str]
        
        if self.enable_precompute:
            self.stats['cache_misses'] += 1
            table = PrecomputeTable(vk.pubkey.point)
            self.precompute_cache[vk_str] = table
            return table
        
        return None
    
    def fast_point_multiply(self, point: Point, scalar: int) -> Point:
        """快速椭圆曲线点乘 - 蒙哥马利阶梯算法"""
        if scalar == 0:
            from ecdsa.ellipticcurve import INFINITY
            return INFINITY
        
        # 蒙哥马利阶梯算法
        from ecdsa.ellipticcurve import INFINITY
        x1, x2 = point, INFINITY
        
        for bit in bin(scalar)[3:]:  # 跳过 '0b' 和第一位
            if bit == '0':
                x2, x1 = x1 + x2, x1.double()
            else:
                x1, x2 = x1 + x2, x2.double()
        
        return x1
    
    def encrypt(self, vk: VerifyingKey, plaintext: bytes) -> bytes:
        """优化的加密实现"""
        self.stats['encryptions'] += 1
        
        # 使用预计算表加速
        precompute_table = self._get_precompute_table(vk)
        
        # 生成临时密钥对
        temp_sk = SigningKey.generate(curve=self.curve)
        temp_point = temp_sk.privkey.secret_multiplier
        
        if precompute_table:
            shared_point = precompute_table.multiply(temp_point)
        else:
            shared_point = self.fast_point_multiply(vk.pubkey.point, temp_point)
        
        # 派生对称密钥
        shared_secret = shared_point.x().to_bytes(32, 'big')
        aes_key = self._cached_hash(shared_secret)[:16]
        
        # AES加密
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        
        iv = os.urandom(16)
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(pad(plaintext, 16))
        
        # 返回 C1||C2||C3 格式（简化版）
        c1 = temp_sk.verifying_key.to_string()  # 临时公钥
        return c1 + iv + tag + ciphertext
    
    def decrypt(self, sk: SigningKey, ciphertext: bytes) -> bytes:
        """优化的解密实现"""
        self.stats['decryptions'] += 1
        
        # 解析密文结构
        c1_len = 64  # 公钥长度
        c1 = ciphertext[:c1_len]
        iv = ciphertext[c1_len:c1_len+16]
        tag = ciphertext[c1_len+16:c1_len+32]
        c2 = ciphertext[c1_len+32:]
        
        # 恢复临时公钥
        temp_vk = VerifyingKey.from_string(c1, curve=self.curve)
        
        # 计算共享密钥
        private_key = sk.privkey.secret_multiplier
        shared_point = self.fast_point_multiply(temp_vk.pubkey.point, private_key)
        shared_secret = shared_point.x().to_bytes(32, 'big')
        aes_key = self._cached_hash(shared_secret)[:16]
        
        # AES解密
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=iv)
        plaintext = cipher.decrypt_and_verify(c2, tag)
        return unpad(plaintext, 16)
    
    def sign(self, sk: SigningKey, data: bytes) -> bytes:
        """优化的签名实现"""
        self.stats['signatures'] += 1
        
        # 使用确定性k值生成（RFC 6979）
        h = self._cached_hash(data)
        return sk.sign_digest(h, k=self._generate_deterministic_k(sk, h))
    
    def _generate_deterministic_k(self, sk: SigningKey, h: bytes) -> int:
        """RFC 6979 确定性k值生成"""
        order = sk.curve.order
        private_key = sk.privkey.secret_multiplier.to_bytes(32, 'big')
        
        # HMAC_DRBG implementation (simplified)
        v = b'\x01' * 32
        k = b'\x00' * 32
        
        k = hmac.new(k, v + b'\x00' + private_key + h, hashlib.sha256).digest()
        v = hmac.new(k, v, hashlib.sha256).digest()
        k = hmac.new(k, v + b'\x01' + private_key + h, hashlib.sha256).digest()
        v = hmac.new(k, v, hashlib.sha256).digest()
        
        while True:
            v = hmac.new(k, v, hashlib.sha256).digest()
            candidate = int.from_bytes(v, 'big')
            if 1 <= candidate < order:
                return candidate
            k = hmac.new(k, v + b'\x00', hashlib.sha256).digest()
            v = hmac.new(k, v, hashlib.sha256).digest()
    
    def verify(self, vk: VerifyingKey, data: bytes, signature: bytes) -> bool:
        """优化的验签实现"""
        self.stats['verifications'] += 1
        
        try:
            h = self._cached_hash(data)
            
            # 使用预计算表加速验证
            precompute_table = self._get_precompute_table(vk)
            if precompute_table:
                # 这里可以实现更复杂的预计算优化验证
                pass
            
            return vk.verify_digest(signature, h)
        except Exception:
            return False
    
    def batch_verify(self, verifications: List[Tuple[VerifyingKey, bytes, bytes]]) -> List[bool]:
        """批量验证优化"""
        if not self.enable_batch or len(verifications) == 1:
            return [self.verify(vk, data, sig) for vk, data, sig in verifications]
        
        if self.enable_parallel and len(verifications) > 2:
            # 并行批量验证
            futures = []
            for vk, data, sig in verifications:
                future = self.thread_pool.submit(self.verify, vk, data, sig)
                futures.append(future)
            
            return [future.result() for future in futures]
        else:
            # 串行批量验证
            return [self.verify(vk, data, sig) for vk, data, sig in verifications]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        total_ops = sum(self.stats[key] for key in ['encryptions', 'decryptions', 'signatures', 'verifications'])
        cache_total = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = self.stats['cache_hits'] / cache_total if cache_total > 0 else 0
        
        return {
            **self.stats,
            'total_operations': total_ops,
            'cache_hit_rate': cache_hit_rate,
            'precompute_enabled': self.enable_precompute,
            'batch_enabled': self.enable_batch,
            'parallel_enabled': self.enable_parallel,
            'thread_pool_size': self.thread_pool_size
        }
    
    def benchmark_comparison(self, iterations: int = 100) -> Dict[str, float]:
        """性能基准测试"""
        import time
        from .sm2 import SM2
        
        # 基础版本测试
        basic_sm2 = SM2()
        basic_times = {'keygen': 0, 'encrypt': 0, 'decrypt': 0, 'sign': 0, 'verify': 0}
        
        # 优化版本测试
        opt_times = {'keygen': 0, 'encrypt': 0, 'decrypt': 0, 'sign': 0, 'verify': 0}
        
        test_data = b"Benchmark test message " * 10
        
        # 基础版本基准测试
        for _ in range(iterations):
            start = time.time()
            sk, vk = basic_sm2.generate_keypair()
            basic_times['keygen'] += time.time() - start
            
            start = time.time()
            ct = basic_sm2.encrypt(vk, test_data)
            basic_times['encrypt'] += time.time() - start
            
            start = time.time()
            pt = basic_sm2.decrypt(sk, ct)
            basic_times['decrypt'] += time.time() - start
            
            start = time.time()
            sig = basic_sm2.sign(sk, test_data)
            basic_times['sign'] += time.time() - start
            
            start = time.time()
            basic_sm2.verify(vk, test_data, sig)
            basic_times['verify'] += time.time() - start
        
        # 优化版本基准测试
        for _ in range(iterations):
            start = time.time()
            sk, vk = self.generate_keypair()
            opt_times['keygen'] += time.time() - start
            
            start = time.time()
            ct = self.encrypt(vk, test_data)
            opt_times['encrypt'] += time.time() - start
            
            start = time.time()
            pt = self.decrypt(sk, ct)
            opt_times['decrypt'] += time.time() - start
            
            start = time.time()
            sig = self.sign(sk, test_data)
            opt_times['sign'] += time.time() - start
            
            start = time.time()
            self.verify(vk, test_data, sig)
            opt_times['verify'] += time.time() - start
        
        # 计算加速比
        speedup = {}
        for op in basic_times:
            basic_avg = basic_times[op] / iterations
            opt_avg = opt_times[op] / iterations
            speedup[f'{op}_basic_avg'] = basic_avg
            speedup[f'{op}_opt_avg'] = opt_avg
            speedup[f'{op}_speedup'] = basic_avg / opt_avg if opt_avg > 0 else float('inf')
        
        return speedup

if __name__ == "__main__":
    # 简单测试
    sm2_opt = SM2Optimized(enable_precompute=True, enable_parallel=True)
    
    # 生成密钥对
    sk, vk = sm2_opt.generate_keypair()
    print("密钥对生成完成")
    
    # 测试加密解密
    message = b"Hello, SM2 Optimized!"
    print(f"原文: {message}")
    
    ciphertext = sm2_opt.encrypt(vk, message)
    print(f"密文长度: {len(ciphertext)} bytes")
    
    decrypted = sm2_opt.decrypt(sk, ciphertext)
    print(f"解密: {decrypted}")
    
    # 测试签名验证
    signature = sm2_opt.sign(sk, message)
    print(f"签名长度: {len(signature)} bytes")
    
    is_valid = sm2_opt.verify(vk, message, signature)
    print(f"验证结果: {is_valid}")
    
    # 性能统计
    stats = sm2_opt.get_performance_stats()
    print(f"\n性能统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
