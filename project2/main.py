#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字水印系统主程序
基于DCT变换的数字水印嵌入、提取和鲁棒性测试

Author: Digital Watermark System
Date: 2025-08-08
"""

import os
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
import argparse
from watermark_system import WatermarkSystem
from robustness_test import RobustnessTest
from utils import (create_test_images, print_system_info, validate_dependencies, 
                   create_demo_watermark, ProgressBar)


def demo_basic_watermarking():
    """基本水印嵌入和提取演示"""
    print("\n" + "="*60)
    print("基本水印嵌入和提取演示")
    print("="*60)
    
    # 创建测试图片和水印
    test_images, watermarks = create_test_images()
    
    # 创建水印系统实例
    ws = WatermarkSystem(alpha=0.1)
    
    # 选择第一个测试图片和水印
    test_image_path = test_images[0]
    watermark_path = watermarks[0]
    
    print(f"使用测试图片: {test_image_path}")
    print(f"使用水印: {watermark_path}")
    
    # 创建结果目录
    results_dir = "results/basic_demo"
    os.makedirs(results_dir, exist_ok=True)
    
    # 嵌入水印
    print("\n正在嵌入水印...")
    watermarked_image = ws.embed_watermark(
        test_image_path, 
        watermark_path,
        os.path.join(results_dir, "watermarked.png")
    )
    
    # 提取水印
    print("正在提取水印...")
    extracted_watermark = ws.extract_watermark(
        watermarked_image,
        os.path.join(results_dir, "extracted_watermark.png")
    )
    
    # 计算质量指标
    original_image = cv2.imread(test_image_path, cv2.IMREAD_GRAYSCALE)
    original_watermark = cv2.imread(watermark_path, cv2.IMREAD_GRAYSCALE)
    
    psnr = ws.calculate_psnr(original_image, watermarked_image)
    nc = ws.calculate_nc(original_watermark, extracted_watermark)
    
    print(f"\n质量评估:")
    print(f"  PSNR: {psnr:.2f} dB")
    print(f"  NC: {nc:.4f}")
    
    # 保存对比图
    save_comparison_image(original_image, watermarked_image, original_watermark, 
                         extracted_watermark, os.path.join(results_dir, "comparison.png"))
    
    print(f"\n结果已保存到: {results_dir}")
    
    return watermarked_image, extracted_watermark


def demo_robustness_test():
    """鲁棒性测试演示"""
    print("\n" + "="*60)
    print("鲁棒性测试演示")
    print("="*60)
    
    # 创建测试图片和水印
    test_images, watermarks = create_test_images()
    
    # 创建鲁棒性测试实例
    rt = RobustnessTest()
    
    # 选择测试图片
    test_image = test_images[1]  # 使用棋盘图案
    watermark = watermarks[1]   # 使用圆形水印
    
    print(f"使用测试图片: {test_image}")
    print(f"使用水印: {watermark}")
    
    # 运行完整的鲁棒性测试
    results_dir = "results/robustness_test"
    rt.run_complete_test(test_image, watermark, results_dir)
    
    return rt.results


def demo_different_parameters():
    """不同参数效果演示"""
    print("\n" + "="*60)
    print("不同参数效果演示")
    print("="*60)
    
    # 创建测试图片和水印
    test_images, watermarks = create_test_images()
    test_image_path = test_images[2]  # 纹理图
    watermark_path = watermarks[2]    # Logo水印
    
    # 测试不同的alpha值
    alpha_values = [0.05, 0.1, 0.2, 0.3]
    results_dir = "results/parameter_test"
    os.makedirs(results_dir, exist_ok=True)
    
    original_image = cv2.imread(test_image_path, cv2.IMREAD_GRAYSCALE)
    original_watermark = cv2.imread(watermark_path, cv2.IMREAD_GRAYSCALE)
    
    results = []
    
    print(f"测试不同的嵌入强度参数 (alpha): {alpha_values}")
    
    for alpha in alpha_values:
        print(f"\n测试 alpha = {alpha}")
        
        # 创建水印系统
        ws = WatermarkSystem(alpha=alpha)
        
        # 嵌入和提取水印
        watermarked = ws.embed_watermark(original_image, original_watermark)
        extracted = ws.extract_watermark(watermarked)
        
        # 计算指标
        psnr = ws.calculate_psnr(original_image, watermarked)
        nc = ws.calculate_nc(original_watermark, extracted)
        
        results.append({
            'alpha': alpha,
            'psnr': psnr,
            'nc': nc,
            'watermarked': watermarked,
            'extracted': extracted
        })
        
        print(f"  PSNR: {psnr:.2f} dB, NC: {nc:.4f}")
        
        # 保存结果
        cv2.imwrite(os.path.join(results_dir, f"watermarked_alpha_{alpha}.png"), watermarked)
        cv2.imwrite(os.path.join(results_dir, f"extracted_alpha_{alpha}.png"), extracted)
    
    # 创建参数对比图
    create_parameter_comparison_plot(results, os.path.join(results_dir, "parameter_comparison.png"))
    
    print(f"\n参数测试结果已保存到: {results_dir}")
    
    return results


def interactive_demo():
    """交互式演示"""
    print("\n" + "="*60)
    print("交互式演示模式")
    print("="*60)
    
    while True:
        print("\n请选择操作:")
        print("1. 基本水印嵌入和提取")
        print("2. 鲁棒性测试")
        print("3. 参数效果测试") 
        print("4. 自定义图片测试")
        print("5. 创建演示水印")
        print("0. 退出")
        
        try:
            choice = input("\n请输入选择 (0-5): ").strip()
            
            if choice == '0':
                print("感谢使用数字水印系统!")
                break
            elif choice == '1':
                demo_basic_watermarking()
            elif choice == '2':
                demo_robustness_test()
            elif choice == '3':
                demo_different_parameters()
            elif choice == '4':
                custom_image_test()
            elif choice == '5':
                create_custom_watermark()
            else:
                print("无效选择，请重新输入。")
                
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            print("请检查输入并重试")


def custom_image_test():
    """自定义图片测试"""
    print("\n自定义图片测试")
    print("-" * 30)
    
    # 获取用户输入
    image_path = input("请输入图片路径 (或按回车使用默认测试图片): ").strip()
    watermark_path = input("请输入水印路径 (或按回车使用默认水印): ").strip()
    
    # 使用默认图片
    if not image_path:
        test_images, watermarks = create_test_images()
        image_path = test_images[0]
        print(f"使用默认测试图片: {image_path}")
    
    if not watermark_path:
        if 'watermarks' not in locals():
            test_images, watermarks = create_test_images()
        watermark_path = watermarks[0]
        print(f"使用默认水印: {watermark_path}")
    
    # 验证文件存在
    if not os.path.exists(image_path):
        print(f"图片文件不存在: {image_path}")
        return
    
    if not os.path.exists(watermark_path):
        print(f"水印文件不存在: {watermark_path}")
        return
    
    # 获取嵌入强度
    try:
        alpha = float(input("请输入嵌入强度 alpha (0.05-0.5, 默认0.1): ") or "0.1")
        alpha = max(0.05, min(0.5, alpha))  # 限制范围
    except ValueError:
        alpha = 0.1
    
    print(f"\n使用参数: alpha={alpha}")
    
    # 执行水印嵌入和提取
    ws = WatermarkSystem(alpha=alpha)
    
    results_dir = "results/custom_test"
    os.makedirs(results_dir, exist_ok=True)
    
    try:
        print("正在处理...")
        
        # 嵌入水印
        watermarked = ws.embed_watermark(image_path, watermark_path)
        
        # 提取水印
        extracted = ws.extract_watermark(watermarked)
        
        # 计算指标
        original_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        original_watermark = cv2.imread(watermark_path, cv2.IMREAD_GRAYSCALE)
        
        psnr = ws.calculate_psnr(original_image, watermarked)
        nc = ws.calculate_nc(original_watermark, extracted)
        
        # 保存结果
        cv2.imwrite(os.path.join(results_dir, "custom_watermarked.png"), watermarked)
        cv2.imwrite(os.path.join(results_dir, "custom_extracted.png"), extracted)
        
        # 保存对比图
        save_comparison_image(original_image, watermarked, original_watermark, 
                             extracted, os.path.join(results_dir, "custom_comparison.png"))
        
        print(f"\n处理完成!")
        print(f"PSNR: {psnr:.2f} dB")
        print(f"NC: {nc:.4f}")
        print(f"结果已保存到: {results_dir}")
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")


def create_custom_watermark():
    """创建自定义水印"""
    print("\n创建自定义水印")
    print("-" * 30)
    
    text = input("请输入水印文字 (默认: DEMO): ").strip() or "DEMO"
    
    try:
        size = int(input("请输入水印大小 (像素, 默认64): ") or "64")
        size = max(32, min(256, size))  # 限制范围
    except ValueError:
        size = 64
    
    # 创建水印
    watermark = create_demo_watermark(text, (size, size))
    
    # 保存水印
    watermark_dir = "test_images"
    os.makedirs(watermark_dir, exist_ok=True)
    watermark_path = os.path.join(watermark_dir, f"custom_watermark_{text}.png")
    cv2.imwrite(watermark_path, watermark)
    
    print(f"自定义水印已创建: {watermark_path}")
    
    # 显示水印
    plt.figure(figsize=(4, 4))
    plt.imshow(watermark, cmap='gray')
    plt.title(f"自定义水印: {text}")
    plt.axis('off')
    
    preview_path = os.path.join(watermark_dir, f"custom_watermark_{text}_preview.png")
    plt.savefig(preview_path, bbox_inches='tight', dpi=150)
    plt.close()
    
    print(f"水印预览已保存: {preview_path}")


def save_comparison_image(original, watermarked, original_watermark, extracted_watermark, output_path):
    """保存对比图"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    axes[0, 0].imshow(original, cmap='gray')
    axes[0, 0].set_title('原始图片')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(watermarked, cmap='gray')
    axes[0, 1].set_title('带水印图片')
    axes[0, 1].axis('off')
    
    axes[1, 0].imshow(original_watermark, cmap='gray')
    axes[1, 0].set_title('原始水印')
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(extracted_watermark, cmap='gray')
    axes[1, 1].set_title('提取的水印')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def create_parameter_comparison_plot(results, output_path):
    """创建参数对比图"""
    alphas = [r['alpha'] for r in results]
    psnrs = [r['psnr'] for r in results]
    ncs = [r['nc'] for r in results]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # PSNR图
    ax1.plot(alphas, psnrs, 'b-o', linewidth=2, markersize=8)
    ax1.set_xlabel('嵌入强度 (α)')
    ax1.set_ylabel('PSNR (dB)')
    ax1.set_title('嵌入强度 vs PSNR')
    ax1.grid(True, alpha=0.3)
    
    # NC图
    ax2.plot(alphas, ncs, 'r-s', linewidth=2, markersize=8)
    ax2.set_xlabel('嵌入强度 (α)')
    ax2.set_ylabel('归一化相关系数 (NC)')
    ax2.set_title('嵌入强度 vs NC')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def main():
    """主程序"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='数字水印系统')
    parser.add_argument('--mode', choices=['demo', 'robustness', 'interactive'], 
                       default='interactive', help='运行模式')
    parser.add_argument('--image', type=str, help='输入图片路径')
    parser.add_argument('--watermark', type=str, help='水印图片路径')
    parser.add_argument('--alpha', type=float, default=0.1, help='嵌入强度')
    parser.add_argument('--output', type=str, default='results', help='输出目录')
    
    args = parser.parse_args()
    
    # 打印系统信息
    print_system_info()
    
    # 验证依赖
    if not validate_dependencies():
        sys.exit(1)
    
    # 根据模式运行
    try:
        if args.mode == 'demo':
            demo_basic_watermarking()
        elif args.mode == 'robustness':
            demo_robustness_test()
        elif args.mode == 'interactive':
            interactive_demo()
        else:
            print(f"未知运行模式: {args.mode}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
