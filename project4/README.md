# Project 4: SM3哈希算法的C语言实现

## 项目简介

本项目实现了中国国密SM3密码哈希算法，符合《GM/T 0004-2012 SM3密码哈希算法》标准。SM3算法产生长度为256比特的哈希值，适用于数字签名和验证、消息认证码生成和验证以及随机数生成等应用。

## 文件结构

```
project4/
├── README.md           # 项目说明文档
├── Makefile           # 构建脚本
├── include/
│   └── sm3.h          # SM3算法头文件
├── src/
│   ├── sm3.c          # SM3算法核心实现
│   └── utils.c        # 工具函数实现
├── test/
│   ├── test_sm3.c     # 测试程序
│   └── benchmark.c    # 性能测试程序
└── build/             # 编译输出目录
```

## SM3算法特性

- **哈希长度**: 256位
- **分组长度**: 512位
- **安全强度**: 128位
- **适用场景**: 数字签名、消息认证、随机数生成

## 构建和运行

### 编译项目
```bash
make all
```

### 运行测试
```bash
make test
./build/test_sm3
```

### 性能测试
```bash
make benchmark
./build/benchmark
```

### 清理编译文件
```bash
make clean
```

## API接口

### 基本接口
- `void sm3_init(sm3_context_t *ctx)` - 初始化SM3上下文
- `void sm3_update(sm3_context_t *ctx, const uint8_t *data, size_t len)` - 更新数据
- `void sm3_final(sm3_context_t *ctx, uint8_t *digest)` - 完成计算并输出哈希值

### 便捷接口
- `void sm3_hash(const uint8_t *data, size_t len, uint8_t *digest)` - 一次性计算哈希值

## 测试用例

项目包含标准测试用例：

1. **空消息测试**: 计算空字符串的哈希值
2. **单分组测试**: 计算单个512位分组的哈希值
3. **多分组测试**: 计算跨越多个分组的长消息哈希值
4. **标准测试向量**: 使用官方测试向量验证正确性

## 性能特点

- 纯C语言实现，具有良好的可移植性
- 优化的轮函数实现
- 支持增量式哈希计算
- 内存使用效率高

## 标准符合性

本实现严格遵循以下标准：
- GM/T 0004-2012 SM3密码哈希算法
- 通过所有官方测试向量
- 支持任意长度的输入消息

## 安全注意事项

- 本实现仅用于学习和研究目的
- 在生产环境中使用前需要进行充分的安全审计
- 建议结合侧信道攻击防护措施使用
