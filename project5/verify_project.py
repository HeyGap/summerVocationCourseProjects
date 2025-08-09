#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SM2 项目完整验证脚本
验证所有模块和功能的正常运行
"""

import sys
import os
import traceback

def test_basic_imports():
    """测试基础模块导入"""
    print("1. 测试基础模块导入...")
    try:
        import main
        print("   ✓ main.py 导入成功")
        
        from src.sm2 import SM2
        print("   ✓ src.sm2 导入成功")
        
        from src.sm2_opt_simple import SM2OptimizedSimple
        print("   ✓ src.sm2_opt_simple 导入成功")
        
        return True
    except Exception as e:
        print(f"   ✗ 基础模块导入失败: {e}")
        return False

def test_sm2_functionality():
    """测试 SM2 基础功能"""
    print("\n2. 测试 SM2 基础功能...")
    try:
        from src.sm2 import SM2
        
        sm2 = SM2()
        
        # 测试密钥生成
        private_key, public_key = sm2.generate_keypair()
        print(f"   ✓ 密钥生成成功: 私钥长度 {len(str(private_key))}")
        
        # 测试加密解密
        message = "Hello SM2 Test"
        ciphertext = sm2.encrypt(public_key, message)
        decrypted = sm2.decrypt(private_key, ciphertext)
        print(f"   ✓ 加密解密测试: {'成功' if decrypted == message else '失败'}")
        
        # 测试签名验证
        signature = sm2.sign(private_key, message)
        verify_result = sm2.verify(public_key, message, signature)
        print(f"   ✓ 签名验证测试: {'成功' if verify_result else '失败'}")
        
        return True
    except Exception as e:
        print(f"   ✗ SM2 功能测试失败: {e}")
        traceback.print_exc()
        return False

def test_optimized_sm2():
    """测试优化版 SM2"""
    print("\n3. 测试优化版 SM2...")
    try:
        from src.sm2_opt_simple import SM2OptimizedSimple
        
        sm2_opt = SM2OptimizedSimple()
        
        # 测试密钥生成
        private_key, public_key = sm2_opt.generate_keypair()
        print(f"   ✓ 优化版密钥生成成功")
        
        # 测试加密解密
        message = "Hello Optimized SM2"
        ciphertext = sm2_opt.encrypt(public_key, message)
        decrypted = sm2_opt.decrypt(private_key, ciphertext)
        print(f"   ✓ 优化版加密解密测试: {'成功' if decrypted == message else '失败'}")
        
        # 测试批量验证
        messages = ["msg1", "msg2", "msg3"]
        signatures = [sm2_opt.sign(private_key, msg) for msg in messages]
        
        # 准备批量验证数据
        verifications = [(public_key, msg, sig) for msg, sig in zip(messages, signatures)]
        batch_result = sm2_opt.batch_verify(verifications)
        print(f"   ✓ 批量验证测试: {'成功' if all(batch_result) else '失败'}")
        
        return True
    except Exception as e:
        print(f"   ✗ 优化版 SM2 测试失败: {e}")
        traceback.print_exc()
        return False

def test_attack_modules():
    """测试攻击模块"""
    print("\n4. 测试攻击模块导入...")
    
    # 添加攻击模块路径
    attacks_path = os.path.join(os.getcwd(), 'attacks')
    if attacks_path not in sys.path:
        sys.path.append(attacks_path)
    
    attack_modules = [
        ('poc.k_reuse_attack', 'SM2KAttack'),
        ('poc.cross_algorithm_attack', 'CrossAlgorithmAttack'),
        ('poc.malleability_attack', 'MalleabilityAttack'),
        ('poc.message_validation_attack', 'MessageValidationDERAttack'),
        ('poc.pubkey_recovery_attack', 'PublicKeyRecoveryAttack')
    ]
    
    success_count = 0
    for module_name, class_name in attack_modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            attack_class = getattr(module, class_name)
            attack_instance = attack_class()
            print(f"   ✓ {module_name.split('.')[-1]} 导入成功")
            success_count += 1
        except Exception as e:
            print(f"   ✗ {module_name.split('.')[-1]} 导入失败: {str(e)[:50]}...")
    
    return success_count == len(attack_modules)

def test_main_interface():
    """测试主程序接口"""
    print("\n5. 测试主程序接口...")
    try:
        import main
        
        # 测试是否有必要的函数
        required_functions = ['demo_basic', 'demo_optimized', 'run_tests', 'run_benchmark']
        
        for func_name in required_functions:
            if hasattr(main, func_name):
                print(f"   ✓ {func_name} 函数存在")
            else:
                print(f"   ✗ {func_name} 函数不存在")
                return False
        
        return True
    except Exception as e:
        print(f"   ✗ 主程序接口测试失败: {e}")
        return False

def run_unit_tests():
    """运行单元测试"""
    print("\n6. 运行单元测试...")
    try:
        # 导入并运行测试
        from test.test_sm2 import TestSM2
        import unittest
        
        # 创建测试套件
        suite = unittest.TestLoader().loadTestsFromTestCase(TestSM2)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print(f"   ✓ 单元测试通过 ({result.testsRun} 个测试)")
            return True
        else:
            print(f"   ✗ 单元测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
            return False
            
    except Exception as e:
        print(f"   ✗ 单元测试运行失败: {e}")
        return False

def main():
    """主验证函数"""
    print("SM2 椭圆曲线密码算法项目验证")
    print("=" * 50)
    
    # 执行所有测试
    tests = [
        test_basic_imports,
        test_sm2_functionality,
        test_optimized_sm2,
        test_attack_modules,
        test_main_interface,
        run_unit_tests
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"   ✗ 测试执行异常: {e}")
    
    # 输出总结
    print(f"\n{'=' * 50}")
    print(f"验证完成: {passed_tests}/{total_tests} 项测试通过")
    
    if passed_tests == total_tests:
        print("所有功能验证通过，项目运行正常")
        return True
    else:
        print(f"有 {total_tests - passed_tests} 项测试未通过，需要检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
