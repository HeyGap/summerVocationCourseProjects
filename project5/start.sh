#!/bin/bash
# SM2 项目快速启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色消息
print_colored() {
    echo -e "${1}${2}${NC}"
}

print_header() {
    echo "================================================================="
    print_colored $BLUE "$1"
    echo "================================================================="
}

print_success() {
    print_colored $GREEN "✓ $1"
}

print_warning() {
    print_colored $YELLOW "⚠ $1"
}

print_error() {
    print_colored $RED "✗ $1"
}

# 检查 Python 环境
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python 未安装或不在 PATH 中"
        exit 1
    fi
    
    print_success "Python 环境检查通过: $($PYTHON_CMD --version)"
}

# 检查依赖
check_dependencies() {
    print_colored $BLUE "检查依赖包..."
    
    if [ -f "requirements.txt" ]; then
        $PYTHON_CMD -c "
import sys
try:
    import ecdsa, Crypto, matplotlib, numpy
    print('所有依赖包已安装')
except ImportError as e:
    print(f'缺少依赖包: {e}')
    print('请运行: pip install -r requirements.txt')
    sys.exit(1)
"
        if [ $? -eq 0 ]; then
            print_success "依赖包检查通过"
        else
            print_error "依赖包检查失败"
            return 1
        fi
    else
        print_warning "requirements.txt 不存在"
    fi
}

# 显示菜单
show_menu() {
    print_header "SM2 椭圆曲线密码算法项目"
    echo "请选择要执行的操作："
    echo
    echo "1. 运行 SM2 基础演示"
    echo "2. 运行 SM2 优化演示"  
    echo "3. 运行完整测试套件"
    echo "4. 运行性能基准测试"
    echo "5. 运行安全攻击演示套件"
    echo "6. 运行单个攻击演示"
    echo "7. 查看项目信息"
    echo "8. 安装/更新依赖"
    echo "0. 退出"
    echo
}

# 运行基础演示
run_basic_demo() {
    print_header "SM2 基础功能演示"
    $PYTHON_CMD main.py demo
}

# 运行优化演示
run_optimized_demo() {
    print_header "SM2 优化版本演示"
    $PYTHON_CMD main.py demo-opt
}

# 运行测试
run_tests() {
    print_header "完整测试套件"
    $PYTHON_CMD main.py test
}

# 运行基准测试
run_benchmark() {
    print_header "性能基准测试"
    $PYTHON_CMD main.py benchmark
}

# 运行攻击演示套件
run_attack_suite() {
    print_header "安全攻击演示套件"
    cd attacks/
    $PYTHON_CMD attack_suite.py
    cd ..
}

# 运行单个攻击演示
run_single_attack() {
    print_header "单个攻击演示"
    echo "请选择攻击类型："
    echo "1. 泄露或重用随机数 k 攻击"
    echo "2. 跨算法重用密钥和随机数攻击"
    echo "3. 签名延展性 (Malleability) 攻击" 
    echo "4. 忽略消息校验与 DER 编码歧义攻击"
    echo "5. 从签名中推导公钥攻击"
    echo
    read -p "请输入选择 (1-5): " attack_choice
    
    case $attack_choice in
        1)
            print_colored $BLUE "运行随机数 k 攻击演示..."
            cd attacks/
            $PYTHON_CMD poc/k_reuse_attack.py
            cd ..
            ;;
        2)
            print_colored $BLUE "运行跨算法攻击演示..."
            cd attacks/
            $PYTHON_CMD poc/cross_algorithm_attack.py
            cd ..
            ;;
        3)
            print_colored $BLUE "运行签名延展性攻击演示..."
            cd attacks/
            $PYTHON_CMD poc/malleability_attack.py
            cd ..
            ;;
        4)
            print_colored $BLUE "运行消息校验攻击演示..."
            cd attacks/
            $PYTHON_CMD poc/message_validation_attack.py
            cd ..
            ;;
        5)
            print_colored $BLUE "运行公钥恢复攻击演示..."
            cd attacks/
            $PYTHON_CMD poc/pubkey_recovery_attack.py
            cd ..
            ;;
        *)
            print_error "无效选择"
            ;;
    esac
}

# 显示项目信息
show_project_info() {
    print_header "项目信息"
    echo "项目名称: SM2 椭圆曲线密码算法实现与安全分析"
    echo "功能特性:"
    echo "  ✓ 完整的 SM2 算法实现"
    echo "  ✓ 性能优化版本"  
    echo "  ✓ 全面的安全攻击分析"
    echo "  ✓ 数学推导和理论证明"
    echo "  ✓ 概念验证 (PoC) 代码"
    echo "  ✓ 防护措施建议"
    echo
    echo "文件结构:"
    echo "  ├── src/           # 核心实现代码"
    echo "  ├── test/          # 测试用例"
    echo "  ├── attacks/       # 攻击分析和演示"
    echo "  ├── main.py        # 主程序入口"
    echo "  └── README.md      # 项目文档"
    echo
    echo "更多信息请查看 README.md 文件"
}

# 安装依赖
install_dependencies() {
    print_header "安装/更新依赖"
    
    if [ -f "requirements.txt" ]; then
        print_colored $BLUE "正在安装依赖包..."
        $PYTHON_CMD -m pip install --upgrade pip
        $PYTHON_CMD -m pip install -r requirements.txt
        
        if [ $? -eq 0 ]; then
            print_success "依赖安装完成"
        else
            print_error "依赖安装失败"
        fi
    else
        print_error "requirements.txt 文件不存在"
    fi
}

# 主函数
main() {
    # 检查环境
    check_python
    check_dependencies
    
    while true; do
        show_menu
        read -p "请输入选择 (0-8): " choice
        echo
        
        case $choice in
            1)
                run_basic_demo
                ;;
            2)
                run_optimized_demo
                ;;
            3)
                run_tests
                ;;
            4)
                run_benchmark
                ;;
            5)
                run_attack_suite
                ;;
            6)
                run_single_attack
                ;;
            7)
                show_project_info
                ;;
            8)
                install_dependencies
                ;;
            0)
                print_colored $GREEN "感谢使用 SM2 项目！"
                exit 0
                ;;
            *)
                print_error "无效选择，请重试"
                ;;
        esac
        
        echo
        read -p "按回车键返回主菜单..."
        clear
    done
}

# 运行主函数
main "$@"
