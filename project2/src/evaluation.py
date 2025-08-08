"""
数字水印系统评估模块
提供鲁棒性测试和性能评估功能
"""
import numpy as np
import cv2
from typing import Dict, List, Tuple
import os
import matplotlib.pyplot as plt
from .watermark import BlindWatermark, WatermarkConfig, load_image


def calculate_psnr(original: np.ndarray, watermarked: np.ndarray) -> float:
    """计算峰值信噪比(PSNR)"""
    mse = np.mean((original.astype(np.float32) - watermarked.astype(np.float32)) ** 2)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return psnr


def calculate_ssim(original: np.ndarray, watermarked: np.ndarray) -> float:
    """计算结构相似性指数(SSIM)"""
    # 转换为灰度图
    if len(original.shape) == 3:
        original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        watermarked_gray = cv2.cvtColor(watermarked, cv2.COLOR_BGR2GRAY)
    else:
        original_gray = original
        watermarked_gray = watermarked
    
    # 计算均值
    mu1 = cv2.GaussianBlur(original_gray.astype(np.float32), (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(watermarked_gray.astype(np.float32), (11, 11), 1.5)
    
    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2
    
    # 计算方差和协方差
    sigma1_sq = cv2.GaussianBlur(original_gray.astype(np.float32) * original_gray.astype(np.float32), (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(watermarked_gray.astype(np.float32) * watermarked_gray.astype(np.float32), (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(original_gray.astype(np.float32) * watermarked_gray.astype(np.float32), (11, 11), 1.5) - mu1_mu2
    
    # SSIM计算
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    return np.mean(ssim_map)


def calculate_ber(original_text: str, extracted_text: str) -> float:
    """计算比特错误率(BER)"""
    # 转换为二进制
    orig_binary = ''.join(format(ord(c), '08b') for c in original_text)
    extr_binary = ''.join(format(ord(c), '08b') for c in extracted_text[:len(original_text)])
    
    # 确保长度一致
    min_len = min(len(orig_binary), len(extr_binary))
    if min_len == 0:
        return 1.0
    
    orig_binary = orig_binary[:min_len]
    extr_binary = extr_binary[:min_len]
    
    # 计算错误比特数
    errors = sum(b1 != b2 for b1, b2 in zip(orig_binary, extr_binary))
    return errors / min_len


def evaluate_robustness(watermarked_image_path: str, 
                       original_text: str,
                       config: WatermarkConfig,
                       attacks_dir: str) -> Dict[str, Dict[str, float]]:
    """评估鲁棒性"""
    watermarker = BlindWatermark(config)
    results = {}
    
    # 从原图提取作为基准
    original_watermarked = load_image(watermarked_image_path)
    baseline_text = watermarker.extract_watermark(original_watermarked, len(original_text))
    baseline_ber = calculate_ber(original_text, baseline_text)
    
    results['original'] = {
        'extracted_text': baseline_text,
        'ber': baseline_ber,
        'success': baseline_text == original_text
    }
    
    # 评估各种攻击
    if os.path.exists(attacks_dir):
        for filename in os.listdir(attacks_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                attack_path = os.path.join(attacks_dir, filename)
                attack_name = os.path.splitext(filename)[0]
                
                try:
                    attacked_image = load_image(attack_path)
                    extracted_text = watermarker.extract_watermark(attacked_image, len(original_text))
                    ber = calculate_ber(original_text, extracted_text)
                    
                    results[attack_name] = {
                        'extracted_text': extracted_text,
                        'ber': ber,
                        'success': extracted_text == original_text
                    }
                except Exception as e:
                    results[attack_name] = {
                        'extracted_text': 'ERROR',
                        'ber': 1.0,
                        'success': False,
                        'error': str(e)
                    }
    
    return results


def generate_evaluation_report(original_image_path: str,
                             watermarked_image_path: str,
                             original_text: str,
                             config: WatermarkConfig,
                             attacks_dir: str,
                             output_dir: str = "evaluation"):
    """生成评估报告"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载图像
    original_image = load_image(original_image_path)
    watermarked_image = load_image(watermarked_image_path)
    
    # 图像质量评估
    psnr = calculate_psnr(original_image, watermarked_image)
    ssim = calculate_ssim(original_image, watermarked_image)
    
    # 鲁棒性评估
    robustness_results = evaluate_robustness(
        watermarked_image_path, original_text, config, attacks_dir
    )
    
    # 生成文本报告
    report_path = os.path.join(output_dir, "evaluation_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("数字水印系统评估报告\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("1. 图像质量评估\n")
        f.write("-" * 20 + "\n")
        f.write(f"PSNR: {psnr:.2f} dB\n")
        f.write(f"SSIM: {ssim:.4f}\n\n")
        
        f.write("2. 鲁棒性评估\n")
        f.write("-" * 20 + "\n")
        f.write(f"原始水印文本: {original_text}\n\n")
        
        success_count = 0
        total_count = len(robustness_results)
        
        for attack_name, result in robustness_results.items():
            f.write(f"攻击类型: {attack_name}\n")
            f.write(f"  提取文本: {result['extracted_text']}\n")
            f.write(f"  比特错误率: {result['ber']:.4f}\n")
            f.write(f"  提取成功: {'是' if result['success'] else '否'}\n")
            if 'error' in result:
                f.write(f"  错误信息: {result['error']}\n")
            f.write("\n")
            
            if result['success']:
                success_count += 1
        
        f.write(f"3. 总体统计\n")
        f.write("-" * 20 + "\n")
        f.write(f"总测试数: {total_count}\n")
        f.write(f"成功提取: {success_count}\n")
        f.write(f"成功率: {success_count/total_count*100:.1f}%\n")
    
    print(f"评估报告已保存到: {report_path}")
    
    # 生成可视化图表
    try:
        # BER分布图
        attack_names = []
        ber_values = []
        
        for attack_name, result in robustness_results.items():
            if attack_name != 'original':
                attack_names.append(attack_name)
                ber_values.append(result['ber'])
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(attack_names)), ber_values)
        plt.xlabel('攻击类型')
        plt.ylabel('比特错误率 (BER)')
        plt.title('不同攻击下的比特错误率')
        plt.xticks(range(len(attack_names)), attack_names, rotation=45, ha='right')
        plt.ylim(0, 1)
        
        # 为成功的测试添加不同颜色
        for i, (bar, attack_name) in enumerate(zip(bars, attack_names)):
            if robustness_results[attack_name]['success']:
                bar.set_color('green')
            else:
                bar.set_color('red')
        
        plt.tight_layout()
        chart_path = os.path.join(output_dir, "ber_chart.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"BER图表已保存到: {chart_path}")
        
    except Exception as e:
        print(f"生成图表时出错: {e}")
    
    return {
        'psnr': psnr,
        'ssim': ssim,
        'robustness_results': robustness_results,
        'success_rate': success_count / total_count
    }
