"""
数字水印核心算法模块
基于DWT+DCT的盲水印实现，支持文本水印的嵌入与提取
"""
from __future__ import annotations
import numpy as np
import cv2
import pywt
from typing import Tuple, Dict, List
import os
from dataclasses import dataclass
from skimage.util import view_as_blocks


@dataclass
class WatermarkConfig:
    """水印配置参数"""
    block_size: int = 8          # DCT块大小
    strength: float = 10.0       # 量化强度
    repetition: int = 5          # 重复编码次数
    seed: int = 42               # 随机种子
    coeff_pos: Tuple[int, int] = (3, 2)  # DCT系数位置


class BlindWatermark:
    """盲水印算法类"""
    
    def __init__(self, config: WatermarkConfig = None):
        self.config = config or WatermarkConfig()
        np.random.seed(self.config.seed)
    
    def _rgb_to_yuv(self, img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """RGB转YUV颜色空间"""
        if len(img.shape) == 3:
            yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
            return yuv[:,:,0], yuv[:,:,1], yuv[:,:,2]
        else:
            return img, None, None
    
    def _yuv_to_rgb(self, y: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        """YUV转RGB颜色空间"""
        if u is not None and v is not None:
            yuv = np.stack([y, u, v], axis=2)
            return cv2.cvtColor(yuv.astype(np.uint8), cv2.COLOR_YUV2BGR)
        else:
            return y.astype(np.uint8)
    
    def _text_to_binary(self, text: str) -> np.ndarray:
        """文本转二进制序列"""
        binary_str = ''.join(format(ord(c), '08b') for c in text)
        return np.array([int(b) for b in binary_str], dtype=np.uint8)
    
    def _binary_to_text(self, binary: np.ndarray) -> str:
        """二进制序列转文本"""
        try:
            # 确保长度是8的倍数
            if len(binary) % 8 != 0:
                binary = binary[:-(len(binary) % 8)]
            
            text = ''
            for i in range(0, len(binary), 8):
                byte = binary[i:i+8]
                char_code = int(''.join(map(str, byte)), 2)
                if char_code > 0:  # 忽略空字符
                    text += chr(char_code)
            return text
        except:
            return "DECODE_ERROR"
    
    def _pad_to_blocks(self, img: np.ndarray, block_size: int) -> Tuple[np.ndarray, Tuple[int, int]]:
        """填充图像到块大小的整数倍"""
        h, w = img.shape
        pad_h = (block_size - h % block_size) % block_size
        pad_w = (block_size - w % block_size) % block_size
        
        padded = np.pad(img, ((0, pad_h), (0, pad_w)), mode='reflect')
        return padded, (h, w)
    
    def _calculate_capacity(self, img_shape: Tuple[int, int]) -> int:
        """计算水印容量（比特数）"""
        h, w = img_shape
        # DWT降采样后的尺寸
        dwt_h, dwt_w = h // 2, w // 2
        # DCT块数量
        blocks_h = dwt_h // self.config.block_size
        blocks_w = dwt_w // self.config.block_size
        return blocks_h * blocks_w
    
    def embed_watermark(self, host_image: np.ndarray, watermark_text: str) -> np.ndarray:
        """嵌入水印"""
        # 转换颜色空间
        y_channel, u_channel, v_channel = self._rgb_to_yuv(host_image)
        y_float = y_channel.astype(np.float32)
        
        # 一级DWT分解
        coeffs = pywt.dwt2(y_float, 'haar')
        LL, (LH, HL, HH) = coeffs
        
        # 计算容量并调整参数
        capacity = self._calculate_capacity(LL.shape)
        watermark_bits = self._text_to_binary(watermark_text)
        
        # 自适应调整重复次数
        required_bits = len(watermark_bits) * self.config.repetition
        if required_bits > capacity:
            self.config.repetition = max(1, capacity // len(watermark_bits))
            print(f"自动调整重复次数为: {self.config.repetition}")
        
        # 重复编码
        repeated_bits = np.tile(watermark_bits, self.config.repetition)
        
        # 分块DCT
        padded_LL, original_shape = self._pad_to_blocks(LL, self.config.block_size)
        blocks = view_as_blocks(padded_LL, (self.config.block_size, self.config.block_size))
        h_blocks, w_blocks = blocks.shape[:2]
        
        # 生成随机嵌入位置
        total_blocks = h_blocks * w_blocks
        embed_positions = np.random.permutation(total_blocks)[:len(repeated_bits)]
        
        # 嵌入水印
        watermarked_blocks = blocks.copy()
        for idx, bit in enumerate(repeated_bits):
            if idx >= len(embed_positions):
                break
            
            pos = embed_positions[idx]
            i, j = pos // w_blocks, pos % w_blocks
            
            # DCT变换
            block = watermarked_blocks[i, j].copy()
            dct_block = cv2.dct(block.astype(np.float32))
            
            # 量化嵌入
            ci, cj = self.config.coeff_pos
            coeff = dct_block[ci, cj]
            
            # 量化间隔嵌入
            step = self.config.strength * 2
            quantized = np.round(coeff / step) * step
            
            if bit == 1:
                if quantized == coeff:
                    quantized += self.config.strength
            else:
                if quantized == coeff:
                    quantized -= self.config.strength
            
            dct_block[ci, cj] = quantized
            
            # 逆DCT
            watermarked_blocks[i, j] = cv2.idct(dct_block)
        
        # 重构LL子带
        watermarked_LL = np.zeros_like(padded_LL)
        for i in range(h_blocks):
            for j in range(w_blocks):
                start_i = i * self.config.block_size
                end_i = start_i + self.config.block_size
                start_j = j * self.config.block_size
                end_j = start_j + self.config.block_size
                
                watermarked_LL[start_i:end_i, start_j:end_j] = watermarked_blocks[i, j]
        
        # 裁剪到原始大小
        watermarked_LL = watermarked_LL[:original_shape[0], :original_shape[1]]
        
        # 逆DWT重构
        watermarked_y = pywt.idwt2((watermarked_LL, (LH, HL, HH)), 'haar')
        watermarked_y = np.clip(watermarked_y, 0, 255)
        
        # 重构图像
        return self._yuv_to_rgb(watermarked_y, u_channel, v_channel)
    
    def extract_watermark(self, watermarked_image: np.ndarray, text_length: int) -> str:
        """提取水印"""
        # 转换颜色空间
        y_channel, _, _ = self._rgb_to_yuv(watermarked_image)
        y_float = y_channel.astype(np.float32)
        
        # DWT分解
        coeffs = pywt.dwt2(y_float, 'haar')
        LL, _ = coeffs
        
        # 分块DCT
        padded_LL, _ = self._pad_to_blocks(LL, self.config.block_size)
        blocks = view_as_blocks(padded_LL, (self.config.block_size, self.config.block_size))
        h_blocks, w_blocks = blocks.shape[:2]
        
        # 提取比特
        total_blocks = h_blocks * w_blocks
        watermark_bits_count = text_length * 8 * self.config.repetition
        embed_positions = np.random.permutation(total_blocks)[:watermark_bits_count]
        
        extracted_bits = []
        for idx in range(min(len(embed_positions), watermark_bits_count)):
            pos = embed_positions[idx]
            i, j = pos // w_blocks, pos % w_blocks
            
            # DCT变换
            block = blocks[i, j]
            dct_block = cv2.dct(block.astype(np.float32))
            
            # 提取比特
            ci, cj = self.config.coeff_pos
            coeff = dct_block[ci, cj]
            
            # 量化解码
            step = self.config.strength * 2
            remainder = coeff % step
            
            if abs(remainder) < self.config.strength:
                extracted_bits.append(0)
            else:
                extracted_bits.append(1)
        
        # 多数投票解码
        extracted_bits = np.array(extracted_bits)
        if len(extracted_bits) >= text_length * 8 * self.config.repetition:
            # 重组并投票
            reshaped_bits = extracted_bits[:text_length * 8 * self.config.repetition].reshape(-1, self.config.repetition)
            decoded_bits = (np.sum(reshaped_bits, axis=1) > self.config.repetition // 2).astype(np.uint8)
        else:
            decoded_bits = extracted_bits[:text_length * 8]
        
        return self._binary_to_text(decoded_bits)


# 攻击函数
def apply_flip_attack(image: np.ndarray) -> Dict[str, np.ndarray]:
    """翻转攻击"""
    return {
        'flip_horizontal': cv2.flip(image, 1),
        'flip_vertical': cv2.flip(image, 0),
        'flip_both': cv2.flip(image, -1)
    }

def apply_rotation_attack(image: np.ndarray) -> Dict[str, np.ndarray]:
    """旋转攻击"""
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    results = {}
    for angle in [5, 10, 15]:
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        results[f'rotate_{angle}'] = rotated
    
    return results

def apply_translation_attack(image: np.ndarray) -> Dict[str, np.ndarray]:
    """平移攻击"""
    h, w = image.shape[:2]
    results = {}
    
    for dx, dy in [(10, 10), (20, 0), (0, 20)]:
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        translated = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        results[f'translate_{dx}_{dy}'] = translated
    
    return results

def apply_crop_attack(image: np.ndarray) -> Dict[str, np.ndarray]:
    """裁剪攻击"""
    h, w = image.shape[:2]
    results = {}
    
    for ratio in [0.8, 0.9, 0.95]:
        crop_h, crop_w = int(h * ratio), int(w * ratio)
        start_h, start_w = (h - crop_h) // 2, (w - crop_w) // 2
        
        cropped = image[start_h:start_h+crop_h, start_w:start_w+crop_w]
        resized = cv2.resize(cropped, (w, h))
        results[f'crop_{ratio}'] = resized
    
    return results

def apply_jpeg_compression(image: np.ndarray) -> Dict[str, np.ndarray]:
    """JPEG压缩攻击"""
    results = {}
    
    for quality in [30, 50, 70]:
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, encoded_img = cv2.imencode('.jpg', image, encode_param)
        decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
        results[f'jpeg_{quality}'] = decoded_img
    
    return results

def apply_noise_attack(image: np.ndarray) -> Dict[str, np.ndarray]:
    """噪声攻击"""
    results = {}
    
    for sigma in [5, 10, 15]:
        noise = np.random.normal(0, sigma, image.shape).astype(np.float32)
        noisy = np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        results[f'noise_{sigma}'] = noisy
    
    return results

def apply_contrast_attack(image: np.ndarray) -> Dict[str, np.ndarray]:
    """对比度攻击"""
    results = {}
    
    for alpha, beta in [(0.8, 10), (1.2, -10), (1.5, 0)]:
        adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        results[f'contrast_{alpha}_{beta}'] = adjusted
    
    return results

def apply_all_attacks(image: np.ndarray) -> Dict[str, np.ndarray]:
    """应用所有攻击"""
    all_attacks = {}
    
    all_attacks.update(apply_flip_attack(image))
    all_attacks.update(apply_rotation_attack(image))
    all_attacks.update(apply_translation_attack(image))
    all_attacks.update(apply_crop_attack(image))
    all_attacks.update(apply_jpeg_compression(image))
    all_attacks.update(apply_noise_attack(image))
    all_attacks.update(apply_contrast_attack(image))
    
    return all_attacks


# 工具函数
def load_image(path: str) -> np.ndarray:
    """加载图像"""
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"无法加载图像: {path}")
    return img

def save_image(image: np.ndarray, path: str) -> None:
    """保存图像"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ext = os.path.splitext(path)[1]
    success, encoded = cv2.imencode(ext or '.png', image)
    if success:
        encoded.tofile(path)
    else:
        raise ValueError(f"无法保存图像: {path}")
