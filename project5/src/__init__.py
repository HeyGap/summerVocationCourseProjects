# src/__init__.py
# SM2包初始化文件

from .sm2 import SM2
from .sm2_opt import SM2Optimized, PrecomputeTable, MemoryPool

__all__ = ['SM2', 'SM2Optimized', 'PrecomputeTable', 'MemoryPool']
__version__ = '1.0.0'
