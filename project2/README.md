# Project 2: 基于数字水印的图片泄露检测

基于频域变换的盲水印系统，实现图片水印的嵌入与提取，并进行多种攻击的鲁棒性测试。

## 算法特点

- **频域嵌入**: 采用离散小波变换(DWT) + 离散余弦变换(DCT)的组合方案
- **盲提取**: 无需原始图像即可提取水印
- **鲁棒性**: 对常见图像攻击具有较强的抵抗能力
- **自适应**: 根据图像容量自动调整嵌入参数

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行演示
```bash
python src/main.py
```

### 命令行使用

1. **嵌入水印**
```bash
python src/main.py embed --input test.jpg --output watermarked.png --text "SECRET_MESSAGE"
```

2. **生成攻击图像**
```bash
python src/main.py attack --input watermarked.png --outdir attacks/
```

3. **提取水印**
```bash
python src/main.py extract --input attacks/ --length 14
```

## 鲁棒性测试

系统支持以下攻击测试：
- 几何攻击：翻转、旋转、平移、缩放、裁剪
- 信号处理：JPEG压缩、高斯噪声、锐化
- 图像增强：对比度调整、亮度调整

## 技术实现

1. **嵌入过程**: 图像 → YUV转换 → DWT分解 → DCT变换 → 量化嵌入
2. **提取过程**: 水印图像 → DWT分解 → DCT变换 → 量化解码 → 投票恢复
3. **容量自适应**: 根据图像大小动态调整重复编码参数

## 许可证

本项目为教学演示代码，算法思想来源于公开文献，具体实现为原创开发。
