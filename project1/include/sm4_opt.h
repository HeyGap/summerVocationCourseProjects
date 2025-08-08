#ifndef SM4_OPT_H
#define SM4_OPT_H

#include "sm4.h"
#include <immintrin.h>

#ifdef __cplusplus
extern "C" {
#endif

// CPU功能检测
typedef struct {
    int has_sse2;
    int has_ssse3;
    int has_aesni;
    int has_avx;
    int has_avx2;
} cpu_features;

/**
 * 检测CPU特性
 * @param features CPU特性结构体
 */
void detect_cpu_features(cpu_features *features);

// T-table优化版本

/**
 * T-table优化的SM4加密分组
 */
void sm4_crypt_block_ttable(const sm4_context *ctx, const uint8_t input[SM4_BLOCK_SIZE], 
                            uint8_t output[SM4_BLOCK_SIZE]);

/**
 * 初始化T-table查找表
 */
void sm4_ttable_init(void);

/**
 * T-table优化的SM4 ECB模式
 */
int sm4_crypt_ecb_ttable(const sm4_context *ctx, size_t length,
                         const uint8_t *input, uint8_t *output);

/**
 * T-table优化的SM4 CTR模式
 */
int sm4_crypt_ctr_ttable(const sm4_context *ctx, size_t length, size_t *nc_off,
                         uint8_t nonce_counter[SM4_BLOCK_SIZE], uint8_t stream_block[SM4_BLOCK_SIZE],
                         const uint8_t *input, uint8_t *output);

// AESNI优化版本

/**
 * AESNI优化的SM4加密分组
 */
void sm4_crypt_block_aesni(const sm4_context *ctx, const uint8_t input[SM4_BLOCK_SIZE], 
                           uint8_t output[SM4_BLOCK_SIZE]);

/**
 * AESNI优化的SM4 ECB模式(并行处理多个分组)
 */
int sm4_crypt_ecb_aesni(const sm4_context *ctx, size_t length,
                        const uint8_t *input, uint8_t *output);

// 并行CTR模式优化

/**
 * 并行CTR模式加密(AESNI版本)
 */
int sm4_crypt_ctr_aesni(const sm4_context *ctx, size_t length, size_t *nc_off,
                        uint8_t nonce_counter[SM4_BLOCK_SIZE], uint8_t stream_block[SM4_BLOCK_SIZE],
                        const uint8_t *input, uint8_t *output);

// 性能测试接口

/**
 * 基准测试结构
 */
typedef struct {
    const char *name;
    double cycles_per_byte;
    double mbps;
    double speedup;
} benchmark_result;

/**
 * 运行SM4性能测试
 * @param data_size 测试数据大小(字节)
 * @param results 测试结果数组
 * @param num_results 结果数组大小
 * @return 实际测试数量
 */
int sm4_benchmark(size_t data_size, benchmark_result *results, int num_results);

// 自动优化选择

/**
 * SM4优化上下文
 */
typedef struct {
    sm4_context base;
    cpu_features features;
    void (*crypt_block)(const sm4_context *ctx, const uint8_t *input, uint8_t *output);
    int (*crypt_ecb)(const sm4_context *ctx, size_t length, const uint8_t *input, uint8_t *output);
    int (*crypt_ctr)(const sm4_context *ctx, size_t length, size_t *nc_off,
                     uint8_t nonce_counter[SM4_BLOCK_SIZE], uint8_t stream_block[SM4_BLOCK_SIZE],
                     const uint8_t *input, uint8_t *output);
} sm4_opt_context;

/**
 * 初始化优化SM4上下文(自动选择最佳实现)
 */
int sm4_opt_init(sm4_opt_context *ctx, const uint8_t key[SM4_KEY_SIZE], int encrypt);

/**
 * 优化版本的分组加密
 */
static inline void sm4_opt_crypt_block(const sm4_opt_context *ctx, 
                                       const uint8_t input[SM4_BLOCK_SIZE], 
                                       uint8_t output[SM4_BLOCK_SIZE]) {
    ctx->crypt_block(&ctx->base, input, output);
}

/**
 * 优化版本的ECB模式
 */
static inline int sm4_opt_crypt_ecb(const sm4_opt_context *ctx, size_t length,
                                    const uint8_t *input, uint8_t *output) {
    return ctx->crypt_ecb(&ctx->base, length, input, output);
}

/**
 * 优化版本的CTR模式
 */
static inline int sm4_opt_crypt_ctr(const sm4_opt_context *ctx, size_t length, size_t *nc_off,
                                    uint8_t nonce_counter[SM4_BLOCK_SIZE], 
                                    uint8_t stream_block[SM4_BLOCK_SIZE],
                                    const uint8_t *input, uint8_t *output) {
    return ctx->crypt_ctr(&ctx->base, length, nc_off, nonce_counter, stream_block, input, output);
}

#ifdef __cplusplus
}
#endif

#endif /* SM4_OPT_H */
