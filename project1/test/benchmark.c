#include "../include/sm4_opt.h"
#include "../include/utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// 基准测试配置
#define BENCHMARK_DATA_SIZE (1024 * 1024)  // 1MB
#define BENCHMARK_ITERATIONS 10
#define WARMUP_ITERATIONS 3

// 基准测试结果结构
typedef struct {
    const char *name;
    double avg_cycles_per_byte;
    double avg_mbps;
    double best_mbps;
    double worst_mbps;
    double speedup_vs_basic;
} detailed_benchmark_result;

// 运行单个实现的基准测试
static void benchmark_implementation(const char *name,
                                   int (*crypt_func)(const sm4_context*, size_t, const uint8_t*, uint8_t*),
                                   const sm4_context *ctx,
                                   const uint8_t *input_data,
                                   uint8_t *output_data,
                                   size_t data_size,
                                   detailed_benchmark_result *result) {
    double total_cycles = 0;
    double total_time = 0;
    double best_time = 1e9;
    double worst_time = 0;
    
    printf("  Benchmarking %s...\n", name);
    
    // 预热
    for (int i = 0; i < WARMUP_ITERATIONS; i++) {
        crypt_func(ctx, data_size, input_data, output_data);
    }
    
    // 实际测试
    for (int i = 0; i < BENCHMARK_ITERATIONS; i++) {
        timestamp_t start, end, diff;
        get_timestamp(&start);
        
        crypt_func(ctx, data_size, input_data, output_data);
        
        get_timestamp(&end);
        calc_time_diff(&start, &end, &diff);
        
        total_cycles += diff.cycles;
        total_time += diff.seconds;
        
        if (diff.seconds < best_time) best_time = diff.seconds;
        if (diff.seconds > worst_time) worst_time = diff.seconds;
        
        printf("    Iteration %d: %.2f MB/s\n", i + 1, 
               (data_size / (1024.0 * 1024.0)) / diff.seconds);
    }
    
    // 计算统计数据
    result->name = name;
    result->avg_cycles_per_byte = total_cycles / (data_size * BENCHMARK_ITERATIONS);
    result->avg_mbps = (data_size / (1024.0 * 1024.0)) / (total_time / BENCHMARK_ITERATIONS);
    result->best_mbps = (data_size / (1024.0 * 1024.0)) / best_time;
    result->worst_mbps = (data_size / (1024.0 * 1024.0)) / worst_time;
}

// SM4 ECB模式基准测试
static void benchmark_sm4_ecb(void) {
    printf("=== SM4 ECB Mode Benchmark ===\n");
    
    uint8_t key[16];
    generate_random_key(key);
    
    uint8_t *input_data = malloc(BENCHMARK_DATA_SIZE);
    uint8_t *output_data = malloc(BENCHMARK_DATA_SIZE);
    
    if (input_data == NULL || output_data == NULL) {
        printf("Failed to allocate benchmark data\n");
        free(input_data);
        free(output_data);
        return;
    }
    
    generate_random(input_data, BENCHMARK_DATA_SIZE);
    
    detailed_benchmark_result results[4];
    int result_count = 0;
    
    // 1. 基本实现
    {
        sm4_context ctx;
        sm4_init(&ctx, key, 1);
        benchmark_implementation("Basic Implementation", 
                               sm4_crypt_ecb, &ctx,
                               input_data, output_data, BENCHMARK_DATA_SIZE,
                               &results[result_count++]);
    }
    
    // 2. T-table优化
    {
        sm4_context ctx;
        sm4_init(&ctx, key, 1);
        sm4_ttable_init();
        benchmark_implementation("T-table Optimization", 
                               (int(*)(const sm4_context*, size_t, const uint8_t*, uint8_t*))sm4_crypt_ecb_ttable,
                               &ctx, input_data, output_data, BENCHMARK_DATA_SIZE,
                               &results[result_count++]);
    }
    
    // 3. AESNI优化（如果支持）
    {
        cpu_features features;
        detect_cpu_features(&features);
        
        if (features.has_aesni) {
            sm4_context ctx;
            sm4_init(&ctx, key, 1);
            benchmark_implementation("AESNI Optimization",
                                   sm4_crypt_ecb_aesni, &ctx,
                                   input_data, output_data, BENCHMARK_DATA_SIZE,
                                   &results[result_count++]);
        } else {
            printf("  AESNI not supported, skipping\n");
        }
    }
    
    // 计算相对加速比
    double baseline_mbps = results[0].avg_mbps;
    for (int i = 0; i < result_count; i++) {
        results[i].speedup_vs_basic = results[i].avg_mbps / baseline_mbps;
    }
    
    // 打印结果表格
    printf("\n=== ECB Benchmark Results ===\n");
    printf("%-25s %12s %12s %12s %12s %10s\n", 
           "Implementation", "Avg MB/s", "Best MB/s", "Worst MB/s", "Cycles/Byte", "Speedup");
    printf("--------------------------------------------------------------------------------\n");
    
    for (int i = 0; i < result_count; i++) {
        printf("%-25s %12.2f %12.2f %12.2f %12.2f %10.2fx\n",
               results[i].name,
               results[i].avg_mbps,
               results[i].best_mbps,
               results[i].worst_mbps,
               results[i].avg_cycles_per_byte,
               results[i].speedup_vs_basic);
    }
    printf("\n");
    
    free(input_data);
    free(output_data);
}

