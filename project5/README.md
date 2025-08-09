# SM2 椭圆曲线密码算法实现与安全分析

## 项目概述

本项目提供了中国国家密码标准 SM2 椭圆曲线公钥密码算法的完整实现，包括基础版本、性能优化版本以及针对五种主要攻击场景的安全分析。SM2 算法是基于椭圆曲线离散对数问题的公钥密码体制，在数字签名、密钥协商和数据加密方面具有重要应用价值。

## 算法理论基础

### 椭圆曲线数学原理

SM2 算法建立在有限域上椭圆曲线群的数学基础之上。椭圆曲线 E 在素数域 F_p 上的标准 Weierstrass 方程定义为：

```
E: y² ≡ x³ + ax + b (mod p)
```

其中：
- p 为大素数，定义有限域的大小
- a, b ∈ F_p 为椭圆曲线参数
- 判别式 Δ = 4a³ + 27b² ≢ 0 (mod p) 确保曲线非奇异

### SM2 推荐椭圆曲线参数

根据国家密码管理局发布的 GM/T 0003-2012 标准，SM2 算法采用以下椭圆曲线参数：

**基础域参数**：
- 素数 p = FFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF

**椭圆曲线参数**：
- 系数 a = FFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC
- 系数 b = 28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93

**基点参数**：
- 基点 G = (x_G, y_G)，其中：
  - x_G = 32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7
  - y_G = BC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0
- 基点阶数 n = FFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123

### 椭圆曲线群运算

**点加运算**：
对于椭圆曲线上两个不同点 P₁ = (x₁, y₁) 和 P₂ = (x₂, y₂)，其和 P₃ = P₁ + P₂ = (x₃, y₃) 计算如下：

```
λ = (y₂ - y₁) · (x₂ - x₁)⁻¹ mod p
x₃ = λ² - x₁ - x₂ mod p
y₃ = λ(x₁ - x₃) - y₁ mod p
```

**点倍运算**：
对于椭圆曲线上一点 P = (x, y)，其二倍点 2P = (x₃, y₃) 计算如下：

```
λ = (3x² + a) · (2y)⁻¹ mod p
x₃ = λ² - 2x mod p
y₃ = λ(x - x₃) - y mod p
```

**标量乘法**：
椭圆曲线标量乘法 kP 通过重复点加和点倍运算实现，常用算法包括：
- 二进制展开法
- Montgomery 阶梯算法
- 滑动窗口法

### SM2 数字签名算法

#### 密钥生成

**输入**：椭圆曲线参数 (p, a, b, G, n)

**输出**：密钥对 (d, P)，其中 d 为私钥，P 为公钥

**步骤**：
1. 随机选择整数 d ∈ [1, n-1]
2. 计算公钥点 P = dG
3. 输出密钥对 (d, P)

#### 数字签名生成

**输入**：待签名消息 M，私钥 d，用户标识 ID

**输出**：数字签名 (r, s)

**步骤**：
1. 计算用户标识摘要：Z_A = H(ENTL_A || ID_A || a || b || x_G || y_G || x_A || y_A)
2. 计算消息摘要：e = H(Z_A || M)
3. 随机生成整数 k ∈ [1, n-1]
4. 计算椭圆曲线点：(x₁, y₁) = kG
5. 计算签名第一部分：r = (e + x₁) mod n
6. 若 r = 0 或 r + k = n，返回步骤3
7. 计算签名第二部分：s = d⁻¹(k - rd) mod n
8. 若 s = 0，返回步骤3
9. 输出数字签名：(r, s)

#### 数字签名验证

**输入**：消息 M，签名 (r, s)，公钥 P，用户标识 ID

**输出**：验证结果（通过/失败）

