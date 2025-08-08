"""数字水印系统包初始化"""

from .watermark import BlindWatermark, WatermarkConfig, apply_all_attacks
from .generate_samples import create_sample_images
from .evaluation import generate_evaluation_report

__version__ = "1.0.0"
__author__ = "Digital Watermark Team"

__all__ = [
    "BlindWatermark",
    "WatermarkConfig", 
    "apply_all_attacks",
    "create_sample_images",
    "generate_evaluation_report"
]
