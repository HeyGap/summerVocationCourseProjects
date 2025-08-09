#ifndef SM3_OPT_H
#define SM3_OPT_H

#include "sm3.h"
#include <immintrin.h>  // AVX2/SSE指令集

#ifdef __cplusplus
extern "C" {
#endif

// 检查CPU特性支持
typedef struct {
    int sse2_support;
    int avx2_support;
    int aes_support;
} cpu_features_t;

/**
 * 检测CPU支持的特性
 */
cpu_features_t sm3_detect_cpu_features(void);

/**
 * 优化的SM3实现选择器
 * 根据CPU特性自动选择最优实现
 */
typedef enum {
    SM3_IMPL_BASIC,     // 基础实现
    SM3_IMPL_SSE2,      // SSE2优化
    SM3_IMPL_AVX2,      // AVX2优化
    SM3_IMPL_AUTO       // 自动选择
} sm3_impl_type_t;

/**
 * 优化的SM3上下文，支持多种实现
 */
typedef struct {
    sm3_context_t base;
    sm3_impl_type_t impl_type;
    void (*process_block_func)(uint32_t state[8], const uint8_t block[64]);
} sm3_opt_context_t;

/**
 * 初始化优化的SM3上下文
 */
void sm3_opt_init(sm3_opt_context_t *ctx, sm3_impl_type_t impl_type);

/**
 * 优化的更新函数
 */
void sm3_opt_update(sm3_opt_context_t *ctx, const uint8_t *data, size_t len);

/**
 * 优化的完成函数
 */
void sm3_opt_final(sm3_opt_context_t *ctx, uint8_t *digest);

/**
 * 优化的一次性计算函数
 */
void sm3_opt_hash(const uint8_t *data, size_t len, uint8_t *digest, sm3_impl_type_t impl_type);

/* ========== 多流并行哈希 ========== */

/**
 * 4路并行SM3哈希计算（AVX2）
 * 同时处理4个独立的数据流
 */
void sm3_hash_4way_avx2(const uint8_t *data1, size_t len1,
                        const uint8_t *data2, size_t len2,
                        const uint8_t *data3, size_t len3,
                        const uint8_t *data4, size_t len4,
                        uint8_t *digest1, uint8_t *digest2,
                        uint8_t *digest3, uint8_t *digest4);

/**
 * 2路并行SM3哈希计算（SSE2）
 * 同时处理2个独立的数据流
 */
void sm3_hash_2way_sse2(const uint8_t *data1, size_t len1,
                        const uint8_t *data2, size_t len2,
                        uint8_t *digest1, uint8_t *digest2);

/* ========== 多块并行处理 ========== */

/**
 * 批量处理多个完整块（同一数据流）
 * 使用流水线和预取优化
 */
void sm3_process_blocks_batch(uint32_t state[8], const uint8_t *blocks, size_t num_blocks);

/**
 * AVX2优化的块处理
 */
void sm3_process_block_avx2(uint32_t state[8], const uint8_t block[64]);

/**
 * SSE2优化的块处理
 */
void sm3_process_block_sse2(uint32_t state[8], const uint8_t block[64]);

/* ========== 单块内并行优化 ========== */

/**
 * 消息扩展的AVX2优化版本
 */
void sm3_message_schedule_avx2(const uint8_t block[64], uint32_t W[68]);

/**
 * 压缩函数的部分并行优化
 */
void sm3_compress_rounds_opt(uint32_t state[8], const uint32_t W[68], const uint32_t W1[64]);

/* ========== 工具和基准测试函数 ========== */

/**
 * 性能基准测试
 */
typedef struct {
    double basic_time;
    double sse2_time;
    double avx2_time;
    double multiway_time;
} sm3_benchmark_result_t;

/**
 * 运行所有优化版本的基准测试
 */
sm3_benchmark_result_t sm3_run_benchmarks(const uint8_t *data, size_t len, int iterations);

/**
 * 验证所有优化实现的正确性
 */
int sm3_verify_optimizations(void);

/**
 * 内存对齐的数据缓冲区分配
 */
void* sm3_aligned_alloc(size_t size, size_t alignment);
void sm3_aligned_free(void* ptr);

/* ========== 高性能快速实现 ========== */

/**
 * 高效的SM3哈希计算（智能选择优化策略）
 * 对小数据使用基础实现避免SIMD开销，对大数据使用批量优化
 */
void sm3_fast_hash(const uint8_t *data, size_t len, uint8_t *digest);

/**
 * 真正高效的4路并行哈希计算
 */
void sm3_hash_4way_parallel(const uint8_t *data1, size_t len1,
                           const uint8_t *data2, size_t len2,
                           const uint8_t *data3, size_t len3,
                           const uint8_t *data4, size_t len4,
                           uint8_t *digest1, uint8_t *digest2,
                           uint8_t *digest3, uint8_t *digest4);

#ifdef __cplusplus
}
#endif

#endif // SM3_OPT_H
