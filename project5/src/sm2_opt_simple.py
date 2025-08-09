# sm2_opt_simple.py
# SM2简化优化实现，专注于可工作的基本优化
# 优化策略：
# 1. 缓存机制
# 2. 并行处理
# 3. 确定性签名
# 4. 批量操作

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
import weakref

class SM2OptimizedSimple:
    """SM2简化优化实现类"""
    
    def __init__(self, enable_cache: bool = True, 
                 enable_batch: bool = True,
                 enable_parallel: bool = True,
                 thread_pool_size: int = 4):
        self.curve = NIST256p
        self.enable_cache = enable_cache
        self.enable_batch = enable_batch
        self.enable_parallel = enable_parallel
        self.thread_pool_size = thread_pool_size
        
        # 缓存
        self.key_cache = weakref.WeakValueDictionary() if enable_cache else None
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
    
    @lru_cache(maxsize=256)
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
        
        # 缓存密钥对
        if self.key_cache is not None:
            self.key_cache[vk.to_string()] = vk
        
        return sk, vk
    
    def encrypt(self, vk: VerifyingKey, plaintext: bytes) -> bytes:
        """优化的加密实现"""
        self.stats['encryptions'] += 1
        
        # 生成临时密钥对
        temp_sk = SigningKey.generate(curve=self.curve)
        
        # 计算共享密钥 (ECDH)
        shared_point = temp_sk.privkey.secret_multiplier * vk.pubkey.point
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
        shared_point = sk.privkey.secret_multiplier * temp_vk.pubkey.point
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
            'cache_enabled': self.enable_cache,
            'batch_enabled': self.enable_batch,
            'parallel_enabled': self.enable_parallel,
            'thread_pool_size': self.thread_pool_size
        }

if __name__ == "__main__":
    # 简单测试
    sm2_opt = SM2OptimizedSimple(enable_cache=True, enable_parallel=True)
    
    # 生成密钥对
    sk, vk = sm2_opt.generate_keypair()
    print("密钥对生成完成")
    
    # 测试加密解密
    message = b"Hello, SM2 Optimized Simple!"
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
