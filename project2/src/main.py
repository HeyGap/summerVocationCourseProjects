"""
数字水印系统命令行接口
提供嵌入、提取、攻击测试等功能
"""
import argparse
import os
import sys
import glob
from pathlib import Path

# 导入模块
try:
    from .watermark import BlindWatermark, WatermarkConfig, apply_all_attacks, load_image, save_image
    from .generate_samples import create_sample_images
except ImportError:
    # 支持直接运行
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from watermark import BlindWatermark, WatermarkConfig, apply_all_attacks, load_image, save_image
    from generate_samples import create_sample_images


def cmd_embed(args):
    """嵌入水印命令"""
    print(f"正在嵌入水印到 {args.input}...")
    
    # 加载图像
    image = load_image(args.input)
    
    # 配置参数
    config = WatermarkConfig(
        block_size=args.block_size,
        strength=args.strength,
        repetition=args.repetition,
        seed=args.seed
    )
    
    # 创建水印对象并嵌入
    watermarker = BlindWatermark(config)
    watermarked_image = watermarker.embed_watermark(image, args.text)
    
    # 保存结果
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    save_image(watermarked_image, args.output)
    
    print(f"水印已嵌入并保存到 {args.output}")
    print(f"水印内容: {args.text}")


def cmd_extract(args):
    """提取水印命令"""
    config = WatermarkConfig(
        block_size=args.block_size,
        strength=args.strength,
        repetition=args.repetition,
        seed=args.seed
    )
    
    watermarker = BlindWatermark(config)
    
    if os.path.isfile(args.input):
        # 单个文件
        print(f"正在从 {args.input} 提取水印...")
        image = load_image(args.input)
        extracted_text = watermarker.extract_watermark(image, args.length)
        print(f"提取的水印: {extracted_text}")
        
    elif os.path.isdir(args.input):
        # 目录中的所有图像
        print(f"正在从目录 {args.input} 中的所有图像提取水印...")
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp']:
            image_files.extend(glob.glob(os.path.join(args.input, ext)))
        
        print(f"找到 {len(image_files)} 个图像文件")
        print("-" * 50)
        
        for image_file in sorted(image_files):
            try:
                image = load_image(image_file)
                extracted_text = watermarker.extract_watermark(image, args.length)
                filename = os.path.basename(image_file)
                print(f"{filename:25} -> {extracted_text}")
            except Exception as e:
                filename = os.path.basename(image_file)
                print(f"{filename:25} -> ERROR: {str(e)}")
    
    else:
        print(f"错误: 输入路径 {args.input} 不存在")


def cmd_attack(args):
    """生成攻击图像命令"""
    print(f"正在对 {args.input} 生成攻击图像...")
    
    # 加载图像
    image = load_image(args.input)
    
    # 应用所有攻击
    attacked_images = apply_all_attacks(image)
    
    # 保存攻击图像
    os.makedirs(args.output_dir, exist_ok=True)
    
    for attack_name, attacked_image in attacked_images.items():
        output_path = os.path.join(args.output_dir, f"{attack_name}.png")
        save_image(attacked_image, output_path)
    
    print(f"生成了 {len(attacked_images)} 个攻击图像，保存在 {args.output_dir}")


def cmd_demo(args):
    """运行演示"""
    print("=== 数字水印系统演示 ===\n")
    
    # 1. 生成测试样本
    print("1. 生成测试样本图像...")
    create_sample_images("samples")
    
    # 2. 嵌入水印
    print("\n2. 嵌入水印...")
    sample_image = "samples/lena.png"
    watermarked_image = "outputs/watermarked_lena.png"
    watermark_text = "SECRET2025"
    
    embed_args = argparse.Namespace(
        input=sample_image,
        output=watermarked_image,
        text=watermark_text,
        block_size=8,
        strength=10.0,
        repetition=5,
        seed=42
    )
    cmd_embed(embed_args)
    
    # 3. 生成攻击图像
    print("\n3. 生成攻击图像...")
    attack_args = argparse.Namespace(
        input=watermarked_image,
        output_dir="attacks"
    )
    cmd_attack(attack_args)
    
    # 4. 从原图提取水印
    print("\n4. 从原始水印图像提取水印...")
    extract_args = argparse.Namespace(
        input=watermarked_image,
        length=len(watermark_text),
        block_size=8,
        strength=10.0,
        repetition=5,
        seed=42
    )
    cmd_extract(extract_args)
    
    # 5. 从攻击图像提取水印
    print("\n5. 从攻击图像提取水印（鲁棒性测试）...")
    extract_args.input = "attacks"
    cmd_extract(extract_args)
    
    print("\n=== 演示完成 ===")


def create_parser():
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(description="数字水印系统")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 嵌入命令
    embed_parser = subparsers.add_parser('embed', help='嵌入水印')
    embed_parser.add_argument('--input', required=True, help='输入图像路径')
    embed_parser.add_argument('--output', required=True, help='输出图像路径')
    embed_parser.add_argument('--text', required=True, help='要嵌入的水印文本')
    embed_parser.add_argument('--block-size', type=int, default=8, help='DCT块大小')
    embed_parser.add_argument('--strength', type=float, default=10.0, help='嵌入强度')
    embed_parser.add_argument('--repetition', type=int, default=5, help='重复编码次数')
    embed_parser.add_argument('--seed', type=int, default=42, help='随机种子')
    embed_parser.set_defaults(func=cmd_embed)
    
    # 提取命令
    extract_parser = subparsers.add_parser('extract', help='提取水印')
    extract_parser.add_argument('--input', required=True, help='输入图像或目录路径')
    extract_parser.add_argument('--length', type=int, required=True, help='水印文本长度')
    extract_parser.add_argument('--block-size', type=int, default=8, help='DCT块大小')
    extract_parser.add_argument('--strength', type=float, default=10.0, help='嵌入强度')
    extract_parser.add_argument('--repetition', type=int, default=5, help='重复编码次数')
    extract_parser.add_argument('--seed', type=int, default=42, help='随机种子')
    extract_parser.set_defaults(func=cmd_extract)
    
    # 攻击命令
    attack_parser = subparsers.add_parser('attack', help='生成攻击图像')
    attack_parser.add_argument('--input', required=True, help='输入图像路径')
    attack_parser.add_argument('--output-dir', required=True, help='攻击图像输出目录')
    attack_parser.set_defaults(func=cmd_attack)
    
    # 演示命令
    demo_parser = subparsers.add_parser('demo', help='运行完整演示')
    demo_parser.set_defaults(func=cmd_demo)
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    
    # 如果没有参数，运行演示
    if len(sys.argv) == 1:
        args = argparse.Namespace(command='demo')
        cmd_demo(args)
        return
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
