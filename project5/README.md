# SM2 基础密码算法实现

## 项目概述

本项目提供了中国国家密码算法 SM2 的基础实现，基于椭圆曲线密码学（ECC）技术。SM2 是中国国家密码管理局发布的公钥密码算法标准，广泛应用于数字签名、密钥协商和公钥加密等密码学应用场景。

## 功能特性

### 核心功能
- **密钥对生成**：基于椭圆曲线的公私钥对生成
- **数字签名**：支持数据签名和签名验证
- **公钥加密**：支持公钥加密和私钥解密
- **密码学安全**：基于 NIST P-256 椭圆曲线的安全实现

### 技术特点
- 纯 Python 实现，依赖最小化
- 兼容标准椭圆曲线密码学库
- 支持多种数据类型的加密和签名
- 完整的单元测试覆盖
- 详细的性能基准测试

## 系统要求

### 环境依赖
- **Python**: 3.6 或更高版本
- **操作系统**: Linux、macOS、Windows

### 第三方依赖
- `ecdsa >= 0.18.0`: 椭圆曲线数字签名算法库
- `pycryptodome >= 3.15.0`: 加密算法库

## 安装与配置

### 1. 克隆项目
```bash
git clone <repository-url>
cd project5-commit1-sm2Basic
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 验证安装
```bash
python src/sm2.py
```

## 使用指南

### 基本用法

```python
from src.sm2 import SM2

# 初始化SM2实例
sm2 = SM2()

# 生成密钥对
private_key, public_key = sm2.generate_keypair()

# 数据加密
message = b"Hello, SM2!"
ciphertext = sm2.encrypt(public_key, message)

# 数据解密
decrypted = sm2.decrypt(private_key, ciphertext)

# 数字签名
signature = sm2.sign(private_key, message)

# 签名验证
is_valid = sm2.verify(public_key, message, signature)
```

### 高级用法

```python
# 处理不同类型的数据
test_cases = [
    b"简单文本",
    b"",  # 空数据
    b"A" * 1000,  # 长数据
    b"\x00\x01\x02\xff\xfe\xfd",  # 二进制数据
]

for data in test_cases:
    # 加密解密循环
    ciphertext = sm2.encrypt(public_key, data)
    decrypted = sm2.decrypt(private_key, ciphertext)
    assert decrypted == data
    
    # 签名验证循环
    signature = sm2.sign(private_key, data)
    assert sm2.verify(public_key, data, signature)
```

## API 文档

### SM2 类

#### 构造函数
```python
SM2()
```
初始化SM2密码算法实例，使用NIST P-256椭圆曲线。

#### 方法说明

##### `generate_keypair()`
生成椭圆曲线密钥对。

**返回值**:
- `tuple`: (私钥, 公钥) 元组

**示例**:
```python
private_key, public_key = sm2.generate_keypair()
```

##### `encrypt(public_key, plaintext)`
使用公钥加密数据。

**参数**:
- `public_key` (VerifyingKey): 椭圆曲线公钥
- `plaintext` (bytes): 待加密的明文数据

**返回值**:
- `bytes`: 加密后的密文数据

**异常**:
- `ValueError`: 输入参数无效
- `CryptoError`: 加密过程失败

##### `decrypt(private_key, ciphertext)`
使用私钥解密数据。

**参数**:
- `private_key` (SigningKey): 椭圆曲线私钥
- `ciphertext` (bytes): 待解密的密文数据

**返回值**:
- `bytes`: 解密后的明文数据

**异常**:
- `ValueError`: 密文格式无效
- `CryptoError`: 解密过程失败

##### `sign(private_key, data)`
使用私钥对数据进行数字签名。

**参数**:
- `private_key` (SigningKey): 椭圆曲线私钥
- `data` (bytes): 待签名的数据

**返回值**:
- `bytes`: 数字签名数据

##### `verify(public_key, data, signature)`
使用公钥验证数字签名。

**参数**:
- `public_key` (VerifyingKey): 椭圆曲线公钥
- `data` (bytes): 原始数据
- `signature` (bytes): 数字签名

**返回值**:
- `bool`: 验证结果，True表示签名有效

## 测试说明

### 运行测试套件
```bash
python test/test_sm2.py
```

## 安全注意事项

### 密码学安全
1. **密钥管理**: 私钥必须安全存储，避免泄露
2. **随机数质量**: 依赖系统提供的安全随机数源
3. **侧信道攻击**: 当前实现未针对侧信道攻击进行防护
4. **量子安全**: 椭圆曲线算法不具备量子计算抗性

### 使用限制
1. **演示目的**: 本实现主要用于教学和演示
2. **生产环境**: 生产环境使用需要额外的安全评估
3. **标准符合性**: 简化实现，与完整SM2标准可能存在差异
4. **性能优化**: 未进行生产级性能优化

## 项目结构

```
project5-commit1-sm2Basic/
├── src/
│   └── sm2.py                 # SM2核心实现
├── test/
│   └── test_sm2.py           # 完整测试套件
├── requirements.txt          # 项目依赖
└── README.md                # 项目文档
```

## 技术实现细节

### 椭圆曲线选择
- **曲线类型**: NIST P-256 (secp256r1)
- **安全等级**: 128位安全强度
- **标准符合**: 符合FIPS 186-4标准

### 加密实现
- **对称算法**: AES-CBC模式
- **密钥派生**: 从椭圆曲线点坐标派生
- **填充方案**: PKCS#7填充
- **初始向量**: 随机生成128位IV

### 签名实现
- **哈希算法**: SHA-256
- **签名格式**: DER编码
- **随机数**: 系统安全随机数生成器