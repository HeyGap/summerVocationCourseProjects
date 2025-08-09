# SM3长度扩展攻击验证

## 概述

本程序演示了针对SM3哈希算法的长度扩展攻击（Length Extension Attack）。长度扩展攻击是针对基于Merkle-Damgård结构的哈希函数的一种攻击方法，包括SM3、MD5、SHA-1、SHA-2等算法都存在这个漏洞。

## 攻击原理

### Merkle-Damgård结构的漏洞

SM3哈希算法采用Merkle-Damgård结构，其工作原理如下：

1. **初始化**：设置初始哈希值（IV）
2. **填充**：对输入消息进行填充，使其长度为512位的倍数
3. **分块处理**：将填充后的消息分成512位的块，依次处理
4. **压缩函数**：每一块都通过压缩函数更新内部状态
5. **输出**：最终的内部状态就是哈希值

### 攻击关键点

长度扩展攻击的核心在于：**如果知道了消息M的哈希值H(M)和长度，就可以计算出H(M || padding || X)的值**，其中：
- `||` 表示拼接操作
- `padding` 是SM3算法自动添加的填充数据
- `X` 是攻击者想要添加的任意数据

这是因为：
1. 哈希值H(M)实际上就是处理完消息M后的内部状态
2. 攻击者可以从这个状态继续，直接处理新的数据块

## 攻击步骤

### 1. 已知信息
- 原始消息的哈希值：`H(secret || known_data)`
- 原始消息的长度
- 不知道secret的具体内容

### 2. 计算填充
根据SM3的填充规则计算原始消息的填充：
```
填充 = 0x80 || 零填充 || 64位长度
```

### 3. 构造新消息
```
新消息 = secret || known_data || 填充 || 恶意数据
```

### 4. 计算新哈希值
1. 从原始哈希值恢复内部状态
2. 设置已处理字节数为原始消息+填充的长度
3. 使用SM3的update函数处理恶意数据
4. 调用final函数得到最终哈希值

## 代码实现要点

### 填充计算
```c
void construct_padding(size_t original_length, uint8_t *padding, size_t *padding_len) {
    uint64_t bit_count = original_length * 8;
    
    // 添加0x80
    padding[0] = 0x80;
    
    // 计算零填充长度
    size_t total_with_length = original_length + 1 + 8;
    size_t blocks_needed = (total_with_length + 63) / 64;
    size_t zero_padding = blocks_needed * 64 - original_length - 1 - 8;
    
    // 添加零填充和长度
    memset(padding + 1, 0, zero_padding);
    // 添加64位长度（大端序）
    // ...
}
```

### 状态恢复
```c
// 从哈希值恢复内部状态
void hash_to_state(const uint8_t *hash, uint32_t *state) {
    for (int i = 0; i < 8; i++) {
        state[i] = ((uint32_t)hash[i*4] << 24) |
                   ((uint32_t)hash[i*4+1] << 16) |
                   ((uint32_t)hash[i*4+2] << 8) |
                   ((uint32_t)hash[i*4+3]);
    }
}
```

### 攻击执行
```c
// 设置攻击上下文
sm3_context_t attack_ctx;
sm3_init(&attack_ctx);
memcpy(attack_ctx.state, recovered_state, sizeof(recovered_state));
attack_ctx.count = original_len + padding_len;  // 关键：设置正确的计数

// 处理恶意数据
sm3_update(&attack_ctx, malicious_data, malicious_len);
sm3_final(&attack_ctx, attack_hash);
```

## 攻击影响

### 安全风险
1. **消息认证绕过**：攻击者可以在不知道密钥的情况下，为扩展后的消息生成有效的哈希值
2. **完整性破坏**：原本用于验证消息完整性的哈希值被恶意利用
3. **权限提升**：在某些应用场景中，可能导致权限提升攻击

### 实际应用场景
1. **API签名绕过**：`sign = H(secret_key || api_params)`
2. **文件完整性验证绕过**：`integrity = H(password || file_content)`
3. **会话令牌伪造**：`token = H(session_secret || user_data)`

## 防御方法

### 1. HMAC（推荐）
使用标准的HMAC算法：
```
HMAC(key, message) = H((key ⊕ opad) || H((key ⊕ ipad) || message))
```

### 2. 双重哈希
```
secure_hash = H(key || H(key || message))
```

### 3. 密钥后置（有限防御）
```
hash = H(message || key)
```
注意：这种方法只能防御长度扩展攻击，但可能受到其他攻击。

### 4. 使用抗长度扩展攻击的哈希函数
- SHA-3（Keccak）
- BLAKE2/BLAKE3
- 其他非Merkle-Damgård结构的哈希函数

## 运行演示

编译并运行：
```bash
make attack
```

程序将演示：
1. 成功的长度扩展攻击
2. 各种防御方法的效果
3. 攻击前后哈希值的对比

## 学习要点

1. **理解Merkle-Damgård结构的内在漏洞**
2. **掌握哈希函数的填充机制**
3. **认识到简单哈希验证的安全风险**
4. **学会使用HMAC等安全的消息认证方法**

## 总结

长度扩展攻击揭示了直接使用哈希函数进行消息认证的危险性。在实际应用中，应当：
1. 避免使用 `H(secret || message)` 的模式
2. 优先使用经过验证的HMAC算法
3. 或者使用不受长度扩展攻击影响的哈希函数

这个漏洞提醒我们：密码学原语的正确使用同算法本身的安全性一样重要。