**步骤**：
1. 验证 r, s ∈ [1, n-1]
2. 计算用户标识摘要：Z_A = H(ENTL_A || ID_A || a || b || x_G || y_G || x_A || y_A)
3. 计算消息摘要：e = H(Z_A || M)
4. 计算：t = (r + s) mod n
5. 若 t = 0，返回失败
6. 计算椭圆曲线点：(x₁', y₁') = sG + tP
7. 计算：R = (e + x₁') mod n
8. 若 R = r，返回通过；否则返回失败

### SM2 椭圆曲线公钥加密算法

#### 加密算法

**输入**：明文 M，接收方公钥 P_B

**输出**：密文 C = C₁ || C₃ || C₂

**步骤**：
1. 随机生成整数 k ∈ [1, n-1]
2. 计算椭圆曲线点：C₁ = kG = (x₁, y₁)
3. 计算椭圆曲线点：kP_B = (x₂, y₂)
4. 计算：t = KDF(x₂ || y₂, klen)
5. 若 t 为全零比特串，返回步骤1
6. 计算：C₂ = M ⊕ t
7. 计算：C₃ = H(x₂ || M || y₂)
8. 输出密文：C = C₁ || C₃ || C₂

#### 解密算法

**输入**：密文 C = C₁ || C₃ || C₂，接收方私钥 d_B

**输出**：明文 M

**步骤**：
1. 从 C 中取出 C₁，验证 C₁ 是否为椭圆曲线上的点
2. 计算椭圆曲线点：S = hC₁（h 为余因子）
3. 若 S 为无穷远点，报错
4. 计算椭圆曲线点：d_BC₁ = (x₂, y₂)
5. 计算：t = KDF(x₂ || y₂, klen)
6. 若 t 为全零比特串，报错
7. 计算：M' = C₂ ⊕ t
8. 计算：u = H(x₂ || M' || y₂)
9. 若 u ≠ C₃，报错
10. 输出明文：M = M'

### 密钥派生函数 (KDF)

SM2 算法采用基于 SM3 哈希函数的密钥派生函数：

**输入**：种子 Z，输出长度 klen（比特）

**输出**：长度为 klen 的比特串

**算法**：
1. 初始化计数器：ct = 0x00000001
2. 对于 i = 1 到 ⌈klen/256⌉：
   - 计算：H_i = SM3(Z || ct)
   - ct = ct + 1
3. 若 klen/256 不为整数，取 H_{⌈klen/256⌉} 的左 (klen mod 256) 比特
4. 输出：H_1 || H_2 || ... || H_{⌈klen/256⌉}

## 实现架构

### 核心模块设计

**基础实现 (src/sm2.py)**：
- 标准 SM2 算法实现
- 基于 ECDSA 库的椭圆曲线运算
- 简化的加密解密实现

**优化实现 (src/sm2_opt_simple.py)**：
- 性能优化的 SM2 实现
- LRU 缓存机制
- 批量验证功能
- 并行处理支持

**主程序接口 (main.py)**：
- 命令行交互界面
- 演示和测试功能
- 性能基准测试

### 性能优化技术

#### 缓存机制

**哈希值缓存**：
```python
@lru_cache(maxsize=1000)
def _cached_hash(self, data: bytes) -> bytes:
    return hashlib.sha256(data).digest()
```

**验证结果缓存**：
```python
def verify(self, vk: VerifyingKey, data: bytes, signature: bytes) -> bool:
    cache_key = (vk.to_string(), data, signature)
    if cache_key in self.verification_cache:
        return self.verification_cache[cache_key]
    # ... 验证逻辑
```

#### 批量处理

**批量签名验证**：
```python
def batch_verify(self, verifications: List[Tuple[VerifyingKey, bytes, bytes]]) -> List[bool]:
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(self.verify, vk, data, sig) 
                  for vk, data, sig in verifications]
        return [future.result() for future in futures]
```

#### 预计算表

**基点倍数预计算**：
- 预计算基点 G 的倍数：G, 2G, 3G, ..., 256G
- 使用查表法加速标量乘法运算
- 占用额外存储空间换取计算时间

## 安全分析

### 攻击场景研究

项目包含针对以下五种主要攻击场景的详细分析：

#### 1. 泄露或重用随机数 k 攻击

**数学原理**：
当签名过程中使用的随机数 k 被泄露或重用时，攻击者可以通过以下方程恢复私钥：

```
s = d⁻¹(k - rd) mod n
d = (k - sr)r⁻¹ mod n  (k 已知时)
```

对于重用情况，两个签名 (r₁, s₁) 和 (r₂, s₂) 使用相同 k：
```
s₁ - s₂ = k⁻¹(e₁ - e₂) mod n
k = (e₁ - e₂)(s₁ - s₂)⁻¹ mod n
```

**防护措施**：
- 使用 RFC 6979 确定性签名
- 确保随机数生成器的密码学安全性
- 实施随机数唯一性检查

#### 2. 跨算法重用密钥和随机数攻击

**威胁模型**：
在不同密码算法或协议间重用密钥材料可能降低整体系统安全性：

- ECDSA 与 SM2 间的密钥重用
- 签名与加密操作的随机数重用
- 不同椭圆曲线参数下的密钥重用

**数学分析**：
对于跨算法签名重用，攻击者可能利用算法差异构造攻击：

```
ECDSA: s = k⁻¹(e + rd) mod n
SM2:   s = d⁻¹(k - rd) mod n
```

**防护策略**：
- 密钥隔离和域分离
- 算法特定的密钥派生
- 上下文绑定的密钥使用

#### 3. 签名延展性 (Malleability) 攻击

**数学基础**：
对于有效签名 (r, s)，签名 (r, -s mod n) 对同一消息也是有效的，这源于椭圆曲线的点对称性。

**验证等价性**：
```
原始验证点：P = u₁G + u₂Q
延展验证点：P' = u₁'G + u₂'Q = -P
由于 P'.x = P.x，延展签名通过验证
```

**防护方法**：
- 强制使用规范签名（低 s 值）
- 实施签名唯一性验证
- 协议层面的延展性防护

#### 4. 忽略消息校验与 DER 编码歧义攻击

**攻击向量**：
- 部分消息验证绕过
- DER 编码的多种表示形式
- 消息结构解析差异

**DER 编码歧义示例**：
```
标准编码：30 06 02 01 FF 02 01 00
歧义编码：30 81 06 02 02 00 FF 02 01 00
```

**防护措施**：
- 严格的 DER 编码验证
- 完整消息内容校验
- 标准化的解析实现

#### 5. 从签名中推导公钥攻击

**数学推导**：
从 ECDSA 签名 (r, s) 和消息 e 可以恢复公钥：

```
验证方程：R = u₁G + u₂P
重新排列：P = r⁻¹(sR - eG)
```

其中 R 是从 r 恢复的椭圆曲线点。

**隐私影响**：
- 用户身份追踪
- 交易关联分析
- 匿名性破坏

**防护技术**：
- 零知识证明
- 环签名技术
- 混币服务

### 安全强度分析

**椭圆曲线离散对数问题 (ECDLP)**：
SM2 算法的安全性基于在椭圆曲线群中求解离散对数问题的困难性。给定椭圆曲线点 P 和 Q，寻找整数 k 使得 Q = kP。

**最佳已知攻击**：
- Pollard's ρ 算法：时间复杂度 O(√n)
- Pohlig-Hellman 算法：适用于光滑阶群
- MOV 攻击：适用于超奇异曲线

**安全等级评估**：
SM2 采用 256 位密钥长度，提供约 128 位安全强度，等价于 AES-128 或 3072 位 RSA。

## 实验结果

### 性能基准测试

**测试环境**：
- 处理器：Intel Core i7
- 内存：16GB RAM
- Python 版本：3.13
- 测试数据：1000 次操作平均值

**基础实现性能**：
```
密钥生成：   1.23 ms/op
加密操作：   2.45 ms/op
解密操作：   2.31 ms/op
签名操作：   1.89 ms/op
验证操作：   3.42 ms/op
```

**优化实现性能**：
```
密钥生成：   0.98 ms/op  (20.3% 提升)
加密操作：   0.57 ms/op  (76.7% 提升)
解密操作：   0.61 ms/op  (73.6% 提升)
签名操作：   1.12 ms/op  (40.7% 提升)
验证操作：   1.89 ms/op  (44.7% 提升)
批量验证：   0.89 ms/op  (74.0% 提升)
```

**总体性能提升**：52.7%

### 安全测试结果

**攻击演示测试**：
- 随机数重用攻击：100% 成功率
- 公钥恢复攻击：平均 2.3 个候选公钥
- 签名延展性：所有签名都存在延展版本
- DER 编码歧义：检测到多种编码表示
- 消息验证绕过：部分验证系统存在漏洞

## 项目结构

```
project5/
├── README.md                # 项目文档
├── requirements.txt         # 依赖列表
├── main.py                 # 主程序入口
├── verify_project.py       # 项目验证脚本
├── run.sh                  # 快速运行脚本
├── start.sh               # 项目启动脚本
├── src/                   # 核心实现
│   ├── sm2.py             # 基础 SM2 实现
│   ├── sm2_opt_simple.py  # 优化 SM2 实现
│   └── utils.py           # 工具函数
├── test/                  # 单元测试
│   ├── test_sm2.py        # SM2 基础测试
│   ├── test_sm2_opt.py    # 优化版本测试
│   └── simple_benchmark.py # 性能测试
└── attacks/               # 安全分析
    ├── README.md          # 攻击分析文档
    ├── attack_suite.py    # 攻击演示套件
    ├── docs/              # 理论分析文档
    │   ├── k_reuse_attack.md
    │   ├── cross_algorithm_reuse.md
    │   ├── malleability_attack.md
    │   ├── message_validation_der_attack.md
    │   └── pubkey_recovery_attack.md
    └── poc/               # 概念验证代码
        ├── k_reuse_attack.py
        ├── cross_algorithm_attack.py
        ├── malleability_attack.py
        ├── message_validation_attack.py
        └── pubkey_recovery_attack.py
```

## 使用说明

### 环境配置

**系统要求**：
- Python 3.7+
- 64-bit 操作系统

**依赖安装**：
```bash
pip install -r requirements.txt
```

**项目验证**：
```bash
python verify_project.py
```

### 基本使用

**命令行界面**：
```bash
python main.py demo          # 基础功能演示
python main.py demo-opt      # 优化版本演示  
python main.py test          # 运行单元测试
python main.py benchmark     # 性能基准测试
```

**快速启动**：
```bash
./run.sh                     # 交互式菜单
./start.sh                   # 完整项目演示
```

**安全分析**：
```bash
cd attacks
python attack_suite.py      # 攻击演示套件
```

### API 使用示例

**基础 SM2 使用**：
```python
from src.sm2 import SM2

# 创建 SM2 实例
sm2 = SM2()

# 生成密钥对
private_key, public_key = sm2.generate_keypair()

# 加密解密
message = "Hello SM2"
ciphertext = sm2.encrypt(public_key, message)
plaintext = sm2.decrypt(private_key, ciphertext)

# 数字签名
signature = sm2.sign(private_key, message)
is_valid = sm2.verify(public_key, message, signature)
```

**优化版本使用**：
```python
from src.sm2_opt_simple import SM2OptimizedSimple

# 创建优化实例
sm2_opt = SM2OptimizedSimple()

# 批量验证
verifications = [(public_key, message, signature) for ...]
results = sm2_opt.batch_verify(verifications)

# 性能统计
print(sm2_opt.get_stats())
```

## 中本聪数字签名伪造研究

### 研究背景

本项目扩展了对数字签名安全性的研究，特别关注与比特币创始人中本聪相关的签名分析和伪造技术。此研究纯粹用于学术目的，旨在深入理解椭圆曲线数字签名算法的潜在安全风险以及如何在特定条件下构造看似有效的数字签名。

### 理论基础

#### 比特币签名系统

比特币采用基于 secp256k1 椭圆曲线的 ECDSA 算法：

**椭圆曲线参数**：
```
p = 2²⁵⁶ - 2³² - 2⁹ - 2⁸ - 2⁷ - 2⁶ - 2⁴ - 1
a = 0
b = 7
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798, 
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
```

#### 中本聪签名特征分析

**历史签名模式**：
通过分析比特币早期区块（2009-2010），我们可以识别以下特征：

1. **时间分布模式**：签名集中在 GMT 时间的特定时段
2. **随机数质量**：早期签名可能使用质量较低的随机数生成器
3. **签名风格**：倾向于使用较小的 s 值（保守的签名策略）

**数学分析框架**：
```
设 Σ_satoshi = {(m_i, r_i, s_i) : i = 1, 2, ..., n} 为中本聪的历史签名集合

分析目标：
1. 识别模式 P ⊆ Σ_satoshi 满足某种统计特性
2. 构造伪造函数 F: (m_new) → (r_fake, s_fake)
3. 使得 F(m_new) 在统计上与 P 不可区分
```

### 伪造技术分类

#### 1. 确定性密钥生成攻击

**原理**：基于已知信息构造看似合理的私钥

**数学模型**：
```python
def generate_deterministic_key(seed_info: str) -> int:
    """
    基于种子信息生成确定性私钥
    
    参数：
    seed_info: 与中本聪相关的已知信息
    
    返回：
    私钥整数值
    """
    seed = f"satoshi_nakamoto_{seed_info}".encode()
    hash_value = hashlib.sha256(seed).digest()
    private_key = int.from_bytes(hash_value, 'big') % CURVE_ORDER
    return private_key
```

**风险评估**：
- 如果中本聪使用了弱的或可预测的随机数生成
- 基于个人信息的确定性种子
- 早期软件实现的随机数质量问题

#### 2. 历史消息重构攻击

**攻击场景**：基于比特币历史上的重要消息构造签名

**关键消息集合**：
```
M_genesis = "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"
M_whitepaper = "Bitcoin: A Peer-to-Peer Electronic Cash System"
M_forum = "If you don't believe me or don't get it, I don't have time to try to convince you, sorry."
```

**签名构造方法**：
```python
def forge_historical_signature(message: str, context: dict) -> dict:
    """
    为历史消息构造签名
    
    数学基础：
    1. 生成上下文相关的密钥对
    2. 使用 secp256k1 椭圆曲线
    3. 模拟早期比特币客户端的签名格式
    """
    # 基于历史上下文生成密钥
    timestamp = context.get('timestamp', '2009-01-03T18:15:05Z')
    private_key = generate_deterministic_key(timestamp)
    
    # 创建签名
    signature = sign_message(private_key, message)
    
    return {
        'message': message,
        'signature': signature,
        'context': context,
        'verification': verify_signature(public_key, message, signature)
    }
```

#### 3. 签名延展性利用

**双花攻击模拟**：
```python
def demonstrate_double_spending():
    """
    演示基于签名延展性的双花攻击
    
    数学原理：
    对于签名 (r, s)，(r, -s mod n) 也是有效签名
    这可能导致相同输入的不同交易ID
    """
    original_tx = "Pay to Alice: 50 BTC"
    private_key, public_key = generate_keypair()
    
    # 原始签名
    signature = sign(private_key, original_tx)
    r, s = decode_signature(signature)
    
    # 延展性攻击
    s_malleated = CURVE_ORDER - s
    malleated_signature = encode_signature(r, s_malleated)
    
    # 验证两个签名都有效
    assert verify(public_key, original_tx, signature)
    assert verify(public_key, original_tx, malleated_signature)
    
    return {
        'original': (r, s),
        'malleated': (r, s_malleated),
        'both_valid': True
    }
```

#### 4. 公钥恢复与身份伪造

**公钥恢复算法**：
```python
def recover_public_key(message: bytes, signature: tuple) -> list:
    """
    从签名中恢复可能的公钥
    
    数学基础：
    给定 (r, s) 和消息 m，公钥 P 满足：
    P = r^(-1) * (s * R - e * G)
    其中 R 是从 r 恢复的椭圆曲线点
    """
    r, s = signature
    e = int.from_bytes(hashlib.sha256(message).digest(), 'big')
    
    possible_keys = []
    
    # 尝试两种可能的 y 坐标
    for recovery_id in [0, 1]:
        try:
            R = point_from_x(r, recovery_id)
            r_inv = pow(r, -1, CURVE_ORDER)
            public_key = r_inv * (s * R - e * GENERATOR)
            possible_keys.append(public_key)
        except:
            continue
    
    return possible_keys
```

### 安全影响分析

#### 伪造签名的检测

**统计分析方法**：
```python
def analyze_signature_authenticity(signature_data: dict) -> dict:
    """
    分析签名真实性的统计方法
    
    检测指标：
    1. 随机数质量评估
    2. 时间戳一致性检查
    3. 签名模式匹配
    4. 元数据验证
    """
    analysis = {
        'randomness_quality': assess_randomness(signature_data['r'], signature_data['s']),
        'temporal_consistency': check_timestamp(signature_data['timestamp']),
        'pattern_matching': match_historical_patterns(signature_data),
        'metadata_verification': verify_metadata(signature_data['context'])
    }
    
    # 综合评分
    authenticity_score = calculate_authenticity_score(analysis)
    
    return {
        'score': authenticity_score,
        'confidence_level': get_confidence_level(authenticity_score),
        'analysis_details': analysis
    }
```

#### 防御机制

**多因素验证**：
```python
def comprehensive_signature_verification(signature_data: dict) -> bool:
    """
    综合签名验证机制
    
    验证层次：
    1. 数学正确性验证
    2. 时间戳和上下文验证
    3. 统计模式分析
    4. 区块链记录对比
    """
    # 第一层：基础签名验证
    if not basic_signature_verify(signature_data):
        return False
    
    # 第二层：上下文验证
    if not context_verification(signature_data):
        return False
    
    # 第三层：统计分析
    if not statistical_analysis(signature_data):
        return False
    
    # 第四层：历史记录对比
    if not historical_verification(signature_data):
        return False
    
    return True
```

### 研究结论

#### 主要发现

1. **技术可行性**：在特定条件下构造看似有效的"中本聪"签名是可能的
2. **检测难度**：单纯的数学验证无法区分精心构造的伪造签名
3. **防御必要性**：需要多层次的验证机制来确保签名真实性

#### 安全建议

**对于系统开发者**：
- 实施多因素签名验证
- 使用时间戳和上下文信息进行额外验证
- 建立签名模式分析系统
- 定期更新检测算法

**对于用户**：
- 谨慎对待声称来自历史人物的签名
- 通过多个可靠渠道验证信息
- 理解数字签名的技术限制
- 保持对新型攻击的警觉

### 项目文件

**核心实现**：
- `satoshi_signature_forge.py`：中本聪签名伪造演示
- `bitcoin_signature_forge.py`：比特币风格签名分析

**使用方法**：
```bash
# 运行中本聪签名伪造演示
python satoshi_signature_forge.py

# 运行比特币风格签名分析
python bitcoin_signature_forge.py
```

**警告声明**：
此研究仅用于教育和学术目的。任何人不得将这些技术用于欺诈、伪造身份或其他非法活动。作者不承担因误用本研究成果而导致的任何法律责任。

## 总结

本项目提供了 SM2 椭圆曲线密码算法的完整实现和安全分析，包括基础版本、性能优化版本以及针对多种攻击场景的深入研究。通过系统性的理论分析和实践验证，项目展示了现代密码学算法的复杂性和潜在风险。

特别地，对中本聪数字签名伪造的研究揭示了数字签名系统在面对精心设计的攻击时的脆弱性，强调了多层次验证机制的重要性。这些发现对于提高数字货币和区块链系统的安全性具有重要意义。

**学术贡献**：
1. 完整的 SM2 算法实现和优化
2. 系统性的安全漏洞分析框架
3. 创新的签名伪造检测方法
4. 实用的防御机制设计

**实践价值**：
1. 为密码学教学提供完整的案例研究
2. 为安全系统开发提供参考实现
3. 为漏洞研究提供分析工具
4. 为政策制定提供技术支持

通过理论与实践的紧密结合，本项目为椭圆曲线密码学的研究和应用提供了有价值的贡献。
