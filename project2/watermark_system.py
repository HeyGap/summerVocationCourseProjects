import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
from scipy.fftpack import dct, idct
import os


class WatermarkSystem:
    """数字水印系统 - 基于DCT变换的频域水印嵌入和提取"""
    
    def __init__(self, alpha=0.1, block_size=8):
        """
        初始化水印系统
        
        Args:
            alpha (float): 水印嵌入强度
            block_size (int): DCT变换块大小
        """
        self.alpha = alpha
        self.block_size = block_size
        
    def _dct2(self, block):
        """二维DCT变换"""
        return dct(dct(block.T, norm='ortho').T, norm='ortho')
    
    def _idct2(self, block):
        """二维IDCT变换"""
        return idct(idct(block.T, norm='ortho').T, norm='ortho')
    
    def _embed_watermark_block(self, dct_block, watermark_bit):
        """在DCT块中嵌入一个水印位"""
        # 选择中频系数进行嵌入 (避免低频和高频)
        pos1 = (3, 4)  # 中频位置1
        pos2 = (4, 3)  # 中频位置2
        
        if watermark_bit == 1:
            # 如果水印位为1，使pos1的系数大于pos2
            if dct_block[pos1] <= dct_block[pos2]:
                avg = (dct_block[pos1] + dct_block[pos2]) / 2
                dct_block[pos1] = avg + self.alpha
                dct_block[pos2] = avg - self.alpha
        else:
            # 如果水印位为0，使pos2的系数大于pos1
            if dct_block[pos2] <= dct_block[pos1]:
                avg = (dct_block[pos1] + dct_block[pos2]) / 2
                dct_block[pos1] = avg - self.alpha
                dct_block[pos2] = avg + self.alpha
        
        return dct_block
    
    def _extract_watermark_bit(self, dct_block):
        """从DCT块中提取一个水印位"""
        pos1 = (3, 4)
        pos2 = (4, 3)
        
        if dct_block[pos1] > dct_block[pos2]:
            return 1
        else:
            return 0
    
    def _prepare_watermark(self, watermark_path, target_size):
        """准备水印数据"""
        if isinstance(watermark_path, str):
            # 从文件加载水印
            watermark = cv2.imread(watermark_path, cv2.IMREAD_GRAYSCALE)
            if watermark is None:
                raise ValueError(f"无法加载水印图片: {watermark_path}")
        else:
            # 直接使用传入的数组
            watermark = watermark_path
            
        # 调整水印大小
        watermark = cv2.resize(watermark, target_size)
        
        # 二值化
        _, watermark_binary = cv2.threshold(watermark, 128, 1, cv2.THRESH_BINARY)
        
        return watermark_binary.flatten()
    
    def embed_watermark(self, image_path, watermark_path, output_path=None):
        """
        嵌入水印到图片中
        
        Args:
            image_path (str): 原始图片路径
            watermark_path (str): 水印图片路径
            output_path (str): 输出路径，如果为None则不保存
            
        Returns:
            numpy.ndarray: 带水印的图片
        """
        # 加载原始图片
        if isinstance(image_path, str):
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"无法加载图片: {image_path}")
        else:
            image = image_path.copy()
            
        # 确保图片尺寸是block_size的倍数
        h, w = image.shape
        new_h = (h // self.block_size) * self.block_size
        new_w = (w // self.block_size) * self.block_size
        image = cv2.resize(image, (new_w, new_h))
        
        # 计算可嵌入的水印位数
        max_watermark_bits = (new_h // self.block_size) * (new_w // self.block_size)
        watermark_size = int(np.sqrt(max_watermark_bits))
        
        # 准备水印
        watermark_bits = self._prepare_watermark(watermark_path, (watermark_size, watermark_size))
        
        # 转换为float类型进行DCT变换
        image_float = image.astype(np.float32)
        watermarked_image = image_float.copy()
        
        bit_index = 0
        # 分块处理
        for i in range(0, new_h, self.block_size):
            for j in range(0, new_w, self.block_size):
                # 提取8x8块
                block = image_float[i:i+self.block_size, j:j+self.block_size]
                
                # DCT变换
                dct_block = self._dct2(block)
                
                # 嵌入水印位
                if bit_index < len(watermark_bits):
                    dct_block = self._embed_watermark_block(dct_block, watermark_bits[bit_index])
                    bit_index += 1
                
                # IDCT变换
                watermarked_block = self._idct2(dct_block)
                watermarked_image[i:i+self.block_size, j:j+self.block_size] = watermarked_block
        
        # 转换回uint8类型
        watermarked_image = np.clip(watermarked_image, 0, 255).astype(np.uint8)
        
        # 保存结果
        if output_path:
            cv2.imwrite(output_path, watermarked_image)
            print(f"带水印图片已保存到: {output_path}")
        
        return watermarked_image
    
    def extract_watermark(self, watermarked_image_path, output_path=None):
        """
        从图片中提取水印
        
        Args:
            watermarked_image_path (str or numpy.ndarray): 带水印的图片路径或数组
            output_path (str): 提取的水印保存路径
            
        Returns:
            numpy.ndarray: 提取的水印图片
        """
        # 加载带水印的图片
        if isinstance(watermarked_image_path, str):
            watermarked_image = cv2.imread(watermarked_image_path, cv2.IMREAD_GRAYSCALE)
            if watermarked_image is None:
                raise ValueError(f"无法加载图片: {watermarked_image_path}")
        else:
            watermarked_image = watermarked_image_path.copy()
        
        h, w = watermarked_image.shape
        new_h = (h // self.block_size) * self.block_size
        new_w = (w // self.block_size) * self.block_size
        watermarked_image = cv2.resize(watermarked_image, (new_w, new_h))
        
        # 计算水印大小
        max_watermark_bits = (new_h // self.block_size) * (new_w // self.block_size)
        watermark_size = int(np.sqrt(max_watermark_bits))
        
        # 转换为float类型
        watermarked_image_float = watermarked_image.astype(np.float32)
        
        extracted_bits = []
        
        # 分块提取
        for i in range(0, new_h, self.block_size):
            for j in range(0, new_w, self.block_size):
                # 提取8x8块
                block = watermarked_image_float[i:i+self.block_size, j:j+self.block_size]
                
                # DCT变换
                dct_block = self._dct2(block)
                
                # 提取水印位
                bit = self._extract_watermark_bit(dct_block)
                extracted_bits.append(bit)
                
                if len(extracted_bits) >= watermark_size * watermark_size:
                    break
            if len(extracted_bits) >= watermark_size * watermark_size:
                break
        
        # 重构水印图片
        extracted_watermark = np.array(extracted_bits[:watermark_size*watermark_size])
        extracted_watermark = extracted_watermark.reshape(watermark_size, watermark_size)
        extracted_watermark = (extracted_watermark * 255).astype(np.uint8)
        
        # 放大水印以便观察
        extracted_watermark = cv2.resize(extracted_watermark, (128, 128), interpolation=cv2.INTER_NEAREST)
        
        # 保存结果
        if output_path:
            cv2.imwrite(output_path, extracted_watermark)
            print(f"提取的水印已保存到: {output_path}")
        
        return extracted_watermark
    
    def calculate_psnr(self, original, watermarked):
        """计算PSNR值"""
        mse = np.mean((original.astype(float) - watermarked.astype(float)) ** 2)
        if mse == 0:
            return float('inf')
        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        return psnr
    
    def calculate_nc(self, original_watermark, extracted_watermark):
        """计算归一化相关系数NC"""
        # 确保两个水印尺寸相同
        if original_watermark.shape != extracted_watermark.shape:
            extracted_watermark = cv2.resize(extracted_watermark, 
                                           (original_watermark.shape[1], original_watermark.shape[0]))
        
        original_flat = original_watermark.flatten().astype(float)
        extracted_flat = extracted_watermark.flatten().astype(float)
        
        # 归一化到[0,1]
        original_flat = original_flat / 255.0
        extracted_flat = extracted_flat / 255.0
        
        numerator = np.sum(original_flat * extracted_flat)
        denominator = np.sqrt(np.sum(original_flat ** 2) * np.sum(extracted_flat ** 2))
        
        if denominator == 0:
            return 0
        
        nc = numerator / denominator
        return nc
