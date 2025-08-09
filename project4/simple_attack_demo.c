#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>
#include "sm3.h"

/**
 * 简化的长度扩展攻击演示
 * 展示攻击者如何在不知道秘密的情况下，为扩展消息计算哈希值
 */

// 辅助函数：从哈希值恢复SM3内部状态
void hash_to_state(const uint8_t *hash, uint32_t *state) {
    for (int i = 0; i < 8; i++) {
        state[i] = ((uint32_t)hash[i*4] << 24) |
                   ((uint32_t)hash[i*4+1] << 16) |
                   ((uint32_t)hash[i*4+2] << 8) |
                   ((uint32_t)hash[i*4+3]);
    }
}

// 计算SM3填充
size_t calculate_sm3_padding(size_t message_len, uint8_t *padding) {
    uint64_t bit_len = message_len * 8;
    size_t pad_len = 0;
    
    // 添加0x80
    padding[pad_len++] = 0x80;
    
    // 计算需要的零填充
    size_t total_len = message_len + 1 + 8; // 消息 + 0x80 + 8字节长度
    size_t blocks = (total_len + 63) / 64;  // 向上取整到64字节边界
    size_t target_len = blocks * 64;
    size_t zeros_needed = target_len - message_len - 1 - 8;
    
    // 添加零填充
    memset(padding + pad_len, 0, zeros_needed);
    pad_len += zeros_needed;
    
    // 添加64位长度（大端序）
    for (int i = 7; i >= 0; i--) {
        padding[pad_len++] = (uint8_t)(bit_len >> (i * 8));
    }
    
    return pad_len;
}

int main() {
    printf("=== SM3长度扩展攻击简化演示 ===\n\n");
    
    // 场景设置
    const char *secret_key = "MySecretKey123";      // 攻击者不知道的秘密
    const char *known_message = "user=alice&role=user";  // 攻击者知道的消息
    const char *malicious_data = "&role=admin";      // 攻击者想要添加的数据
    
    // 1. 计算原始消息的哈希值（模拟已知的哈希值）
    char original[256];
    snprintf(original, sizeof(original), "%s%s", secret_key, known_message);
    size_t original_len = strlen(original);
    
    uint8_t original_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)original, original_len, original_hash);
    
    printf("原始消息: \"%s\"\n", known_message);
    printf("原始消息总长度: %zu 字节 (包含秘密密钥)\n", original_len);
    printf("原始哈希值: ");
    for (int i = 0; i < 16; i++) printf("%02x", original_hash[i]);
    printf("...\n\n");
    
    // 2. 攻击者执行长度扩展攻击
    printf("开始长度扩展攻击...\n");
    
    // 计算填充
    uint8_t padding[128];
    size_t padding_len = calculate_sm3_padding(original_len, padding);
    printf("计算填充长度: %zu 字节\n", padding_len);
    
    // 从哈希值恢复状态
    uint32_t recovered_state[8];
    hash_to_state(original_hash, recovered_state);
    printf("从哈希值恢复内部状态\n");
    
    // 设置攻击上下文
    sm3_context_t attack_ctx;
    sm3_init(&attack_ctx);
    memcpy(attack_ctx.state, recovered_state, sizeof(recovered_state));
    attack_ctx.count = original_len + padding_len;  // 设置已处理的字节数
    attack_ctx.buffer_len = 0;
    
    // 处理恶意数据
    sm3_update(&attack_ctx, (uint8_t*)malicious_data, strlen(malicious_data));
    
    uint8_t attack_hash[SM3_DIGEST_SIZE];
    sm3_final(&attack_ctx, attack_hash);
    
    printf("长度扩展攻击计算的哈希值: ");
    for (int i = 0; i < 16; i++) printf("%02x", attack_hash[i]);
    printf("...\n\n");
    
    // 3. 验证攻击结果
    printf("验证攻击结果:\n");
    
    // 构造完整的扩展消息
    size_t extended_len = original_len + padding_len + strlen(malicious_data);
    char *extended_message = malloc(extended_len + 1);
    
    memcpy(extended_message, original, original_len);
    memcpy(extended_message + original_len, padding, padding_len);
    memcpy(extended_message + original_len + padding_len, malicious_data, strlen(malicious_data));
    
    // 直接计算扩展消息的哈希值
    uint8_t direct_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)extended_message, extended_len, direct_hash);
    
    printf("直接计算扩展消息的哈希值: ");
    for (int i = 0; i < 16; i++) printf("%02x", direct_hash[i]);
    printf("...\n");
    
    // 比较结果
    if (memcmp(attack_hash, direct_hash, SM3_DIGEST_SIZE) == 0) {
        printf("攻击成功! 两个哈希值完全匹配!\n");
        printf("攻击者在不知道秘密密钥的情况下，成功计算出了扩展消息的哈希值\n\n");
        
        // 展示攻击效果
        printf("攻击效果分析:\n");
        printf("   原始消息: %s\n", known_message);
        printf("   扩展后的逻辑消息: %s%s\n", known_message, malicious_data);
        printf("   攻击者成功将用户权限从 'user' 提升到 'admin'\n\n");
    } else {
        printf("攻击失败，哈希值不匹配\n\n");
    }
    
    // 4. 展示如何防御
    printf("防御方法演示:\n");
    
    // 错误方法
    printf("易受攻击: H(secret || message)\n");
    char vulnerable[256];
    snprintf(vulnerable, sizeof(vulnerable), "%s%s%s", secret_key, known_message, malicious_data);
    uint8_t vuln_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)vulnerable, strlen(vulnerable), vuln_hash);
    printf("   结果: ");
    for (int i = 0; i < 16; i++) printf("%02x", vuln_hash[i]);
    printf("... (可被长度扩展攻击)\n");
    
    // 正确方法 - HMAC风格
    printf("安全方法: H(secret || H(secret || message))\n");
    char inner[256];
    snprintf(inner, sizeof(inner), "%s%s%s", secret_key, known_message, malicious_data);
    uint8_t inner_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)inner, strlen(inner), inner_hash);
    
    char outer[256];
    memcpy(outer, secret_key, strlen(secret_key));
    memcpy(outer + strlen(secret_key), inner_hash, SM3_DIGEST_SIZE);
    
    uint8_t secure_hash[SM3_DIGEST_SIZE];
    sm3_hash((uint8_t*)outer, strlen(secret_key) + SM3_DIGEST_SIZE, secure_hash);
    printf("   结果: ");
    for (int i = 0; i < 16; i++) printf("%02x", secure_hash[i]);
    printf("... (抵抗长度扩展攻击)\n\n");
    
    printf("学习总结:\n");
    printf("• 长度扩展攻击利用了Merkle-Damgård结构的特性\n");
    printf("• 攻击者只需要知道哈希值和消息长度，不需要知道秘密内容\n");
    printf("• 在实际应用中，应该使用HMAC或其他安全的消息认证方法\n");
    printf("• 简单的 H(secret || message) 模式是不安全的\n");
    
    free(extended_message);
    return 0;
}
