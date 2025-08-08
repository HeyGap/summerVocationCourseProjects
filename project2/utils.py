import numpy as np
import cv2
import os
import matplotlib.pyplot as plt
from PIL import Image


def create_test_images(output_dir='test_images'):
    """创建测试用的图片和水印"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建测试图片1: 渐变图
    img1 = np.zeros((512, 512), dtype=np.uint8)
    for i in range(512):
        for j in range(512):
            img1[i, j] = int(255 * (i + j) / (512 + 512))
    cv2.imwrite(os.path.join(output_dir, 'test_gradient.png'), img1)
    
    # 创建测试图片2: 棋盘图案
    img2 = np.zeros((512, 512), dtype=np.uint8)
    square_size = 64
    for i in range(0, 512, square_size):
        for j in range(0, 512, square_size):
            if ((i // square_size) + (j // square_size)) % 2 == 0:
                img2[i:i+square_size, j:j+square_size] = 255
    cv2.imwrite(os.path.join(output_dir, 'test_checkerboard.png'), img2)
    
    # 创建测试图片3: 随机纹理
    np.random.seed(42)
    img3 = np.random.randint(0, 256, (512, 512), dtype=np.uint8)
    img3 = cv2.GaussianBlur(img3, (15, 15), 0)
    cv2.imwrite(os.path.join(output_dir, 'test_texture.png'), img3)
    
    # 创建水印图片: 简单的文字水印
    watermark = np.zeros((64, 64), dtype=np.uint8)
    cv2.putText(watermark, 'WM', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    cv2.imwrite(os.path.join(output_dir, 'watermark_text.png'), watermark)
    
    # 创建水印图片: 圆形图案
    watermark2 = np.zeros((64, 64), dtype=np.uint8)
    cv2.circle(watermark2, (32, 32), 25, 255, -1)
    cv2.circle(watermark2, (32, 32), 15, 0, -1)
    cv2.imwrite(os.path.join(output_dir, 'watermark_circle.png'), watermark2)
    
    # 创建水印图片: Logo样式
    watermark3 = np.zeros((64, 64), dtype=np.uint8)
    # 画一个简单的logo
    cv2.rectangle(watermark3, (10, 10), (54, 54), 255, 2)
    cv2.line(watermark3, (10, 32), (54, 32), 255, 2)
    cv2.line(watermark3, (32, 10), (32, 54), 255, 2)
    cv2.imwrite(os.path.join(output_dir, 'watermark_logo.png'), watermark3)
    
    print(f"测试图片已创建到 {output_dir} 目录")
    return [
        os.path.join(output_dir, 'test_gradient.png'),
        os.path.join(output_dir, 'test_checkerboard.png'),
        os.path.join(output_dir, 'test_texture.png')
    ], [
        os.path.join(output_dir, 'watermark_text.png'),
        os.path.join(output_dir, 'watermark_circle.png'),
        os.path.join(output_dir, 'watermark_logo.png')
    ]


def load_image_safe(image_path):
    """安全地加载图片"""
    if not os.path.exists(image_path):
        return None
    
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None
    
    return image


def save_image_comparison(original, watermarked, extracted_watermark, output_path):
    """保存图片对比结果"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    axes[0].imshow(original, cmap='gray')
    axes[0].set_title('原始图片')
    axes[0].axis('off')
    
    axes[1].imshow(watermarked, cmap='gray')
    axes[1].set_title('带水印图片')
    axes[1].axis('off')
    
    axes[2].imshow(extracted_watermark, cmap='gray')
    axes[2].set_title('提取的水印')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def calculate_image_metrics(img1, img2):
    """计算图像质量指标"""
    # PSNR
    mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
    if mse == 0:
        psnr = float('inf')
    else:
        psnr = 20 * np.log10(255.0 / np.sqrt(mse))
    
    # SSIM (简化版)
    mu1 = np.mean(img1)
    mu2 = np.mean(img2)
    sigma1_sq = np.var(img1)
    sigma2_sq = np.var(img2)
    sigma12 = np.mean((img1 - mu1) * (img2 - mu2))
    
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    
    ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / \
           ((mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2))
    
    return {'psnr': psnr, 'ssim': ssim}


def resize_image_to_multiple(image, block_size=8):
    """调整图片尺寸为block_size的倍数"""
    h, w = image.shape
    new_h = (h // block_size) * block_size
    new_w = (w // block_size) * block_size
    
    if new_h != h or new_w != w:
        image = cv2.resize(image, (new_w, new_h))
    
    return image


def create_watermark_pattern(size=(64, 64), pattern_type='text'):
    """创建不同类型的水印图案"""
    watermark = np.zeros(size, dtype=np.uint8)
    
    if pattern_type == 'text':
        cv2.putText(watermark, 'WM', (size[0]//4, size[1]//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
    
    elif pattern_type == 'circle':
        center = (size[0]//2, size[1]//2)
        radius = min(size) // 3
        cv2.circle(watermark, center, radius, 255, -1)
    
    elif pattern_type == 'cross':
        center_x, center_y = size[0]//2, size[1]//2
        thickness = max(2, min(size)//16)
        cv2.line(watermark, (0, center_y), (size[0], center_y), 255, thickness)
        cv2.line(watermark, (center_x, 0), (center_x, size[1]), 255, thickness)
    
    elif pattern_type == 'diamond':
        center = (size[0]//2, size[1]//2)
        points = np.array([
            [center[0], center[1] - size[1]//3],
            [center[0] + size[0]//3, center[1]],
            [center[0], center[1] + size[1]//3],
            [center[0] - size[0]//3, center[1]]
        ], np.int32)
        cv2.fillPoly(watermark, [points], 255)
    
    return watermark


def print_system_info():
    """打印系统信息"""
    import platform
    import sys
    
    print("=" * 50)
    print("数字水印系统 - 系统信息")
    print("=" * 50)
    print(f"Python版本: {sys.version}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"OpenCV版本: {cv2.__version__}")
    print(f"NumPy版本: {np.__version__}")
    print("=" * 50)


def validate_dependencies():
    """验证依赖包是否正确安装"""
    required_packages = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'PIL': 'Pillow',
        'scipy': 'scipy'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("缺少以下依赖包:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\n请运行: pip install -r requirements.txt")
        return False
    
    print("所有依赖包已正确安装")
    return True


def create_demo_watermark(text="DEMO", size=(64, 64)):
    """创建演示用的文字水印"""
    watermark = np.zeros(size, dtype=np.uint8)
    
    # 计算文字大小和位置
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2
    
    # 获取文字尺寸
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    
    # 计算文字位置（居中）
    text_x = (size[0] - text_size[0]) // 2
    text_y = (size[1] + text_size[1]) // 2
    
    # 绘制文字
    cv2.putText(watermark, text, (text_x, text_y), font, font_scale, 255, thickness)
    
    return watermark


class ProgressBar:
    """简单的进度条类"""
    
    def __init__(self, total, prefix='Progress', width=50):
        self.total = total
        self.prefix = prefix
        self.width = width
        self.current = 0
    
    def update(self, increment=1):
        self.current += increment
        percent = (self.current / self.total) * 100
        filled_width = int(self.width * self.current / self.total)
        
        bar = '█' * filled_width + '░' * (self.width - filled_width)
        print(f'\r{self.prefix} |{bar}| {percent:.1f}% ({self.current}/{self.total})', end='')
        
        if self.current >= self.total:
            print()  # 换行


if __name__ == "__main__":
    print("工具函数模块")
    print("请使用其他模块调用这些函数")
