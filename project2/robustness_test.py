import numpy as np
import cv2
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  
matplotlib.rcParams['axes.unicode_minus'] = False
import os
from watermark_system import WatermarkSystem
import random
import datetime


class RobustnessTest:
    """鲁棒性测试类 - 测试水印在各种攻击下的生存能力"""
    
    def __init__(self, watermark_system=None):
        """
        初始化鲁棒性测试
        
        Args:
            watermark_system: 水印系统实例
        """
        self.watermark_system = watermark_system or WatermarkSystem()
        self.results = []
    
    def flip_attack(self, image, flip_type=1):
        """
        翻转攻击
        
        Args:
            image: 输入图像
            flip_type: 翻转类型 (0:垂直翻转, 1:水平翻转, -1:水平垂直翻转)
        """
        return cv2.flip(image, flip_type)
    
    def translation_attack(self, image, tx=10, ty=10):
        """
        平移攻击
        
        Args:
            image: 输入图像
            tx, ty: x和y方向的平移像素数
        """
        h, w = image.shape
        M = np.float32([[1, 0, tx], [0, 1, ty]])
        translated = cv2.warpAffine(image, M, (w, h))
        return translated
    
    def rotation_attack(self, image, angle=15):
        """
        旋转攻击
        
        Args:
            image: 输入图像
            angle: 旋转角度
        """
        h, w = image.shape
        center = (w//2, h//2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h))
        return rotated
    
    def scaling_attack(self, image, scale_factor=0.8):
        """
        缩放攻击
        
        Args:
            image: 输入图像
            scale_factor: 缩放因子
        """
        h, w = image.shape
        new_h, new_w = int(h * scale_factor), int(w * scale_factor)
        scaled = cv2.resize(image, (new_w, new_h))
        # 恢复到原始尺寸
        scaled_back = cv2.resize(scaled, (w, h))
        return scaled_back
    
    def contrast_attack(self, image, alpha=1.5):
        """
        对比度调整攻击
        
        Args:
            image: 输入图像
            alpha: 对比度调整因子
        """
        # 转换为PIL图像进行对比度调整
        pil_image = Image.fromarray(image)
        enhancer = ImageEnhance.Contrast(pil_image)
        enhanced = enhancer.enhance(alpha)
        return np.array(enhanced)
    
    def brightness_attack(self, image, beta=30):
        """
        亮度调整攻击
        
        Args:
            image: 输入图像
            beta: 亮度调整值
        """
        brightened = cv2.add(image, beta)
        return np.clip(brightened, 0, 255).astype(np.uint8)
    
    def gaussian_blur_attack(self, image, kernel_size=5):
        """
        高斯模糊攻击
        
        Args:
            image: 输入图像
            kernel_size: 模糊核大小
        """
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    
    def noise_attack(self, image, noise_type='gaussian', intensity=25):
        """
        噪声攻击
        
        Args:
            image: 输入图像
            noise_type: 噪声类型 ('gaussian', 'salt_pepper')
            intensity: 噪声强度
        """
        if noise_type == 'gaussian':
            noise = np.random.normal(0, intensity, image.shape)
            noisy = image.astype(float) + noise
            return np.clip(noisy, 0, 255).astype(np.uint8)
        
        elif noise_type == 'salt_pepper':
            noisy = image.copy()
            h, w = image.shape
            
            # 椒噪声
            num_pepper = int(h * w * intensity / 1000)
            coords = [np.random.randint(0, i-1, num_pepper) for i in image.shape]
            noisy[coords[0], coords[1]] = 0
            
            # 盐噪声
            num_salt = int(h * w * intensity / 1000)
            coords = [np.random.randint(0, i-1, num_salt) for i in image.shape]
            noisy[coords[0], coords[1]] = 255
            
            return noisy
        
        return image
    
    def jpeg_compression_attack(self, image, quality=50):
        """
        JPEG压缩攻击
        
        Args:
            image: 输入图像
            quality: JPEG质量 (1-100)
        """
        # 使用OpenCV进行JPEG编码和解码
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, encimg = cv2.imencode('.jpg', image, encode_param)
        compressed = cv2.imdecode(encimg, cv2.IMREAD_GRAYSCALE)
        return compressed
    
    def cropping_attack(self, image, crop_ratio=0.2):
        """
        裁剪攻击
        
        Args:
            image: 输入图像
            crop_ratio: 裁剪比例
        """
        h, w = image.shape
        crop_h, crop_w = int(h * crop_ratio), int(w * crop_ratio)
        
        # 随机选择裁剪起始点
        start_h = random.randint(0, max(1, h - crop_h - 1))
        start_w = random.randint(0, max(1, w - crop_w - 1))
        
        # 裁剪
        cropped = image[start_h:start_h+h-crop_h, start_w:start_w+w-crop_w]
        
        # 恢复到原始尺寸
        restored = cv2.resize(cropped, (w, h))
        return restored
    
    def test_attack(self, original_image, watermarked_image, watermark, attack_func, attack_name, **kwargs):
        """
        测试单个攻击
        
        Args:
            original_image: 原始图像
            watermarked_image: 带水印图像
            watermark: 原始水印
            attack_func: 攻击函数
            attack_name: 攻击名称
            **kwargs: 攻击参数
        """
        print(f"正在测试: {attack_name}")
        
        # 执行攻击
        attacked_image = attack_func(watermarked_image, **kwargs)
        
        # 提取水印
        extracted_watermark = self.watermark_system.extract_watermark(attacked_image)
        
        # 计算评估指标
        psnr = self.watermark_system.calculate_psnr(watermarked_image, attacked_image)
        nc = self.watermark_system.calculate_nc(watermark, extracted_watermark)
        
        # 计算BER (位错误率)
        watermark_binary = (cv2.resize(watermark, extracted_watermark.shape) > 128).astype(bool)
        extracted_binary = (extracted_watermark > 128).astype(bool)
        ber = np.sum(watermark_binary != extracted_binary) / watermark_binary.size
        
        result = {
            'attack': attack_name,
            'parameters': kwargs,
            'psnr': psnr,
            'nc': nc,
            'ber': ber,
            'attacked_image': attacked_image,
            'extracted_watermark': extracted_watermark
        }
        
        self.results.append(result)
        
        print(f"  PSNR: {psnr:.2f} dB")
        print(f"  NC: {nc:.4f}")
        print(f"  BER: {ber:.4f}")
        print()
        
        return result
    
    def run_complete_test(self, image_path, watermark_path, output_dir='results'):
        """
        运行完整的鲁棒性测试
        
        Args:
            image_path: 测试图片路径
            watermark_path: 水印图片路径
            output_dir: 结果输出目录
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载图片
        original_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        watermark = cv2.imread(watermark_path, cv2.IMREAD_GRAYSCALE)
        
        if original_image is None or watermark is None:
            raise ValueError("无法加载图片或水印")
        
        # 嵌入水印
        print("嵌入水印...")
        watermarked_image = self.watermark_system.embed_watermark(original_image, watermark)
        
        # 保存带水印图片
        cv2.imwrite(os.path.join(output_dir, 'watermarked_image.png'), watermarked_image)
        
        # 计算原始PSNR
        psnr_original = self.watermark_system.calculate_psnr(original_image, watermarked_image)
        print(f"原始图像PSNR: {psnr_original:.2f} dB\n")
        
        # 清空之前的结果
        self.results = []
        
        # 几何攻击测试
        print("=== 几何攻击测试 ===")
        self.test_attack(original_image, watermarked_image, watermark, 
                        self.flip_attack, "水平翻转", flip_type=1)
        
        self.test_attack(original_image, watermarked_image, watermark, 
                        self.flip_attack, "垂直翻转", flip_type=0)
        
        self.test_attack(original_image, watermarked_image, watermark, 
                        self.translation_attack, "平移攻击", tx=20, ty=20)
        
        self.test_attack(original_image, watermarked_image, watermark, 
                        self.rotation_attack, "旋转攻击", angle=15)
        
        self.test_attack(original_image, watermarked_image, watermark, 
                        self.scaling_attack, "缩放攻击", scale_factor=0.8)
        
        # 图像处理攻击测试
        print("=== 图像处理攻击测试 ===")
        self.test_attack(original_image, watermarked_image, watermark, 
                        self.contrast_attack, "对比度调整", alpha=1.5)
        
        self.test_attack(original_image, watermarked_image, watermark, 
                        self.brightness_attack, "亮度调整", beta=30)
        
        self.test_attack(original_image, watermarked_image, watermark, 
                        self.gaussian_blur_attack, "高斯模糊", kernel_size=5)
        
        self.test_attack(original_image, watermarked_image, watermark, 
                        self.noise_attack, "高斯噪声", noise_type='gaussian', intensity=25)
        
        self.test_attack(original_image, watermarked_image, watermark, 
                        self.noise_attack, "椒盐噪声", noise_type='salt_pepper', intensity=10)
        
        # 压缩攻击测试
        print("=== 压缩攻击测试 ===")
        for quality in [30, 50, 70]:
            self.test_attack(original_image, watermarked_image, watermark, 
                            self.jpeg_compression_attack, f"JPEG压缩(Q={quality})", quality=quality)
        
        # 裁剪攻击测试
        print("=== 裁剪攻击测试 ===")
        for ratio in [0.1, 0.2, 0.3]:
            self.test_attack(original_image, watermarked_image, watermark, 
                            self.cropping_attack, f"裁剪攻击({int(ratio*100)}%)", crop_ratio=ratio)
        
        # 生成测试报告
        self.generate_report(output_dir)
        
        # 保存可视化结果
        self.save_visualization(watermark, output_dir)
        
        print(f"测试完成！结果已保存到 {output_dir} 目录")
    
    def generate_report(self, output_dir):
        """生成测试报告"""
        report_path = os.path.join(output_dir, 'robustness_report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("数字水印鲁棒性测试报告\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"测试时间: {datetime.datetime.now()}\n")
            f.write(f"水印系统参数: alpha={self.watermark_system.alpha}, block_size={self.watermark_system.block_size}\n\n")
            
            f.write("测试结果摘要:\n")
            f.write("-" * 30 + "\n")
            f.write(f"{'攻击类型':<15} {'PSNR(dB)':<10} {'NC':<8} {'BER':<8}\n")
            f.write("-" * 50 + "\n")
            
            for result in self.results:
                f.write(f"{result['attack']:<15} {result['psnr']:<10.2f} {result['nc']:<8.4f} {result['ber']:<8.4f}\n")
            
            f.write("\n详细分析:\n")
            f.write("-" * 30 + "\n")
            
            # 分类统计
            geometric_attacks = [r for r in self.results if any(x in r['attack'] for x in ['翻转', '平移', '旋转', '缩放'])]
            processing_attacks = [r for r in self.results if any(x in r['attack'] for x in ['对比度', '亮度', '模糊', '噪声'])]
            compression_attacks = [r for r in self.results if 'JPEG' in r['attack']]
            cropping_attacks = [r for r in self.results if '裁剪' in r['attack']]
            
            categories = [
                ("几何攻击", geometric_attacks),
                ("图像处理攻击", processing_attacks), 
                ("压缩攻击", compression_attacks),
                ("裁剪攻击", cropping_attacks)
            ]
            
            for cat_name, cat_results in categories:
                if cat_results:
                    avg_nc = np.mean([r['nc'] for r in cat_results])
                    avg_ber = np.mean([r['ber'] for r in cat_results])
                    f.write(f"{cat_name}: 平均NC={avg_nc:.4f}, 平均BER={avg_ber:.4f}\n")
            
        print(f"测试报告已保存到: {report_path}")
    
    def save_visualization(self, original_watermark, output_dir):
        """保存可视化结果"""
        if not self.results:
            return
        
        # 创建可视化图表
        fig, axes = plt.subplots(4, 4, figsize=(16, 16))
        axes = axes.flatten()
        
        # 显示前16个测试结果
        for i, result in enumerate(self.results[:16]):
            if i >= 16:
                break
                
            ax = axes[i]
            ax.imshow(result['extracted_watermark'], cmap='gray')
            ax.set_title(f"{result['attack']}\nNC:{result['nc']:.3f}, BER:{result['ber']:.3f}")
            ax.axis('off')
        
        # 隐藏多余的子图
        for i in range(len(self.results), 16):
            axes[i].axis('off')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'extracted_watermarks.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
        # 创建性能图表
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        
        attack_names = [r['attack'] for r in self.results]
        psnr_values = [r['psnr'] for r in self.results]
        nc_values = [r['nc'] for r in self.results]
        ber_values = [r['ber'] for r in self.results]
        
        # PSNR图
        ax1.bar(range(len(attack_names)), psnr_values)
        ax1.set_title('PSNR值')
        ax1.set_ylabel('PSNR (dB)')
        ax1.set_xticks(range(len(attack_names)))
        ax1.set_xticklabels(attack_names, rotation=45, ha='right')
        
        # NC图
        ax2.bar(range(len(attack_names)), nc_values)
        ax2.set_title('归一化相关系数(NC)')
        ax2.set_ylabel('NC')
        ax2.set_xticks(range(len(attack_names)))
        ax2.set_xticklabels(attack_names, rotation=45, ha='right')
        ax2.axhline(y=0.7, color='r', linestyle='--', label='良好阈值(0.7)')
        ax2.legend()
        
        # BER图
        ax3.bar(range(len(attack_names)), ber_values)
        ax3.set_title('位错误率(BER)')
        ax3.set_ylabel('BER')
        ax3.set_xticks(range(len(attack_names)))
        ax3.set_xticklabels(attack_names, rotation=45, ha='right')
        ax3.axhline(y=0.3, color='r', linestyle='--', label='可接受阈值(0.3)')
        ax3.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'performance_metrics.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"可视化结果已保存到: {output_dir}")


if __name__ == "__main__":
    # 创建测试实例
    rt = RobustnessTest()
    
    # 运行简单测试
    print("运行鲁棒性测试模块...")
    print("请使用 main.py 运行完整测试")