// SM4 CTR模式基准测试
static void benchmark_sm4_ctr(void) {
    printf("=== SM4 CTR Mode Benchmark ===\n");
    
    uint8_t key[16];
    generate_random_key(key);
    
    uint8_t nonce_counter[16] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0a, 0x0b, 0x00, 0x00, 0x00, 0x01
    };
    
    uint8_t *input_data = malloc(BENCHMARK_DATA_SIZE);
    uint8_t *output_data = malloc(BENCHMARK_DATA_SIZE);
    
    if (input_data == NULL || output_data == NULL) {
        printf("Failed to allocate benchmark data\n");
        free(input_data);
        free(output_data);
        return;
    }
    
    generate_random(input_data, BENCHMARK_DATA_SIZE);
    
    sm4_context ctx;
    sm4_init(&ctx, key, 1);
    
    // 测试基本CTR实现
    {
        uint8_t nc[16], sb[16];
        memcpy(nc, nonce_counter, 16);
        size_t nc_off = 0;
        
        timestamp_t start, end, diff;
        get_timestamp(&start);
        
        for (int i = 0; i < BENCHMARK_ITERATIONS; i++) {
            memcpy(nc, nonce_counter, 16);
            nc_off = 0;
            sm4_crypt_ctr(&ctx, BENCHMARK_DATA_SIZE, &nc_off, nc, sb, input_data, output_data);
        }
        
        get_timestamp(&end);
        calc_time_diff(&start, &end, &diff);
        
        double avg_mbps = (BENCHMARK_DATA_SIZE * BENCHMARK_ITERATIONS / (1024.0 * 1024.0)) / diff.seconds;
        printf("  Basic CTR:     %.2f MB/s\n", avg_mbps);
    }
    
    // 测试优化CTR实现（如果有AESNI支持）
    {
        cpu_features features;
        detect_cpu_features(&features);
        
        if (features.has_aesni) {
            uint8_t nc[16], sb[16];
            memcpy(nc, nonce_counter, 16);
            size_t nc_off = 0;
            
            timestamp_t start, end, diff;
            get_timestamp(&start);
            
            for (int i = 0; i < BENCHMARK_ITERATIONS; i++) {
                memcpy(nc, nonce_counter, 16);
                nc_off = 0;
                sm4_crypt_ctr_aesni(&ctx, BENCHMARK_DATA_SIZE, &nc_off, nc, sb, input_data, output_data);
            }
            
            get_timestamp(&end);
            calc_time_diff(&start, &end, &diff);
            
            double avg_mbps = (BENCHMARK_DATA_SIZE * BENCHMARK_ITERATIONS / (1024.0 * 1024.0)) / diff.seconds;
            printf("  AESNI CTR:     %.2f MB/s\n", avg_mbps);
        }
    }
    
    printf("\n");
    free(input_data);
    free(output_data);
}

