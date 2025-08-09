#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>
#include "sm3.h"

/**
 * 计算填充长度
 * 给定原始消息长度，计算SM3填充后的总长度
 */
size_t calculate_padding_length(size_t original_length) {
    // SM3填充规则：消息 + 0x80 + 零填充 + 64位长度
    // 总长度必须是512位(64字节)的倍数
    size_t total_bits = original_length * 8;
    size_t padded_bits = ((total_bits + 64 + 511) / 512) * 512;
    return padded_bits / 8;
}

/**
 * 构造填充数据
 * 根据原始消息长度构造SM3填充
 */
void construct_padding(size_t original_length, uint8_t *padding, size_t *padding_len) {
    uint64_t bit_count = original_length * 8;
    size_t bytes_after_msg = 0;
    
    // 添加0x80
    padding[bytes_after_msg++] = 0x80;
    
    // 计算需要多少零填充
    size_t total_with_length = original_length + 1 + 8; // 消息 + 0x80 + 8字节长度
    size_t blocks_needed = (total_with_length + 63) / 64; // 向上取整到64字节边界
    size_t padded_length = blocks_needed * 64;
    size_t zero_padding = padded_length - original_length - 1 - 8;
    
    // 添加零填充
    memset(padding + bytes_after_msg, 0, zero_padding);
    bytes_after_msg += zero_padding;
    
    // 添加64位长度（大端序）
    padding[bytes_after_msg++] = (uint8_t)(bit_count >> 56);
    padding[bytes_after_msg++] = (uint8_t)(bit_count >> 48);
    padding[bytes_after_msg++] = (uint8_t)(bit_count >> 40);
    padding[bytes_after_msg++] = (uint8_t)(bit_count >> 32);
    padding[bytes_after_msg++] = (uint8_t)(bit_count >> 24);
    padding[bytes_after_msg++] = (uint8_t)(bit_count >> 16);
    padding[bytes_after_msg++] = (uint8_t)(bit_count >> 8);
    padding[bytes_after_msg++] = (uint8_t)bit_count;
    
    *padding_len = bytes_after_msg;
}

/**
 * 从哈希值恢复内部状态
 */
void hash_to_state(const uint8_t *hash, uint32_t *state) {
    for (int i = 0; i < 8; i++) {
        state[i] = ((uint32_t)hash[i*4] << 24) |
                   ((uint32_t)hash[i*4+1] << 16) |
                   ((uint32_t)hash[i*4+2] << 8) |
                   ((uint32_t)hash[i*4+3]);
    }
}

/**
 * 从内部状态生成哈希值
 */
void state_to_hash(const uint32_t *state, uint8_t *hash) {
    for (int i = 0; i < 8; i++) {
        hash[i*4] = (uint8_t)(state[i] >> 24);
        hash[i*4+1] = (uint8_t)(state[i] >> 16);
        hash[i*4+2] = (uint8_t)(state[i] >> 8);
        hash[i*4+3] = (uint8_t)state[i];
    }
}

/**
 * 长度扩展攻击实现
 */
