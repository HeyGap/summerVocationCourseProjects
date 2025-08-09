#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "sm3.h"
#include "sm3_opt.h"

int main() {
    printf("SM3哈希算法优化性能测试\n");
    printf("======================\n\n");
    
    // CPU特性检测
    cpu_features_t features = sm3_detect_cpu_features();
    printf("CPU特性: SSE2=%s, AVX2=%s\n\n",
           features.sse2_support ? "支持" : "不支持",
           features.avx2_support ? "支持" : "不支持");
    
    // 测试数据
    const char *test_data = "这是一个用于测试SM3哈希算法性能的较长文本字符串。"
                           "We will test the performance of different implementations "
                           "including the basic version and optimized versions.";
    
    size_t len = strlen(test_data);
    printf("测试数据长度: %zu 字节\n\n", len);
    
    uint8_t digest[SM3_DIGEST_SIZE];
    
    // 基础实现性能测试
    clock_t start = clock();
    for (int i = 0; i < 10000; i++) {
        sm3_hash((const uint8_t*)test_data, len, digest);
    }
    clock_t end = clock();
    double basic_time = ((double)(end - start)) / CLOCKS_PER_SEC;
    
    printf("基础实现: %.3f秒 (10000次)\n", basic_time);
    printf("基础结果: ");
    for (int i = 0; i < SM3_DIGEST_SIZE; i++) {
        printf("%02x", digest[i]);
    }
    printf("\n\n");
    
    // 快速实现性能测试
    uint8_t fast_digest[SM3_DIGEST_SIZE];
    start = clock();
    for (int i = 0; i < 10000; i++) {
        sm3_fast_hash((const uint8_t*)test_data, len, fast_digest);
    }
    end = clock();
    double fast_time = ((double)(end - start)) / CLOCKS_PER_SEC;
    
    printf("快速实现: %.3f秒 (10000次)\n", fast_time);
    printf("快速结果: ");
    for (int i = 0; i < SM3_DIGEST_SIZE; i++) {
        printf("%02x", fast_digest[i]);
    }
    printf("\n");
    
    // 验证结果正确性
    if (memcmp(digest, fast_digest, SM3_DIGEST_SIZE) == 0) {
        printf("正确性验证: ✓ 结果一致\n");
    } else {
        printf("正确性验证: ✗ 结果不一致\n");
    }
    
    // 性能对比
    if (fast_time < basic_time) {
        printf("性能提升: %.2fx 加速\n", basic_time / fast_time);
    } else {
        printf("性能对比: %.2fx 倍慢 (小数据SIMD开销)\n", fast_time / basic_time);
    }
    
    // 大数据测试
    printf("\n=== 大数据性能测试 ===\n");
    size_t big_size = 64 * 1024; // 64KB
    uint8_t *big_data = malloc(big_size);
    if (big_data) {
        for (size_t i = 0; i < big_size; i++) {
            big_data[i] = (uint8_t)(i & 0xFF);
        }
        
        printf("大数据长度: %zu 字节\n", big_size);
        
        // 基础实现
        start = clock();
        for (int i = 0; i < 100; i++) {
            sm3_hash(big_data, big_size, digest);
        }
        end = clock();
        basic_time = ((double)(end - start)) / CLOCKS_PER_SEC;
        
        // 快速实现
        start = clock();
        for (int i = 0; i < 100; i++) {
            sm3_fast_hash(big_data, big_size, fast_digest);
        }
        end = clock();
        fast_time = ((double)(end - start)) / CLOCKS_PER_SEC;
        
        printf("基础实现: %.3f秒 (100次)\n", basic_time);
        printf("快速实现: %.3f秒 (100次)\n", fast_time);
        
        if (memcmp(digest, fast_digest, SM3_DIGEST_SIZE) == 0) {
            printf("正确性验证: ✓ 结果一致\n");
        } else {
            printf("正确性验证: ✗ 结果不一致\n");
        }
        
        if (fast_time < basic_time) {
            printf("大数据加速: %.2fx\n", basic_time / fast_time);
        } else {
            printf("大数据性能: %.2fx 倍慢\n", fast_time / basic_time);
        }
        
        free(big_data);
    }
    
    return 0;
}
