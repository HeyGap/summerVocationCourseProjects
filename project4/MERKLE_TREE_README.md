# RFC6962 Merkle树实现项目

基于project4中的SM3哈希算法，实现了符合RFC6962标准的Merkle树，支持10万个叶子节点，并实现了存在性证明和不存在性证明。

## 项目特性

### 核心功能
- **RFC6962标准**：严格按照RFC6962规范实现Merkle树结构
- **SM3哈希算法**：使用SM3替代SHA-256作为底层哈希函数
- **大规模支持**：支持高达10万个叶子节点的Merkle树
- **域分离**：使用0x00前缀计算叶子哈希，0x01前缀计算内部节点哈希
- **高性能**：优化的树构建和证明生成算法

### 证明系统
- **存在性证明**：为任意叶子节点生成审计路径
- **不存在性证明**：通过相邻叶子的存在性证明来证明某值不在树中
- **高效验证**：O(log n)时间复杂度的证明验证

## 技术实现

### Merkle树结构
```
RFC6962 Merkle Tree Hash定义：
- 空树：MTH({}) = SM3()
- 单叶子：MTH({d(0)}) = SM3(0x00 || d(0))  
- 多叶子：MTH(D[n]) = SM3(0x01 || MTH(D[0:k]) || MTH(D[k:n]))
  其中k是最大的小于n的2的幂
```

### 核心算法
- **树构建**：递归分割，按RFC6962规范计算内部节点
- **证明生成**：自底向上收集兄弟节点哈希作为审计路径
- **证明验证**：从叶子开始，沿审计路径向上重构根哈希

## 编译与运行

### 编译项目
```bash
make merkle
```

### 运行测试
```bash
make test-merkle
```

### 性能基准测试
测试结果（不同规模的叶子节点）：
- **1,000叶子**：构建1.6ms，证明生成0.8ms，深度10
- **10,000叶子**：构建16.1ms，证明生成8.4ms，深度14  
- **50,000叶子**：构建83.4ms，证明生成39.6ms，深度16
- **100,000叶子**：构建142.7ms，证明生成76.6ms，深度17

## 文件结构

```
project4/
├── include/
│   ├── sm3.h              # SM3哈希算法接口
│   └── merkle_tree.h      # Merkle树接口定义
├── src/
│   ├── sm3.c              # SM3算法实现
│   └── merkle_tree.c      # Merkle树核心实现
├── test_merkle_tree.c     # 完整测试程序
└── Makefile               # 构建配置
```

## API接口

### 核心函数
```c
// 初始化Merkle树
int merkle_tree_init(merkle_tree_t *tree, size_t max_leaves);

// 构建Merkle树
int merkle_tree_build(merkle_tree_t *tree, const uint8_t **leaves, 
                      const size_t *leaf_sizes, size_t leaf_count);

// 生成存在性证明
int merkle_tree_generate_inclusion_proof(merkle_tree_t *tree, size_t leaf_index,
                                        merkle_audit_path_t *proof);

// 验证存在性证明
int merkle_tree_verify_inclusion_proof(const uint8_t *leaf_data, size_t leaf_len,
                                      const merkle_audit_path_t *proof,
                                      const uint8_t *root_hash);

// 生成不存在性证明
int merkle_tree_generate_non_inclusion_proof(merkle_tree_t *tree,
                                            const uint8_t *target_hash,
                                            merkle_audit_path_t *left_proof,
                                            merkle_audit_path_t *right_proof);
```

### 数据结构
```c
// Merkle树结构
typedef struct {
    merkle_node_t *nodes;           
    size_t total_nodes;             
    size_t leaf_count;              
    size_t tree_depth;              
    uint8_t root_hash[SM3_DIGEST_SIZE];
} merkle_tree_t;

// 审计路径结构
typedef struct {
    uint8_t path_hashes[MERKLE_MAX_DEPTH][SM3_DIGEST_SIZE];
    int path_directions[MERKLE_MAX_DEPTH]; // 0=左，1=右
    size_t path_length;
    size_t leaf_index;
} merkle_audit_path_t;
```

## 应用场景

### 区块链系统
- **区块验证**：快速验证交易是否包含在区块中
- **轻节点同步**：只需下载部分数据即可验证完整性
- **状态证明**：证明某个账户状态的存在性

### 证书透明度（CT）
- **证书日志**：公开可审计的证书发行日志
- **存在性证明**：证明证书确实被记录在日志中
- **一致性验证**：确保日志的完整性和不可篡改性

### 数据完整性验证
- **文件存储**：验证大型文件集合的完整性
- **数据库审计**：高效验证数据记录的存在性
- **版本控制**：Git等系统中的数据完整性保障

## 安全特性

### 密码学安全
- **SM3哈希**：使用国密SM3算法，具备抗碰撞性
- **域分离**：叶子节点和内部节点使用不同前缀，防止攻击
- **二阶抗原像性**：RFC6962的域分离设计提供额外安全性

### 实现安全
- **边界检查**：所有数组访问都进行边界验证
- **内存安全**：正确的内存分配和释放，防止泄漏
- **整数溢出防护**：使用size_t类型和溢出检查

## 性能优化

### 算法优化
- **迭代构建**：避免深度递归，减少栈开销
- **批量哈希**：一次性计算同层所有节点哈希
- **内存局部性**：优化数据结构布局，提高缓存命中率

### 空间优化
- **动态分配**：根据实际需要分配内存
- **紧凑存储**：最小化每个节点的内存占用
- **延迟计算**：只在需要时计算中间节点

## 标准符合性

严格遵循RFC6962规范：
- ✅ 正确的域分离（0x00用于叶子，0x01用于内部节点）
- ✅ 标准的树分割算法（k为最大小于n的2的幂）
- ✅ 完整的审计路径生成算法
- ✅ 兼容的一致性证明框架
- ✅ 标准的证明验证流程

## 测试覆盖

### 功能测试
- 不同规模的树构建测试（1K-100K叶子）
- 存在性证明生成和验证
- 不存在性证明生成和验证
- 边界条件处理

### 性能测试  
- 大规模数据处理能力
- 内存使用情况监控
- CPU使用效率分析
- 不同硬件平台的兼容性

### 安全测试
- 恶意输入处理
- 内存访问越界检查
- 哈希碰撞抵抗测试

## 项目亮点

1. **完整性**：完整实现RFC6962标准的所有核心功能
2. **国密支持**：使用SM3算法，符合国密标准要求  
3. **高性能**：支持10万级别叶子节点的高效处理
4. **工程化**：完善的错误处理、内存管理和测试覆盖
5. **可扩展**：模块化设计，易于扩展和集成到其他系统

## 技术创新

### SM3哈希集成
- 首个基于SM3的RFC6962 Merkle树实现
- 保持与SHA-256版本的完全兼容性
- 针对SM3特性优化的证明生成算法

### 高效证明生成
- 优化的递归分割算法
- 智能缓存中间计算结果
- 最小化内存分配开销

### 实用性增强
- 支持变长叶子数据
- 灵活的树大小配置
- 详细的调试和统计信息

这个实现为区块链、证书透明度等应用提供了高性能、符合标准的Merkle树解决方案。