// 不同数据大小的性能测试
static void benchmark_different_sizes(void) {
    printf("=== Performance vs Data Size ===\n");
    
    uint8_t key[16];
    generate_random_key(key);
    
    sm4_context ctx;
    sm4_init(&ctx, key, 1);
    
    size_t sizes[] = {16, 64, 256, 1024, 4096, 16384, 65536, 262144}; // 16B to 256KB
    size_t num_sizes = sizeof(sizes) / sizeof(sizes[0]);
    
    printf("%-12s %-15s %-15s %-15s\n", "Size", "Basic (MB/s)", "T-table (MB/s)", "Speedup");
    printf("---------------------------------------------------------------\n");
    
    for (size_t i = 0; i < num_sizes; i++) {
        size_t size = sizes[i];
        uint8_t *input = malloc(size);
        uint8_t *output = malloc(size);
        
        if (input == NULL || output == NULL) {
            printf("Memory allocation failed for size %zu\n", size);
            free(input);
            free(output);
            continue;
        }
        
        generate_random(input, size);
        
        // 基本实现
        double basic_time = 0;
        for (int j = 0; j < 100; j++) {
            timestamp_t start, end, diff;
            get_timestamp(&start);
            sm4_crypt_ecb(&ctx, size, input, output);
            get_timestamp(&end);
            calc_time_diff(&start, &end, &diff);
            basic_time += diff.seconds;
        }
        double basic_mbps = (size * 100 / (1024.0 * 1024.0)) / basic_time;
        
        // T-table实现
        sm4_ttable_init();
        double ttable_time = 0;
        for (int j = 0; j < 100; j++) {
            timestamp_t start, end, diff;
            get_timestamp(&start);
            sm4_crypt_ecb_ttable(&ctx, size, input, output);
            get_timestamp(&end);
            calc_time_diff(&start, &end, &diff);
            ttable_time += diff.seconds;
        }
        double ttable_mbps = (size * 100 / (1024.0 * 1024.0)) / ttable_time;
        
        printf("%-12zu %-15.2f %-15.2f %-15.2fx\n", 
               size, basic_mbps, ttable_mbps, ttable_mbps / basic_mbps);
        
        free(input);
        free(output);
    }
    printf("\n");
}

int main(void) {
    printf("=== SM4 Performance Benchmark Suite ===\n\n");
    
    printf("Benchmark Configuration:\n");
    printf("  Data size: %d MB\n", BENCHMARK_DATA_SIZE / (1024 * 1024));
    printf("  Iterations: %d\n", BENCHMARK_ITERATIONS);
    printf("  Warmup iterations: %d\n", WARMUP_ITERATIONS);
    printf("\n");
    
    // 显示系统信息
    cpu_features features;
    detect_cpu_features(&features);
    
    printf("Detected CPU Features:\n");
    printf("  SSE2:        %s\n", features.has_sse2 ? "Yes" : "No");
    printf("  SSSE3:       %s\n", features.has_ssse3 ? "Yes" : "No");
    printf("  AES-NI:      %s\n", features.has_aesni ? "Yes" : "No");
    printf("  AVX:         %s\n", features.has_avx ? "Yes" : "No");
    printf("  AVX2:        %s\n", features.has_avx2 ? "Yes" : "No");
    printf("\n");
    
    // 运行基准测试
    benchmark_sm4_ecb();
    benchmark_sm4_ctr();
    benchmark_different_sizes();
    
    printf("=== Benchmark Complete ===\n");
    return 0;
}
