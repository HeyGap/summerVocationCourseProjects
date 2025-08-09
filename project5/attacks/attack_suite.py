#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SM2/ECDSA 密码学攻击演示套件
统一演示所有五种攻击场景
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# 导入所有攻击模块
from poc.k_reuse_attack import SM2KAttack
from poc.cross_algorithm_attack import CrossAlgorithmAttack
from poc.malleability_attack import MalleabilityAttack
from poc.message_validation_attack import MessageValidationDERAttack
from poc.pubkey_recovery_attack import PublicKeyRecoveryAttack

class AttackSuite:
    """攻击演示套件"""
    
    def __init__(self):
        self.attacks = {
            '1': ('泄露或重用随机数 k 攻击', SM2KAttack),
            '2': ('跨算法重用密钥和随机数攻击', CrossAlgorithmAttack),
            '3': ('签名延展性 (Malleability) 攻击', MalleabilityAttack),
            '4': ('忽略消息校验与 DER 编码歧义攻击', MessageValidationDERAttack),
            '5': ('从签名中推导公钥攻击', PublicKeyRecoveryAttack)
        }
    
    def display_menu(self):
        """显示攻击选择菜单"""
        print("SM2/ECDSA 密码学攻击演示套件")
        print("=" * 50)
        print("请选择要演示的攻击类型：")
        print()
        
        for key, (name, _) in self.attacks.items():
            print(f"{key}. {name}")
        
        print("0. 运行所有攻击演示")
        print("q. 退出")
        print()
    
    def run_attack(self, attack_key):
        """运行指定的攻击演示"""
        if attack_key == '0':
            self.run_all_attacks()
            return
        
        if attack_key in self.attacks:
            name, attack_class = self.attacks[attack_key]
            print(f"\\n正在运行：{name}")
            print("=" * 60)
            
            try:
                attack_instance = attack_class()
                if hasattr(attack_instance, 'demonstrate_attacks'):
                    attack_instance.demonstrate_attacks()
                elif hasattr(attack_instance, 'demonstrate_attack'):
                    attack_instance.demonstrate_attack()
                else:
                    print("攻击类未实现演示方法")
            except Exception as e:
                print(f"运行攻击演示时出错：{e}")
                import traceback
                traceback.print_exc()
            
            print("\\n" + "=" * 60)
            print("演示完成，按回车键继续...")
            input()
        else:
            print("无效的选择，请重试。")
    
    def run_all_attacks(self):
        """运行所有攻击演示"""
        print("\\n运行所有攻击演示")
        print("=" * 80)
        
        for key, (name, attack_class) in self.attacks.items():
            print(f"\\n[{key}/5] {name}")
            print("=" * 60)
            
            try:
                attack_instance = attack_class()
                if hasattr(attack_instance, 'demonstrate_attacks'):
                    attack_instance.demonstrate_attacks()
                elif hasattr(attack_instance, 'demonstrate_attack'):
                    attack_instance.demonstrate_attack()
                
                print("\\n按回车键继续下一个演示...")
                input()
                
            except Exception as e:
                print(f"运行 {name} 时出错：{e}")
                print("继续下一个演示...")
                continue
        
        print("\\n" + "=" * 80)
        print("所有攻击演示完成！")
    
    def run(self):
        """运行攻击套件"""
        while True:
            self.display_menu()
            choice = input("请输入选择 (1-5, 0, q): ").strip().lower()
            
            if choice == 'q':
                print("退出攻击演示套件")
                break
            elif choice in ['0', '1', '2', '3', '4', '5']:
                self.run_attack(choice)
            else:
                print("无效选择，请重试。\\n")

def main():
    """主函数"""
    try:
        suite = AttackSuite()
        suite.run()
    except KeyboardInterrupt:
        print("\\n用户中断，退出程序")
    except Exception as e:
        print(f"程序运行时出错：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
