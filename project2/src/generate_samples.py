"""
生成测试样本图像
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_sample_images(output_dir: str = "samples") -> None:
    """创建测试样本图像"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 样本1: Lena风格的测试图像
    size = (512, 512)
    
    # 创建彩色渐变图像
    img1 = Image.new('RGB', size)
    pixels1 = []
    for y in range(size[1]):
        for x in range(size[0]):
            r = int(255 * (x / size[0]))
            g = int(255 * (y / size[1]))
            b = int(255 * ((x + y) / (size[0] + size[1])))
            pixels1.append((r, g, b))
    
    img1.putdata(pixels1)
    
    # 添加文字
    draw1 = ImageDraw.Draw(img1)
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        # 使用默认字体
        font = ImageFont.load_default()
    
    draw1.text((50, 50), "SAMPLE IMAGE 1", fill=(255, 255, 255), font=font)
    draw1.text((50, 100), "Lena Style", fill=(0, 0, 0), font=font)
    
    # 添加一些几何图形
    draw1.rectangle([200, 200, 300, 300], outline=(255, 0, 0), width=3)
    draw1.ellipse([350, 350, 450, 450], outline=(0, 255, 0), width=3)
    
    img1.save(os.path.join(output_dir, "lena.png"))
    
    # 样本2: 复杂纹理图像
    img2 = Image.new('RGB', size)
    pixels2 = []
    
    for y in range(size[1]):
        for x in range(size[0]):
            # 创建复杂的纹理模式
            r = int(127 + 127 * np.sin(x * 0.02) * np.cos(y * 0.02))
            g = int(127 + 127 * np.sin(x * 0.03) * np.sin(y * 0.03))
            b = int(127 + 127 * np.cos(x * 0.025) * np.cos(y * 0.025))
            pixels2.append((r, g, b))
    
    img2.putdata(pixels2)
    
    draw2 = ImageDraw.Draw(img2)
    draw2.text((50, 50), "SAMPLE IMAGE 2", fill=(255, 255, 255), font=font)
    draw2.text((50, 100), "Texture Pattern", fill=(255, 255, 0), font=font)
    
    img2.save(os.path.join(output_dir, "baboon.png"))
    
    # 样本3: 自然场景模拟
    img3 = Image.new('RGB', size, (135, 206, 250))  # 天空蓝
    draw3 = ImageDraw.Draw(img3)
    
    # 绘制地面
    draw3.rectangle([0, 400, size[0], size[1]], fill=(34, 139, 34))
    
    # 绘制太阳
    draw3.ellipse([400, 50, 480, 130], fill=(255, 255, 0))
    
    # 绘制云朵
    for i, (x, y) in enumerate([(100, 80), (250, 60), (350, 90)]):
        draw3.ellipse([x-30, y-15, x+30, y+15], fill=(255, 255, 255))
        draw3.ellipse([x-20, y-25, x+20, y+5], fill=(255, 255, 255))
    
    # 绘制房屋
    # 房屋主体
    draw3.rectangle([150, 250, 250, 350], fill=(139, 69, 19))
    # 屋顶
    draw3.polygon([(125, 250), (200, 200), (275, 250)], fill=(165, 42, 42))
    # 门
    draw3.rectangle([180, 300, 220, 350], fill=(101, 67, 33))
    # 窗户
    draw3.rectangle([160, 270, 190, 290], fill=(173, 216, 230))
    
    draw3.text((50, 450), "SAMPLE IMAGE 3", fill=(0, 0, 0), font=font)
    draw3.text((50, 480), "Natural Scene", fill=(0, 0, 0), font=font)
    
    img3.save(os.path.join(output_dir, "scene.png"))
    
    print(f"测试样本图像已创建在 {output_dir} 目录中")

if __name__ == "__main__":
    create_sample_images()
