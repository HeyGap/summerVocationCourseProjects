#!/bin/bash
# run.sh - SM2 项目运行脚本

echo "SM2 椭圆曲线密码算法项目"
echo "========================"
echo ""
echo "可用命令："
echo "  python main.py demo        - 基础实现演示"
echo "  python main.py demo-opt    - 优化实现演示" 
echo "  python main.py test        - 运行测试套件"
echo "  python main.py benchmark   - 性能基准测试"
echo ""
echo "单独测试："
echo "  python test/test_sm2.py           - 基础实现测试"
echo "  python test/test_sm2_simple.py    - 优化实现测试"
echo "  python test/simple_benchmark.py   - 性能基准测试"
echo ""

# 检查Python环境
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "错误: 需要 Python 3.6 或更高版本"
    exit 1
fi

# 检查依赖
echo "检查依赖库..."
python3 -c "import ecdsa, Crypto, matplotlib, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "警告: 某些依赖库缺失，请运行: pip install -r requirements.txt"
fi

echo "环境检查完成，可以开始使用项目。"