void length_extension_attack() {
    printf("=== SM3长度扩展攻击演示 ===\n\n");
    
    // 模拟场景：我们知道某个秘密消息的哈希值，但不知道消息内容
    const char *secret = "secret_key_123456";  // 这是我们不知道的秘密
    const char *known_suffix = "public_data";   // 这是我们知道的公开数据
    const char *malicious_data = "HACKED_DATA"; // 这是我们想要添加的恶意数据
    
    // 攻击者已知信息：
    size_t secret_len = strlen(secret);  // 假设攻击者通过某种方式知道了长度
    
    // 1. 计算原始消息的哈希值（模拟已知的哈希值）
    char original_message[256];
    snprintf(original_message, sizeof(original_message), "%s%s", secret, known_suffix);
    uint8_t original_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)original_message, strlen(original_message), original_hash);
    
    printf("原始消息: \"%s%s\"\n", secret, known_suffix);
    printf("原始消息长度: %zu 字节\n", strlen(original_message));
    printf("原始哈希值: ");
    sm3_print_digest(original_hash);
    printf("\n");
    
    // 2. 攻击者进行长度扩展攻击
    printf("=== 开始长度扩展攻击 ===\n");
    
    // 计算原始消息的填充
    size_t original_len = strlen(original_message);
    uint8_t padding[128];
    size_t padding_len;
    construct_padding(original_len, padding, &padding_len);
    
    printf("计算得到的填充长度: %zu 字节\n", padding_len);
    
    // 构造扩展后的消息
    char extended_message[512];
    size_t extended_len = 0;
    
    // 复制原始消息
    memcpy(extended_message, original_message, original_len);
    extended_len += original_len;
    
    // 添加填充
    memcpy(extended_message + extended_len, padding, padding_len);
    extended_len += padding_len;
    
    // 添加恶意数据
    memcpy(extended_message + extended_len, malicious_data, strlen(malicious_data));
    extended_len += strlen(malicious_data);
    
    printf("构造的扩展消息长度: %zu 字节\n", extended_len);
    
    // 3. 使用长度扩展攻击计算新哈希值
    // 从原始哈希值恢复内部状态
    uint32_t state[8];
    hash_to_state(original_hash, state);
    
    // 创建SM3上下文并设置为攻击状态
    sm3_context_t attack_ctx;
    sm3_init(&attack_ctx);
    
    // 设置内部状态为原始哈希值对应的状态
    memcpy(attack_ctx.state, state, sizeof(state));
    
    // 设置已处理的字节数（原始消息 + 填充的长度）
    attack_ctx.count = original_len + padding_len;
    attack_ctx.buffer_len = 0;
    
    // 处理恶意数据
    sm3_update(&attack_ctx, (uint8_t*)malicious_data, strlen(malicious_data));
    
    uint8_t attack_hash[SM3_DIGEST_SIZE];
    sm3_final(&attack_ctx, attack_hash);
    
    printf("长度扩展攻击计算的哈希值: ");
    sm3_print_digest(attack_hash);
    
    // 4. 验证攻击结果
    printf("\n=== 验证攻击结果 ===\n");
    
    // 直接计算扩展消息的哈希值
    uint8_t direct_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)extended_message, extended_len, direct_hash);
    
    printf("直接计算扩展消息的哈希值: ");
    sm3_print_digest(direct_hash);
    
    // 比较结果
    if (memcmp(attack_hash, direct_hash, SM3_DIGEST_SIZE) == 0) {
        printf("✓ 长度扩展攻击成功！哈希值匹配\n");
        printf("✓ 攻击者在不知道秘密的情况下，成功计算出了扩展消息的哈希值\n");
    } else {
        printf("✗ 长度扩展攻击失败，哈希值不匹配\n");
    }
    
    printf("\n=== 攻击总结 ===\n");
    printf("1. 攻击者已知: 原始消息的哈希值和长度\n");
    printf("2. 攻击者未知: 原始消息的具体内容（包含秘密）\n");
    printf("3. 攻击结果: 成功计算出了 原始消息+填充+恶意数据 的哈希值\n");
    printf("4. 安全影响: 破坏了基于哈希的消息认证的完整性\n");
}

/**
 * 演示如何防御长度扩展攻击
 */
void demonstrate_defense() {
    printf("\n\n=== 长度扩展攻击防御方法演示 ===\n");
    
    const char *secret = "secret_key_123456";
    const char *message = "important_data";
    
    printf("秘密密钥: \"%s\"\n", secret);
    printf("要认证的消息: \"%s\"\n\n", message);
    
    // 错误的方法：直接拼接后计算哈希 H(secret || message)
    printf("1. 易受攻击的方法: H(secret || message)\n");
    char vulnerable[256];
    snprintf(vulnerable, sizeof(vulnerable), "%s%s", secret, message);
    uint8_t vulnerable_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)vulnerable, strlen(vulnerable), vulnerable_hash);
    printf("   结果: ");
    sm3_print_digest(vulnerable_hash);
    printf("   ✗ 容易受到长度扩展攻击\n\n");
    
    // 正确的方法1：HMAC结构 H(secret || H(secret || message))
    printf("2. 较安全的方法: H(secret || H(secret || message))\n");
    uint8_t inner_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)vulnerable, strlen(vulnerable), inner_hash);
    
    char outer[256];
    memcpy(outer, secret, strlen(secret));
    memcpy(outer + strlen(secret), inner_hash, SM3_DIGEST_SIZE);
    
    uint8_t secure_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)outer, strlen(secret) + SM3_DIGEST_SIZE, secure_hash);
    printf("   结果: ");
    sm3_print_digest(secure_hash);
    printf("   ✓ 抵抗长度扩展攻击\n\n");
    
    // 正确的方法2：将秘密放在后面 H(message || secret)
    printf("3. 简单的防御方法: H(message || secret)\n");
    char suffix_secret[256];
    snprintf(suffix_secret, sizeof(suffix_secret), "%s%s", message, secret);
    uint8_t suffix_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)suffix_secret, strlen(suffix_secret), suffix_hash);
    printf("   结果: ");
    sm3_print_digest(suffix_hash);
    printf("   ✓ 抵抗长度扩展攻击\n");
    printf("   注意: 但可能受到其他类型的攻击\n\n");
    
    printf("推荐使用标准的HMAC算法来防御长度扩展攻击。\n");
}

int main() {
    printf("SM3长度扩展攻击验证程序\n");
    printf("========================\n\n");
    
    // 执行长度扩展攻击演示
    length_extension_attack();
    
    // 演示防御方法
    demonstrate_defense();
    
    return 0;
}
