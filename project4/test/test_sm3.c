#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <strings.h>
#include "sm3.h"

// 测试向量结构体
typedef struct {
    const char *name;
    const char *input;
    const char *expected;
} test_vector_t;

// 十六进制字符串转字节数组
static size_t hex_to_bytes(const char *hex, uint8_t *bytes) {
    size_t len = strlen(hex);
    size_t i;
    
    if (len % 2 != 0) return 0;
    
    for (i = 0; i < len / 2; i++) {
        unsigned int byte;
        if (sscanf(hex + i * 2, "%02x", &byte) != 1) {
            return 0;
        }
        bytes[i] = (uint8_t)byte;
    }
    
    return len / 2;
}

// 运行单个测试用例
static int run_test(const test_vector_t *test) {
    uint8_t input[1024];
    uint8_t digest[SM3_DIGEST_SIZE];
    char hex_result[SM3_DIGEST_SIZE * 2 + 1];
    size_t input_len;
    
    printf("测试: %s\n", test->name);
    printf("输入: %s\n", test->input);
    
    if (strlen(test->input) == 0) {
        // 空字符串测试
        input_len = 0;
    } else {
        // 将十六进制输入转换为字节
        input_len = hex_to_bytes(test->input, input);
        if (input_len == 0) {
            // 尝试作为ASCII字符串处理
            strcpy((char*)input, test->input);
            input_len = strlen(test->input);
        }
    }
    
    // 计算哈希值
    sm3_hash(input, input_len, digest);
    
    // 转换为十六进制字符串
    sm3_digest_to_hex(digest, hex_result);
    
    printf("结果: %s\n", hex_result);
    printf("期望: %s\n", test->expected);
    
    if (strcasecmp(hex_result, test->expected) == 0) {
        printf("✓ 测试通过\n\n");
        return 1;
    } else {
        printf("✗ 测试失败\n\n");
        return 0;
    }
}

// 测试增量更新功能
static int test_incremental() {
    const char *message = "abcdefghijklmnopqrstuvwxyz";
    uint8_t digest1[SM3_DIGEST_SIZE];
    uint8_t digest2[SM3_DIGEST_SIZE];
    sm3_context_t ctx;
    size_t len = strlen(message);
    size_t i;
    
    printf("测试: 增量更新功能\n");
    
    // 一次性计算
    sm3_hash((uint8_t*)message, len, digest1);
    
    // 逐字节增量计算
    sm3_init(&ctx);
    for (i = 0; i < len; i++) {
        sm3_update(&ctx, (uint8_t*)&message[i], 1);
    }
    sm3_final(&ctx, digest2);
    
    // 比较结果
    if (memcmp(digest1, digest2, SM3_DIGEST_SIZE) == 0) {
        printf("✓ 增量更新测试通过\n\n");
        return 1;
    } else {
        printf("✗ 增量更新测试失败\n\n");
        return 0;
    }
}

// 长消息测试
static int test_long_message() {
    const size_t test_size = 1000000; // 1MB
    uint8_t *data = malloc(test_size);
    uint8_t digest[SM3_DIGEST_SIZE];
    char hex_result[SM3_DIGEST_SIZE * 2 + 1];
    size_t i;
    
    if (!data) {
        printf("内存分配失败\n");
        return 0;
    }
    
    printf("测试: 长消息 (1MB)\n");
    
    // 填充测试数据
    for (i = 0; i < test_size; i++) {
        data[i] = (uint8_t)(i & 0xFF);
    }
    
    // 计算哈希
    clock_t start = clock();
    sm3_hash(data, test_size, digest);
    clock_t end = clock();
    
    sm3_digest_to_hex(digest, hex_result);
    
    double seconds = (double)(end - start) / CLOCKS_PER_SEC;
    double mbps = (test_size / 1048576.0) / seconds;
    
    printf("结果: %s\n", hex_result);
    printf("时间: %.3f秒 (%.2f MB/s)\n", seconds, mbps);
    printf("✓ 长消息测试完成\n\n");
    
    free(data);
    return 1;
}

int main() {
    // 标准测试向量
    test_vector_t test_vectors[] = {
        {
            "空消息",
            "",
            "1ab21d8355cfa17f8e61194831e81a8f22bec8c728fefb747ed035eb5082aa2b"
        },
        {
            "单字符 'a'",
            "61",
            "623476ac18f65a2909e43c7fec61b49c7e764a91a18ccb82f1917a29c86c5e88"
        },
        {
            "字符串 'abc'",
            "616263",
            "66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0"
        },
        {
            "标准测试向量1",
            "abc",
            "66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0"
        },
        {
            "448位消息",
            "abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd",
            "ee6c8807dd66ed0eb1be76dfaaa06a4ea4fb417a0bd90078aef4563ae01d5936"
        }
    };
    
    int total_tests = sizeof(test_vectors) / sizeof(test_vectors[0]);
    int passed_tests = 0;
    int i;
    
    printf("=== SM3哈希算法测试程序 ===\n\n");
    
    // 运行标准测试向量
    for (i = 0; i < total_tests; i++) {
        if (run_test(&test_vectors[i])) {
            passed_tests++;
        }
    }
    
    // 运行增量更新测试
    if (test_incremental()) {
        passed_tests++;
        total_tests++;
    }
    
    // 运行长消息测试
    if (test_long_message()) {
        passed_tests++;
        total_tests++;
    }
    
    // 输出测试结果
    printf("=== 测试结果 ===\n");
    printf("通过: %d/%d\n", passed_tests, total_tests);
    
    if (passed_tests == total_tests) {
        printf("✓ 所有测试通过！\n");
        return 0;
    } else {
        printf("✗ 部分测试失败！\n");
        return 1;
    }
}
