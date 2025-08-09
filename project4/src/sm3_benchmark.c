#include "sm3_opt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>

// 获取当前时间（微秒精度）
static double get_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}

// 验证优化实现的正确性
int sm3_verify_optimizations(void) {
    const char *test_vectors[] = {
        "abc",
        "abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd",
        "",
        "a",
        "message digest",
        "abcdefghijklmnopqrstuvwxyz",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
        "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
    };
    
    int num_tests = sizeof(test_vectors) / sizeof(test_vectors[0]);
    int passed = 0;
    
    printf("验证优化实现的正确性:\n");
    printf("===================\n");
    
    for (int i = 0; i < num_tests; i++) {
        const uint8_t *data = (const uint8_t*)test_vectors[i];
        size_t len = strlen(test_vectors[i]);
        
        uint8_t digest_basic[SM3_DIGEST_SIZE];
        uint8_t digest_sse2[SM3_DIGEST_SIZE];
        uint8_t digest_avx2[SM3_DIGEST_SIZE];
        
        // 基础实现
        sm3_hash(data, len, digest_basic);
        
        // 优化实现
        sm3_opt_hash(data, len, digest_sse2, SM3_IMPL_SSE2);
        sm3_opt_hash(data, len, digest_avx2, SM3_IMPL_AVX2);
        
        // 比较结果
        int sse2_match = memcmp(digest_basic, digest_sse2, SM3_DIGEST_SIZE) == 0;
        int avx2_match = memcmp(digest_basic, digest_avx2, SM3_DIGEST_SIZE) == 0;
        
        printf("测试 %d: \"%s\"\n", i + 1, test_vectors[i]);
        printf("  基础实现: ");
        for (int j = 0; j < 8; j++) {
            printf("%02x", digest_basic[j]);
        }
        printf("...\n");
        
        printf("  SSE2实现: %s\n", sse2_match ? "PASS" : "FAIL");
        printf("  AVX2实现: %s\n", avx2_match ? "PASS" : "FAIL");
        
        if (sse2_match && avx2_match) {
            passed++;
        }
        printf("\n");
    }
    
    printf("测试结果: %d/%d 通过\n", passed, num_tests);
    return passed == num_tests;
}

// 单项性能测试
static double benchmark_single_impl(const uint8_t *data, size_t len, int iterations,
                                   void (*hash_func)(const uint8_t*, size_t, uint8_t*),
                                   const char *impl_name) {
    uint8_t digest[SM3_DIGEST_SIZE];
    double start_time, end_time;
    
    start_time = get_time();
    for (int i = 0; i < iterations; i++) {
        hash_func(data, len, digest);
    }
    end_time = get_time();
    
    double total_time = end_time - start_time;
    double throughput = (len * iterations) / (total_time * 1048576.0); // MB/s
    
    printf("%-12s: %.3fs, %.2f MB/s\n", impl_name, total_time, throughput);
    
    return total_time;
}

// 包装函数
static void hash_basic(const uint8_t *data, size_t len, uint8_t *digest) {
    sm3_hash(data, len, digest);
}

static void hash_sse2(const uint8_t *data, size_t len, uint8_t *digest) {
    sm3_opt_hash(data, len, digest, SM3_IMPL_SSE2);
}

static void hash_avx2(const uint8_t *data, size_t len, uint8_t *digest) {
    sm3_opt_hash(data, len, digest, SM3_IMPL_AVX2);
}

static void hash_auto(const uint8_t *data, size_t len, uint8_t *digest) {
    sm3_opt_hash(data, len, digest, SM3_IMPL_AUTO);
}

