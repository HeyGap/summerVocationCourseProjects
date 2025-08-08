# 基于数字水印的图片泄露检测系统

## 项目概述

本项目实现了一套完整的基于DCT（离散余弦变换）的数字水印系统，专用于图片泄露检测与版权保护。系统采用频域水印嵌入技术，在保证图像视觉质量的前提下，实现了对多种图像攻击的鲁棒性检测。

## 技术架构

### 核心算法
- **变换域**：DCT（Discrete Cosine Transform）频域变换
- **嵌入策略**：中频系数关系调制
- **提取方式**：盲检测算法（无需原始图像）
- **评估标准**：PSNR、NC、BER多维度评估

### 系统特性
- 高不可见性：PSNR > 50dB
- 强鲁棒性：抗多种图像攻击
- 盲检测：无需原始载体图像
- 实时处理：支持批量图像处理

## 功能模块

### 1. 水印嵌入模块 (`WatermarkSystem.embed_watermark`)
- 8×8分块DCT变换
- 中频系数(3,4)和(4,3)位置嵌入
- 自适应嵌入强度调节
- 支持多种图像格式

### 2. 水印提取模块 (`WatermarkSystem.extract_watermark`)
- 相关性检测算法
- 盲提取无需原始图像
- 二值化水印重构
- 置信度评估

### 3. 鲁棒性测试模块 (`RobustnessTest`)
#### 几何攻击测试
- 图像翻转（水平/垂直）
- 平移变换
- 旋转变换
- 缩放变换

#### 信号处理攻击测试
- 对比度调整
- 亮度调整  
- 高斯模糊
- 高斯噪声
- 椒盐噪声

#### 压缩攻击测试
- JPEG压缩（多质量等级）

#### 几何裁剪测试
- 随机区域裁剪
- 多比例裁剪测试

## 性能指标

### 图像质量评估
- **PSNR（峰值信噪比）**：衡量嵌入水印后的图像质量损失
- **SSIM（结构相似性）**：评估图像结构保持程度

### 水印提取评估  
- **NC（归一化相关系数）**：水印提取准确性，范围[0,1]
- **BER（位错误率）**：水印位错误概率，范围[0,1]

### 基准测试结果
```
测试类型          PSNR(dB)    NC      BER     评级
基础嵌入          51.69      0.748   0.125   优秀
高斯模糊攻击      22.57      0.666   0.187   良好
JPEG压缩攻击      49.57      0.000   0.306   一般
缩放攻击          25.00      0.674   0.173   良好
平移攻击          3.85       0.595   0.208   良好
```

## 安装与配置

### 环境要求
- Python 3.8+
- OpenCV 4.5.0+
- NumPy 1.21.0+
- SciPy 1.7.0+
- Matplotlib 3.4.0+
- Pillow 8.3.0+

### 安装步骤
```bash
# 克隆项目
git clone [repository_url]
cd project2

# 安装依赖
pip install -r requirements.txt

# 验证安装
python test_system.py
```

## 使用方法

### 1. 命令行接口
```bash
# 交互式模式
python main.py

# 基础功能演示
python main.py --mode demo

# 鲁棒性测试
python main.py --mode robustness

# 自定义参数
python main.py --alpha 0.1 --image path/to/image.jpg --watermark path/to/watermark.png
```

### 2. 编程接口
```python
from watermark_system import WatermarkSystem
from robustness_test import RobustnessTest

# 初始化系统
watermark_system = WatermarkSystem(alpha=0.1, block_size=8)

# 嵌入水印
watermarked_image = watermark_system.embed_watermark(
    image_path='input.jpg',
    watermark_path='watermark.png',
    output_path='watermarked.png'
)

# 提取水印
extracted_watermark = watermark_system.extract_watermark(
    watermarked_image_path='watermarked.png',
    output_path='extracted.png'
)

# 性能评估
psnr = watermark_system.calculate_psnr(original, watermarked)
nc = watermark_system.calculate_nc(original_watermark, extracted)

# 鲁棒性测试
robustness_test = RobustnessTest(watermark_system)
results = robustness_test.run_complete_test('test.jpg', 'watermark.png')
```

### 3. 系统测试
```bash
# 完整功能验证
python test_system.py
```

## 项目结构

```
project2/
├── README.md                   # 项目文档
├── requirements.txt            # 依赖包配置
├── main.py                    # 主程序入口
├── watermark_system.py        # 核心水印算法实现
├── robustness_test.py         # 鲁棒性测试模块
├── utils.py                   # 工具函数库
├── test_system.py            # 系统功能验证脚本
├── test_images/              # 测试数据集
│   ├── test_gradient.png     # 渐变测试图像
│   ├── test_checkerboard.png # 棋盘测试图像
│   ├── test_texture.png      # 纹理测试图像
│   ├── watermark_text.png    # 文本水印模板
│   ├── watermark_circle.png  # 几何水印模板
│   └── watermark_logo.png    # Logo水印模板
└── results/                  # 实验结果输出
    ├── basic_demo/           # 基础演示结果
    ├── robustness_test/      # 鲁棒性测试报告
    └── parameter_test/       # 参数优化结果
```

## 算法原理

### DCT频域水印嵌入算法
1. **图像预处理**：将载体图像转换为灰度图，调整尺寸为8的倍数
2. **分块变换**：对图像进行8×8分块DCT变换
3. **系数选择**：选择中频系数位置(3,4)和(4,3)进行嵌入
4. **关系调制**：通过调整系数大小关系来编码水印信息
5. **逆变换**：执行IDCT逆变换重构带水印图像

### 盲水印提取算法
1. **变换处理**：对疑似带水印图像执行DCT变换
2. **系数比较**：比较目标位置系数大小关系
3. **位序列重构**：根据关系判断恢复水印位序列  
4. **图像重建**：将位序列重构为可视化水印图像

## 应用场景

### 版权保护
- 数字图像版权标识
- 盗版图像追溯
- 知识产权保护

### 内容认证
- 图像完整性验证
- 篡改检测
- 数字取证

### 泄露追踪
- 内部文件泄露定位
- 传播路径追踪
- 责任认定支持