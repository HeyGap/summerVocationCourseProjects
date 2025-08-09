#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试所有攻击模块
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

def test_attack_module(module_name, class_name):
    """测试单个攻击模块"""
    try:
        print(f"\\n测试 {module_name}...")
        print("-" * 40)
        
        # 动态导入模块
        module = __import__(f"poc.{module_name}", fromlist=[class_name])
        attack_class = getattr(module, class_name)
        
        # 创建实例并运行演示
        attack_instance = attack_class()
        if hasattr(attack_instance, 'demonstrate_attacks'):
            attack_instance.demonstrate_attacks()
        elif hasattr(attack_instance, 'demonstrate_attack'):
            attack_instance.demonstrate_attack()
        else:
            print(f"警告：{class_name} 没有演示方法")
        
        print(f"✓ {module_name} 测试通过")
        return True
        
    except Exception as e:
        print(f"✗ {module_name} 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("SM2/ECDSA 攻击模块快速测试")
    print("=" * 50)
    
    # 定义要测试的攻击模块
    attacks = [
        ("k_reuse_attack", "SM2KAttack"),
        ("cross_algorithm_attack", "CrossAlgorithmAttack"), 
        ("malleability_attack", "MalleabilityAttack"),
        ("message_validation_attack", "MessageValidationDERAttack"),
        ("pubkey_recovery_attack", "PublicKeyRecoveryAttack")
    ]
    
    results = []
    
    for module_name, class_name in attacks:
        success = test_attack_module(module_name, class_name)
        results.append((module_name, success))
        
        print("\\n" + "="*50)
        print("按回车键继续下一个测试...")
        input()
    
    # 汇总结果
    print("\\n测试结果汇总:")
    print("=" * 50)
    
    passed = 0
    for module_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{module_name}: {status}")
        if success:
            passed += 1
    
    print(f"\\n总计：{passed}/{len(results)} 个模块测试通过")
    
    if passed == len(results):
        print("\\n🎉 所有攻击模块都工作正常！")
    else:
        print(f"\\n⚠️  有 {len(results) - passed} 个模块需要修复")

if __name__ == "__main__":
    main()
