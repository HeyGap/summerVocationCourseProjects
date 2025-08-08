#include "../include/sm4_opt.h"
#include "../include/utils.h"
#include <cpuid.h>
#include <string.h>

// CPU特性检测
void detect_cpu_features(cpu_features *features) {
    if (features == NULL) {
        return;
    }

    memset(features, 0, sizeof(*features));

#if defined(__x86_64__) || defined(__i386__)
    unsigned int eax, ebx, ecx, edx;

    // 检查CPUID是否支持
    if (__get_cpuid(1, &eax, &ebx, &ecx, &edx)) {
        // ECX寄存器中的特性位
        features->has_sse2 = (edx & (1 << 26)) != 0;
        features->has_ssse3 = (ecx & (1 << 9)) != 0;
        features->has_aesni = (ecx & (1 << 25)) != 0;
        features->has_avx = (ecx & (1 << 28)) != 0;
    }

    // 检查扩展特性
    if (__get_cpuid(7, &eax, &ebx, &ecx, &edx)) {
        // EBX寄存器中的特性位
        features->has_avx2 = (ebx & (1 << 5)) != 0;
    }
#endif

    // 在其他架构上，默认不支持这些特性
}

// 初始化优化SM4上下文
int sm4_opt_init(sm4_opt_context *ctx, const uint8_t key[SM4_KEY_SIZE], int encrypt) {
    if (ctx == NULL || key == NULL) {
        return -1;
    }

    // 检测CPU特性
    detect_cpu_features(&ctx->features);

    // 初始化基础SM4上下文
    if (sm4_init(&ctx->base, key, encrypt) != 0) {
        return -1;
    }

    // 根据CPU特性选择最佳实现
    if (ctx->features.has_aesni) {
        // 使用AESNI优化
        ctx->crypt_block = (void(*)(const sm4_context*, const uint8_t*, uint8_t*))sm4_crypt_block_aesni;
        ctx->crypt_ecb = sm4_crypt_ecb_aesni;
        ctx->crypt_ctr = sm4_crypt_ctr_aesni;
    } else {
        // 使用T-table优化
        sm4_ttable_init();
        ctx->crypt_block = (void(*)(const sm4_context*, const uint8_t*, uint8_t*))sm4_crypt_block_ttable;
        ctx->crypt_ecb = (int(*)(const sm4_context*, size_t, const uint8_t*, uint8_t*))sm4_crypt_ecb_ttable;
        ctx->crypt_ctr = (int(*)(const sm4_context*, size_t, size_t*, uint8_t*, uint8_t*, const uint8_t*, uint8_t*))sm4_crypt_ctr_ttable;
    }

    return 0;
}

// 性能基准测试
int sm4_benchmark(size_t data_size, benchmark_result *results, int num_results) {
    if (results == NULL || num_results < 4) {
        return -1;
    }

    uint8_t *test_data = malloc(data_size);
    uint8_t *output_data = malloc(data_size);
    uint8_t key[16];
    
    if (test_data == NULL || output_data == NULL) {
        free(test_data);
        free(output_data);
        return -1;
    }

    // 生成测试数据
    generate_random(test_data, data_size);
    generate_random_key(key);

    int result_count = 0;

    // 1. 基本实现测试
    {
        sm4_context ctx;
        sm4_init(&ctx, key, 1);

        timestamp_t start, end, diff;
        get_timestamp(&start);

        sm4_crypt_ecb(&ctx, data_size, test_data, output_data);

        get_timestamp(&end);
        calc_time_diff(&start, &end, &diff);

        results[result_count].name = "Basic Implementation";
        results[result_count].cycles_per_byte = (double)diff.cycles / data_size;
        results[result_count].mbps = (data_size / (1024.0 * 1024.0)) / diff.seconds;
        results[result_count].speedup = 1.0;
        result_count++;
    }

    // 2. T-table优化测试
    if (result_count < num_results) {
        sm4_context ctx;
        sm4_init(&ctx, key, 1);
        sm4_ttable_init();

        timestamp_t start, end, diff;
        get_timestamp(&start);

        sm4_crypt_ecb_ttable(&ctx, data_size, test_data, output_data);

        get_timestamp(&end);
        calc_time_diff(&start, &end, &diff);

        results[result_count].name = "T-table Optimization";
        results[result_count].cycles_per_byte = (double)diff.cycles / data_size;
        results[result_count].mbps = (data_size / (1024.0 * 1024.0)) / diff.seconds;
        results[result_count].speedup = results[0].mbps / results[result_count].mbps;
        result_count++;
    }

    // 3. AESNI优化测试
    if (result_count < num_results) {
        cpu_features features;
        detect_cpu_features(&features);

        if (features.has_aesni) {
            sm4_context ctx;
            sm4_init(&ctx, key, 1);

            timestamp_t start, end, diff;
            get_timestamp(&start);

            sm4_crypt_ecb_aesni(&ctx, data_size, test_data, output_data);

            get_timestamp(&end);
            calc_time_diff(&start, &end, &diff);

            results[result_count].name = "AESNI Optimization";
            results[result_count].cycles_per_byte = (double)diff.cycles / data_size;
            results[result_count].mbps = (data_size / (1024.0 * 1024.0)) / diff.seconds;
            results[result_count].speedup = results[result_count].mbps / results[0].mbps;
        } else {
            results[result_count].name = "AESNI Optimization (N/A)";
            results[result_count].cycles_per_byte = 0;
            results[result_count].mbps = 0;
            results[result_count].speedup = 0;
        }
        result_count++;
    }

    free(test_data);
    free(output_data);

    return result_count;
}

// T-table函数的前向声明实现
extern int sm4_crypt_ecb_ttable(const sm4_context *ctx, size_t length,
                                const uint8_t *input, uint8_t *output);
extern int sm4_crypt_ctr_ttable(const sm4_context *ctx, size_t length, size_t *nc_off,
                                uint8_t nonce_counter[SM4_BLOCK_SIZE], uint8_t stream_block[SM4_BLOCK_SIZE],
                                const uint8_t *input, uint8_t *output);

// 如果T-table函数未在其他文件中实现，提供回退实现
__attribute__((weak)) int sm4_crypt_ecb_ttable(const sm4_context *ctx, size_t length,
                                              const uint8_t *input, uint8_t *output) {
    return sm4_crypt_ecb(ctx, length, input, output);
}

__attribute__((weak)) int sm4_crypt_ctr_ttable(const sm4_context *ctx, size_t length, size_t *nc_off,
                                              uint8_t nonce_counter[SM4_BLOCK_SIZE], uint8_t stream_block[SM4_BLOCK_SIZE],
                                              const uint8_t *input, uint8_t *output) {
    return sm4_crypt_ctr(ctx, length, nc_off, nonce_counter, stream_block, input, output);
}
