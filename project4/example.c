#include <stdio.h>
#include <string.h>
#include "sm3.h"

int main() {
    const char *message = "Hello, SM3!";
    uint8_t digest[SM3_DIGEST_SIZE];
    char hex_output[SM3_DIGEST_SIZE * 2 + 1];
    
    printf("SM3哈希算法使用示例\n");
    printf("==================\n\n");
    
    printf("输入消息: \"%s\"\n", message);
    printf("消息长度: %zu 字节\n\n", strlen(message));
    
    // 计算哈希值
    sm3_hash((uint8_t*)message, strlen(message), digest);
    
    // 转换为十六进制字符串
    sm3_digest_to_hex(digest, hex_output);
    
    printf("SM3哈希值: %s\n\n", hex_output);
    
    // 演示增量更新
    printf("增量更新示例:\n");
    sm3_context_t ctx;
    uint8_t digest2[SM3_DIGEST_SIZE];
    char hex_output2[SM3_DIGEST_SIZE * 2 + 1];
    
    sm3_init(&ctx);
    sm3_update(&ctx, (uint8_t*)"Hello, ", 7);
    sm3_update(&ctx, (uint8_t*)"SM3!", 4);
    sm3_final(&ctx, digest2);
    
    sm3_digest_to_hex(digest2, hex_output2);
    printf("增量计算结果: %s\n", hex_output2);
    
    // 验证结果一致性
    if (memcmp(digest, digest2, SM3_DIGEST_SIZE) == 0) {
        printf("✓ 一次性计算和增量计算结果一致\n");
    } else {
        printf("✗ 计算结果不一致\n");
    }
    
    return 0;
}
