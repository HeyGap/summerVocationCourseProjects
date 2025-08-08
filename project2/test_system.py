#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字水印系统测试脚本
快速验证所有功能是否正常工作
"""

import os
import cv2
import numpy as np
from watermark_system import WatermarkSystem
from robustness_test import RobustnessTest
from utils import create_test_images, print_system_info


def test_basic_functionality():
    """测试基本功能"""
    print("="*50)
    print("测试基本水印功能")
    print("="*50)
    
    # 创建测试图片
    test_images, watermarks = create_test_images()
    
    # 创建水印系统
    ws = WatermarkSystem(alpha=0.1)
    
    # 测试嵌入和提取
    original_image = cv2.imread(test_images[0], cv2.IMREAD_GRAYSCALE)
    watermark = cv2.imread(watermarks[0], cv2.IMREAD_GRAYSCALE)
    
    print(f"原始图片尺寸: {original_image.shape}")
    print(f"水印尺寸: {watermark.shape}")
    
    # 嵌入水印
    watermarked = ws.embed_watermark(original_image, watermark)
    print(f"水印嵌入完成")
    
    # 提取水印
    extracted = ws.extract_watermark(watermarked)
    print(f"水印提取完成")
    
    # 计算指标
    psnr = ws.calculate_psnr(original_image, watermarked)
    nc = ws.calculate_nc(watermark, extracted)
    
    print(f"PSNR: {psnr:.2f} dB")
    print(f"NC: {nc:.4f}")
    
    # 判断成功标准
    if psnr > 30 and nc > 0.5:
        print("✓ 基本功能测试通过")
        return True
    else:
        print("✗ 基本功能测试失败")
        return False


def test_robustness_sample():
    """测试鲁棒性（简化版）"""
    print("\n" + "="*50)
    print("测试鲁棒性（样本测试）")
    print("="*50)
    
    # 创建测试图片
    test_images, watermarks = create_test_images()
    
    # 创建测试实例
    rt = RobustnessTest()
    original_image = cv2.imread(test_images[1], cv2.IMREAD_GRAYSCALE)
    watermark = cv2.imread(watermarks[1], cv2.IMREAD_GRAYSCALE)
    
    # 嵌入水印
    watermarked = rt.watermark_system.embed_watermark(original_image, watermark)
    
    print("测试几个常见攻击...")
    
    # 测试高斯模糊
    result1 = rt.test_attack(original_image, watermarked, watermark, 
                            rt.gaussian_blur_attack, "高斯模糊", kernel_size=3)
    
    # 测试JPEG压缩
    result2 = rt.test_attack(original_image, watermarked, watermark,
                            rt.jpeg_compression_attack, "JPEG压缩", quality=70)
    
    # 测试缩放
    result3 = rt.test_attack(original_image, watermarked, watermark,
                            rt.scaling_attack, "缩放", scale_factor=0.9)
    
    # 评估结果
    avg_nc = (result1['nc'] + result2['nc'] + result3['nc']) / 3
    
    if avg_nc > 0.3:
        print(f"✓ 鲁棒性测试通过 (平均NC: {avg_nc:.4f})")
        return True
    else:
        print(f"✗ 鲁棒性测试需要改进 (平均NC: {avg_nc:.4f})")
        return False


def test_different_images():
    """测试不同类型的图片"""
    print("\n" + "="*50)
    print("测试不同类型图片")
    print("="*50)
    
    test_images, watermarks = create_test_images()
    ws = WatermarkSystem(alpha=0.12)
    
    results = []
    
    for i, (img_path, img_name) in enumerate(zip(test_images, 
                                                ["渐变图", "棋盘图", "纹理图"])):
        print(f"测试{img_name}...")
        
        original = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        watermark = cv2.imread(watermarks[i % len(watermarks)], cv2.IMREAD_GRAYSCALE)
        
        watermarked = ws.embed_watermark(original, watermark)
        extracted = ws.extract_watermark(watermarked)
        
        psnr = ws.calculate_psnr(original, watermarked)
        nc = ws.calculate_nc(watermark, extracted)
        
        results.append({'name': img_name, 'psnr': psnr, 'nc': nc})
        print(f"  {img_name}: PSNR={psnr:.2f}dB, NC={nc:.4f}")
    
    avg_psnr = np.mean([r['psnr'] for r in results])
    avg_nc = np.mean([r['nc'] for r in results])
    
    print(f"平均PSNR: {avg_psnr:.2f}dB")
    print(f"平均NC: {avg_nc:.4f}")
    
    if avg_psnr > 35 and avg_nc > 0.4:
        print("✓ 多图片测试通过")
        return True
    else:
        print("✗ 多图片测试需要改进")
        return False


def main():
    """主测试函数"""
    print_system_info()
    
    test_results = []
    
    # 运行各项测试
    test_results.append(test_basic_functionality())
    test_results.append(test_robustness_sample())
    test_results.append(test_different_images())
    
    # 总结测试结果
    print("\n" + "="*50)
    print("测试结果总结")
    print("="*50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("所有测试都通过了")
    else:
        print("有部分测试未通过")
    
    return passed == total


if __name__ == "__main__":
    main()
