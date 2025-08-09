"""
工具函数
"""

import random
from typing import List, Any


def shuffle_list(input_list: List[Any]) -> List[Any]:
    """
    随机打乱列表顺序
    """
    shuffled = input_list.copy()
    random.shuffle(shuffled)
    return shuffled


def find_common_elements(list1: List[Any], list2: List[Any]) -> List[Any]:
    """
    找到两个列表的交集元素
    """
    set1 = set(list1)
    set2 = set(list2)
    return list(set1.intersection(set2))


def print_step(step_num: int, participant: str, description: str):
    """
    打印协议步骤信息
    """
    print(f"步骤 {step_num} - {participant}: {description}")


def print_separator():
    """
    打印分隔线
    """
    print("-" * 60)