// 多流并行测试
static void benchmark_multiway(size_t data_size, int iterations) {
    uint8_t *data1 = malloc(data_size);
    uint8_t *data2 = malloc(data_size);
    uint8_t *data3 = malloc(data_size);
    uint8_t *data4 = malloc(data_size);
    
    uint8_t digest1[SM3_DIGEST_SIZE], digest2[SM3_DIGEST_SIZE];
    uint8_t digest3[SM3_DIGEST_SIZE], digest4[SM3_DIGEST_SIZE];
    
    if (!data1 || !data2 || !data3 || !data4) {
        printf("内存分配失败\n");
        goto cleanup;
    }
    
    // 填充测试数据
    for (size_t i = 0; i < data_size; i++) {
        data1[i] = (uint8_t)(i & 0xFF);
        data2[i] = (uint8_t)((i + 1) & 0xFF);
        data3[i] = (uint8_t)((i + 2) & 0xFF);
        data4[i] = (uint8_t)((i + 3) & 0xFF);
    }
    
    printf("\n多流并行测试 (数据大小: %zu 字节, 迭代: %d次):\n", data_size, iterations);
    printf("========================================\n");
    
    // 串行4次调用
    double start_time = get_time();
    for (int i = 0; i < iterations; i++) {
        sm3_hash(data1, data_size, digest1);
        sm3_hash(data2, data_size, digest2);
        sm3_hash(data3, data_size, digest3);
        sm3_hash(data4, data_size, digest4);
    }
    double serial_time = get_time() - start_time;
    
    // 4路并行
    start_time = get_time();
    for (int i = 0; i < iterations; i++) {
        sm3_hash_4way_avx2(data1, data_size, data2, data_size,
                          data3, data_size, data4, data_size,
                          digest1, digest2, digest3, digest4);
    }
    double parallel_time = get_time() - start_time;
    
    double serial_throughput = (data_size * 4 * iterations) / (serial_time * 1048576.0);
    double parallel_throughput = (data_size * 4 * iterations) / (parallel_time * 1048576.0);
    double speedup = serial_time / parallel_time;
    
    printf("串行执行    : %.3fs, %.2f MB/s\n", serial_time, serial_throughput);
    printf("4路并行     : %.3fs, %.2f MB/s\n", parallel_time, parallel_throughput);
    printf("加速比      : %.2fx\n", speedup);
    
cleanup:
    free(data1);
    free(data2);
    free(data3);
    free(data4);
}

// 运行所有基准测试
sm3_benchmark_result_t sm3_run_benchmarks(const uint8_t *data, size_t len, int iterations) {
    sm3_benchmark_result_t result = {0};
    
    printf("\nSM3优化实现性能基准测试\n");
    printf("=======================\n");
    printf("数据大小: %zu 字节\n", len);
    printf("迭代次数: %d 次\n\n", iterations);
    
    // 显示CPU特性
    cpu_features_t features = sm3_detect_cpu_features();
    printf("CPU特性支持:\n");
    printf("  SSE2: %s\n", features.sse2_support ? "是" : "否");
    printf("  AVX2: %s\n", features.avx2_support ? "是" : "否");
    printf("  AES:  %s\n\n", features.aes_support ? "是" : "否");
    
    // 单实现基准测试
    printf("单实现性能比较:\n");
    result.basic_time = benchmark_single_impl(data, len, iterations, hash_basic, "基础实现");
    result.sse2_time = benchmark_single_impl(data, len, iterations, hash_sse2, "SSE2优化");
    result.avx2_time = benchmark_single_impl(data, len, iterations, hash_avx2, "AVX2优化");
    
    double auto_time = benchmark_single_impl(data, len, iterations, hash_auto, "自动选择");
    
    printf("\n加速比:\n");
    printf("  SSE2 vs 基础: %.2fx\n", result.basic_time / result.sse2_time);
    printf("  AVX2 vs 基础: %.2fx\n", result.basic_time / result.avx2_time);
    printf("  自动 vs 基础: %.2fx\n", result.basic_time / auto_time);
    
    // 多流并行测试
    benchmark_multiway(len, iterations / 10);
    
    return result;
}

// 不同大小数据的综合测试
void sm3_comprehensive_benchmark(void) {
    size_t sizes[] = {64, 256, 1024, 4096, 16384, 65536};
    int iterations[] = {10000, 5000, 2000, 500, 100, 20};
    int num_sizes = sizeof(sizes) / sizeof(sizes[0]);
    
    printf("\n=== SM3优化实现综合性能测试 ===\n");
    
    for (int i = 0; i < num_sizes; i++) {
        uint8_t *test_data = malloc(sizes[i]);
        if (!test_data) {
            printf("内存分配失败，跳过大小 %zu\n", sizes[i]);
            continue;
        }
        
        // 填充测试数据
        for (size_t j = 0; j < sizes[i]; j++) {
            test_data[j] = (uint8_t)(j & 0xFF);
        }
        
        printf("\n--- 数据大小: %zu 字节 ---\n", sizes[i]);
        sm3_run_benchmarks(test_data, sizes[i], iterations[i]);
        
        free(test_data);
    }
}
