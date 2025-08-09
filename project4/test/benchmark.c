#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include "sm3.h"

// 获取当前时间（微秒）
static double get_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}

// 性能测试函数
static void benchmark_sm3(size_t data_size, int iterations) {
    uint8_t *data = malloc(data_size);
    uint8_t digest[SM3_DIGEST_SIZE];
    double start_time, end_time, total_time;
    double throughput;
    int i;
    
    if (!data) {
        printf("内存分配失败\n");
        return;
    }
    
    // 填充随机数据
    srand((unsigned int)time(NULL));
    for (i = 0; i < (int)data_size; i++) {
        data[i] = (uint8_t)(rand() & 0xFF);
    }
    
    printf("数据大小: %zu 字节, 迭代次数: %d\n", data_size, iterations);
    
    // 性能测试
    start_time = get_time();
    for (i = 0; i < iterations; i++) {
        sm3_hash(data, data_size, digest);
    }
    end_time = get_time();
    
    total_time = end_time - start_time;
    throughput = (data_size * iterations) / (total_time * 1048576.0); // MB/s
    
    printf("总时间: %.3f 秒\n", total_time);
    printf("平均时间: %.6f 秒/次\n", total_time / iterations);
    printf("吞吐量: %.2f MB/s\n", throughput);
    printf("处理速度: %.0f 字节/秒\n\n", (data_size * iterations) / total_time);
    
    free(data);
}

// 增量更新性能测试
static void benchmark_incremental(size_t total_size, size_t chunk_size) {
    uint8_t *data = malloc(total_size);
    uint8_t digest[SM3_DIGEST_SIZE];
    sm3_context_t ctx;
    double start_time, end_time;
    double throughput;
    size_t processed = 0;
    
    if (!data) {
        printf("内存分配失败\n");
        return;
    }
    
    // 填充测试数据
    for (size_t i = 0; i < total_size; i++) {
        data[i] = (uint8_t)(i & 0xFF);
    }
    
    printf("增量更新测试 - 总大小: %zu 字节, 块大小: %zu 字节\n", 
           total_size, chunk_size);
    
    start_time = get_time();
    
    sm3_init(&ctx);
    while (processed < total_size) {
        size_t current_chunk = (total_size - processed) < chunk_size ? 
                              (total_size - processed) : chunk_size;
        sm3_update(&ctx, data + processed, current_chunk);
        processed += current_chunk;
    }
    sm3_final(&ctx, digest);
    
    end_time = get_time();
    
    throughput = total_size / ((end_time - start_time) * 1048576.0);
    
    printf("时间: %.3f 秒\n", end_time - start_time);
    printf("吞吐量: %.2f MB/s\n\n", throughput);
    
    free(data);
}

// 不同数据大小的对比测试
static void benchmark_sizes() {
    size_t sizes[] = {64, 256, 1024, 4096, 16384, 65536, 262144, 1048576};
    int iterations[] = {100000, 50000, 10000, 2000, 500, 100, 20, 5};
    int num_sizes = sizeof(sizes) / sizeof(sizes[0]);
    int i;
    
    printf("=== 不同数据大小性能对比 ===\n");
    for (i = 0; i < num_sizes; i++) {
        benchmark_sm3(sizes[i], iterations[i]);
    }
}

// 内存使用测试
static void test_memory_usage() {
    sm3_context_t ctx;
    printf("=== 内存使用情况 ===\n");
    printf("SM3上下文大小: %zu 字节\n", sizeof(sm3_context_t));
    printf("状态数组大小: %zu 字节\n", sizeof(ctx.state));
    printf("缓冲区大小: %zu 字节\n", sizeof(ctx.buffer));
    printf("总内存使用: %zu 字节\n\n", sizeof(sm3_context_t));
}

// 正确性验证
static void verify_correctness() {
    const char *test_data = "The quick brown fox jumps over the lazy dog";
    uint8_t digest1[SM3_DIGEST_SIZE];
    uint8_t digest2[SM3_DIGEST_SIZE];
    sm3_context_t ctx;
    char hex1[65], hex2[65];
    
    printf("=== 正确性验证 ===\n");
    
    // 一次性计算
    sm3_hash((uint8_t*)test_data, strlen(test_data), digest1);
    
    // 分块计算
    sm3_init(&ctx);
    sm3_update(&ctx, (uint8_t*)test_data, 10);
    sm3_update(&ctx, (uint8_t*)test_data + 10, 20);
    sm3_update(&ctx, (uint8_t*)test_data + 30, strlen(test_data) - 30);
    sm3_final(&ctx, digest2);
    
    sm3_digest_to_hex(digest1, hex1);
    sm3_digest_to_hex(digest2, hex2);
    
    printf("测试数据: \"%s\"\n", test_data);
    printf("一次性计算: %s\n", hex1);
    printf("分块计算:   %s\n", hex2);
    
    if (memcmp(digest1, digest2, SM3_DIGEST_SIZE) == 0) {
        printf("✓ 正确性验证通过\n\n");
    } else {
        printf("✗ 正确性验证失败\n\n");
    }
}

int main() {
    printf("=== SM3哈希算法性能测试 ===\n\n");
    
    // 内存使用信息
    test_memory_usage();
    
    // 正确性验证
    verify_correctness();
    
    // 不同数据大小的性能测试
    benchmark_sizes();
    
    // 增量更新性能测试
    printf("=== 增量更新性能测试 ===\n");
    benchmark_incremental(1048576, 1024);      // 1MB 数据，1KB 块
    benchmark_incremental(1048576, 4096);      // 1MB 数据，4KB 块
    benchmark_incremental(1048576, 65536);     // 1MB 数据，64KB 块
    
    // 长时间运行测试
    printf("=== 长时间运行测试 ===\n");
    benchmark_sm3(1048576, 100); // 100MB 总数据量
    
    return 0;
}
