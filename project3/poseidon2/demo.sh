#!/bin/bash

# Poseidon2 零知识证明演示脚本

echo "=================================="
echo "  Poseidon2 零知识证明演示"
echo "=================================="
echo ""

# 检查依赖
echo "检查依赖..."
if ! command -v circom &> /dev/null; then
    echo "错误: circom 未安装"
    echo "请安装: npm install -g circom"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "错误: Node.js 未安装"
    exit 1
fi

echo "✓ 依赖检查通过"
echo ""

# 安装npm依赖
echo "安装npm依赖..."
npm install
echo ""

# 编译电路
echo "1. 编译Poseidon2电路..."
npm run compile
if [ $? -ne 0 ]; then
    echo "错误: 电路编译失败"
    exit 1
fi
echo "✓ 电路编译完成"
echo ""

# 生成信任设置
echo "2. 生成信任设置..."
echo "   这可能需要几分钟时间..."
npm run setup
if [ $? -ne 0 ]; then
    echo "错误: 信任设置失败"
    exit 1
fi
echo "✓ 信任设置完成"
echo ""

# 电路专用设置
echo "3. 生成电路密钥..."
npm run setup-circuit
if [ $? -ne 0 ]; then
    echo "错误: 电路密钥生成失败"
    exit 1
fi
echo "✓ 电路密钥生成完成"
echo ""

# 生成测试输入
echo "4. 生成测试输入..."
npm run test
if [ $? -ne 0 ]; then
    echo "错误: 测试输入生成失败"
    exit 1
fi
echo "✓ 测试输入生成完成"
echo ""

# 生成见证
echo "5. 生成见证..."
npm run witness
if [ $? -ne 0 ]; then
    echo "错误: 见证生成失败"
    exit 1
fi
echo "✓ 见证生成完成"
echo ""

# 生成证明
echo "6. 生成Groth16证明..."
npm run prove
if [ $? -ne 0 ]; then
    echo "错误: 证明生成失败"
    exit 1
fi
echo "✓ 证明生成完成"
echo ""

# 验证证明
echo "7. 验证证明..."
npm run verify
if [ $? -ne 0 ]; then
    echo "错误: 证明验证失败"
    exit 1
fi
echo "✓ 证明验证成功!"
echo ""

# 运行完整验证
echo "8. 运行系统验证..."
node js/verify.js
echo ""

echo "=================================="
echo "         演示完成!"
echo "=================================="
echo ""
echo "生成的文件:"
echo "- build/simple_poseidon2.r1cs     (电路约束)"
echo "- build/verification_key.json     (验证密钥)"  
echo "- build/proof.json                (零知识证明)"
echo "- build/public.json               (公开输入)"
echo "- build/input.json                (原始输入)"
echo ""
echo "证明声明: 我知道某个原象，其Poseidon2哈希值等于公开的哈希值"
echo "在不泄露原象的情况下，证明了对其知识的拥有"
echo ""
echo "这展示了零知识证明的核心价值:"
echo "1. 完整性: 证明者确实知道原象"
echo "2. 零知识: 验证者无法从证明中获得原象信息"  
echo "3. 简洁性: 证明大小固定(128字节)且验证快速"
