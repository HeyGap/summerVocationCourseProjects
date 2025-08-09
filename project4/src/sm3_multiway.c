#include "sm3_opt.h"
#include <string.h>
#include <immintrin.h>

// ========== 4路并行哈希实现 (AVX2) ==========

#ifdef __AVX2__

// AVX2 4路并行状态结构
typedef struct {
    __m256i state[8];  // 8个状态寄存器，每个包含4个32位值
} sm3_4way_context_t;

// 4路并行的常量
static const uint32_t SM3_IV_4WAY[8][4] __attribute__((aligned(32))) = {
    {0x7380166F, 0x7380166F, 0x7380166F, 0x7380166F},
    {0x4914B2B9, 0x4914B2B9, 0x4914B2B9, 0x4914B2B9},
    {0x172442D7, 0x172442D7, 0x172442D7, 0x172442D7},
    {0xDA8A0600, 0xDA8A0600, 0xDA8A0600, 0xDA8A0600},
    {0xA96F30BC, 0xA96F30BC, 0xA96F30BC, 0xA96F30BC},
    {0x163138AA, 0x163138AA, 0x163138AA, 0x163138AA},
    {0xE38DEE4D, 0xE38DEE4D, 0xE38DEE4D, 0xE38DEE4D},
    {0xB0FB0E4E, 0xB0FB0E4E, 0xB0FB0E4E, 0xB0FB0E4E}
};

// 4路并行大端序转换
static inline __m256i load_be32_4way(const uint8_t *p1, const uint8_t *p2, 
                                      const uint8_t *p3, const uint8_t *p4, int offset) {
    uint32_t v1 = __builtin_bswap32(*(uint32_t*)(p1 + offset));
    uint32_t v2 = __builtin_bswap32(*(uint32_t*)(p2 + offset));
    uint32_t v3 = __builtin_bswap32(*(uint32_t*)(p3 + offset));
    uint32_t v4 = __builtin_bswap32(*(uint32_t*)(p4 + offset));
    return _mm256_set_epi32(v4, v3, v2, v1, v4, v3, v2, v1);
}

// AVX2 左旋转
static inline __m256i rotl32_avx2(__m256i x, int n) {
    return _mm256_or_si256(_mm256_slli_epi32(x, n), _mm256_srli_epi32(x, 32 - n));
}

// 4路并行FF函数
static inline __m256i FF_4way(__m256i x, __m256i y, __m256i z, int j) {
    if (j < 16) {
        return _mm256_xor_si256(_mm256_xor_si256(x, y), z);
    } else {
        return _mm256_or_si256(_mm256_or_si256(_mm256_and_si256(x, y), 
                               _mm256_and_si256(x, z)), _mm256_and_si256(y, z));
    }
}

// 4路并行GG函数
static inline __m256i GG_4way(__m256i x, __m256i y, __m256i z, int j) {
    if (j < 16) {
        return _mm256_xor_si256(_mm256_xor_si256(x, y), z);
    } else {
        return _mm256_or_si256(_mm256_and_si256(x, y), 
                               _mm256_and_si256(_mm256_xor_si256(x, _mm256_set1_epi32(0xFFFFFFFF)), z));
    }
}

// 4路并行P0函数
static inline __m256i P0_4way(__m256i x) {
    return _mm256_xor_si256(_mm256_xor_si256(x, rotl32_avx2(x, 9)), rotl32_avx2(x, 17));
}

// 4路并行块处理
static void sm3_process_block_4way(sm3_4way_context_t *ctx, 
                                   const uint8_t *block1, const uint8_t *block2, 
                                   const uint8_t *block3, const uint8_t *block4) {
    __m256i W[68];
    __m256i W1[64];
    __m256i A, B, C, D, E, F, G, H;
    __m256i SS1, SS2, TT1, TT2;
    __m256i T1 = _mm256_set1_epi32(0x79CC4519);
    __m256i T2 = _mm256_set1_epi32(0x7A879D8A);
    int j;

    // 4路并行消息扩展
    for (j = 0; j < 16; j++) {
        W[j] = load_be32_4way(block1, block2, block3, block4, j * 4);
    }

    for (j = 16; j < 68; j++) {
        __m256i temp1 = _mm256_xor_si256(_mm256_xor_si256(W[j-16], W[j-9]), 
                                         rotl32_avx2(W[j-3], 15));
        __m256i temp2 = _mm256_xor_si256(_mm256_xor_si256(temp1, rotl32_avx2(temp1, 15)), 
                                         rotl32_avx2(temp1, 23));
        W[j] = _mm256_xor_si256(_mm256_xor_si256(temp2, rotl32_avx2(W[j-13], 7)), W[j-6]);
    }

    // 生成W1
    for (j = 0; j < 64; j++) {
        W1[j] = _mm256_xor_si256(W[j], W[j+4]);
    }

    // 初始化工作变量
    A = ctx->state[0]; B = ctx->state[1]; C = ctx->state[2]; D = ctx->state[3];
    E = ctx->state[4]; F = ctx->state[5]; G = ctx->state[6]; H = ctx->state[7];

    // 64轮压缩
    for (j = 0; j < 64; j++) {
        __m256i T_val = (j < 16) ? T1 : T2;
        __m256i rotl_A = rotl32_avx2(A, 12);
        __m256i temp_sum = _mm256_add_epi32(_mm256_add_epi32(rotl_A, E), 
                                            rotl32_avx2(T_val, j % 32));
        SS1 = rotl32_avx2(temp_sum, 7);
        SS2 = _mm256_xor_si256(SS1, rotl_A);
        
        TT1 = _mm256_add_epi32(_mm256_add_epi32(FF_4way(A, B, C, j), D), 
                               _mm256_add_epi32(SS2, W1[j]));
        TT2 = _mm256_add_epi32(_mm256_add_epi32(GG_4way(E, F, G, j), H), 
                               _mm256_add_epi32(SS1, W[j]));

        D = C;
        C = rotl32_avx2(B, 9);
        B = A;
        A = TT1;
        H = G;
        G = rotl32_avx2(F, 19);
        F = E;
        E = P0_4way(TT2);
    }

    // 更新状态
    ctx->state[0] = _mm256_xor_si256(ctx->state[0], A);
    ctx->state[1] = _mm256_xor_si256(ctx->state[1], B);
    ctx->state[2] = _mm256_xor_si256(ctx->state[2], C);
    ctx->state[3] = _mm256_xor_si256(ctx->state[3], D);
    ctx->state[4] = _mm256_xor_si256(ctx->state[4], E);
    ctx->state[5] = _mm256_xor_si256(ctx->state[5], F);
    ctx->state[6] = _mm256_xor_si256(ctx->state[6], G);
    ctx->state[7] = _mm256_xor_si256(ctx->state[7], H);
}

void sm3_hash_4way_avx2(const uint8_t *data1, size_t len1,
                        const uint8_t *data2, size_t len2,
                        const uint8_t *data3, size_t len3,
                        const uint8_t *data4, size_t len4,
                        uint8_t *digest1, uint8_t *digest2,
                        uint8_t *digest3, uint8_t *digest4) {
    
    sm3_4way_context_t ctx;
    uint8_t *aligned_data1, *aligned_data2, *aligned_data3, *aligned_data4;
    size_t padded_len1, padded_len2, padded_len3, padded_len4;
    size_t max_len, i;
    
    // 初始化4路上下文
    for (i = 0; i < 8; i++) {
        ctx.state[i] = _mm256_load_si256((__m256i*)SM3_IV_4WAY[i]);
    }
    
    // 计算填充后的长度
    padded_len1 = len1 + 1 + ((56 - (len1 + 1) % 64) % 64) + 8;
    padded_len2 = len2 + 1 + ((56 - (len2 + 1) % 64) % 64) + 8;
    padded_len3 = len3 + 1 + ((56 - (len3 + 1) % 64) % 64) + 8;
    padded_len4 = len4 + 1 + ((56 - (len4 + 1) % 64) % 64) + 8;
    
    max_len = padded_len1;
    if (padded_len2 > max_len) max_len = padded_len2;
    if (padded_len3 > max_len) max_len = padded_len3;
    if (padded_len4 > max_len) max_len = padded_len4;
    
    // 分配对齐的缓冲区并进行填充
    aligned_data1 = sm3_aligned_alloc(max_len, 32);
    aligned_data2 = sm3_aligned_alloc(max_len, 32);
    aligned_data3 = sm3_aligned_alloc(max_len, 32);
    aligned_data4 = sm3_aligned_alloc(max_len, 32);
    
    if (!aligned_data1 || !aligned_data2 || !aligned_data3 || !aligned_data4) {
        goto cleanup;
    }
    
    // 填充数据流1
    memcpy(aligned_data1, data1, len1);
    aligned_data1[len1] = 0x80;
    memset(aligned_data1 + len1 + 1, 0, padded_len1 - len1 - 9);
    *(uint64_t*)(aligned_data1 + padded_len1 - 8) = __builtin_bswap64(len1 * 8);
    memset(aligned_data1 + padded_len1, 0, max_len - padded_len1);
    
    // 填充数据流2
    memcpy(aligned_data2, data2, len2);
    aligned_data2[len2] = 0x80;
    memset(aligned_data2 + len2 + 1, 0, padded_len2 - len2 - 9);
    *(uint64_t*)(aligned_data2 + padded_len2 - 8) = __builtin_bswap64(len2 * 8);
    memset(aligned_data2 + padded_len2, 0, max_len - padded_len2);
    
    // 填充数据流3
    memcpy(aligned_data3, data3, len3);
    aligned_data3[len3] = 0x80;
    memset(aligned_data3 + len3 + 1, 0, padded_len3 - len3 - 9);
    *(uint64_t*)(aligned_data3 + padded_len3 - 8) = __builtin_bswap64(len3 * 8);
    memset(aligned_data3 + padded_len3, 0, max_len - padded_len3);
    
    // 填充数据流4
    memcpy(aligned_data4, data4, len4);
    aligned_data4[len4] = 0x80;
    memset(aligned_data4 + len4 + 1, 0, padded_len4 - len4 - 9);
    *(uint64_t*)(aligned_data4 + padded_len4 - 8) = __builtin_bswap64(len4 * 8);
    memset(aligned_data4 + padded_len4, 0, max_len - padded_len4);
    
    // 4路并行处理所有块
    for (i = 0; i < max_len; i += 64) {
        sm3_process_block_4way(&ctx, aligned_data1 + i, aligned_data2 + i, 
                               aligned_data3 + i, aligned_data4 + i);
    }
    
    // 提取最终结果
    uint32_t results[8][4] __attribute__((aligned(32)));
    for (i = 0; i < 8; i++) {
        _mm256_store_si256((__m256i*)results[i], ctx.state[i]);
    }
    
    // 输出最终哈希值
    for (i = 0; i < 8; i++) {
        *(uint32_t*)(digest1 + i * 4) = __builtin_bswap32(results[i][0]);
        *(uint32_t*)(digest2 + i * 4) = __builtin_bswap32(results[i][1]);
        *(uint32_t*)(digest3 + i * 4) = __builtin_bswap32(results[i][2]);
        *(uint32_t*)(digest4 + i * 4) = __builtin_bswap32(results[i][3]);
    }
    
cleanup:
    if (aligned_data1) sm3_aligned_free(aligned_data1);
    if (aligned_data2) sm3_aligned_free(aligned_data2);
    if (aligned_data3) sm3_aligned_free(aligned_data3);
    if (aligned_data4) sm3_aligned_free(aligned_data4);
}

#else

// AVX2不支持时的回退实现
void sm3_hash_4way_avx2(const uint8_t *data1, size_t len1,
                        const uint8_t *data2, size_t len2,
                        const uint8_t *data3, size_t len3,
                        const uint8_t *data4, size_t len4,
                        uint8_t *digest1, uint8_t *digest2,
                        uint8_t *digest3, uint8_t *digest4) {
    // 回退到串行计算
    sm3_hash(data1, len1, digest1);
    sm3_hash(data2, len2, digest2);
    sm3_hash(data3, len3, digest3);
    sm3_hash(data4, len4, digest4);
}

#endif

// ========== 2路并行哈希实现 (SSE2) ==========

#ifdef __SSE2__

// SSE2 2路并行状态结构
typedef struct {
    __m128i state[8];  // 8个状态寄存器，每个包含2个32位值
} sm3_2way_context_t;

// 2路并行的常量
static const uint32_t SM3_IV_2WAY[8][2] __attribute__((aligned(16))) = {
    {0x7380166F, 0x7380166F}, {0x4914B2B9, 0x4914B2B9},
    {0x172442D7, 0x172442D7}, {0xDA8A0600, 0xDA8A0600},
    {0xA96F30BC, 0xA96F30BC}, {0x163138AA, 0x163138AA},
    {0xE38DEE4D, 0xE38DEE4D}, {0xB0FB0E4E, 0xB0FB0E4E}
};

// SSE2 左旋转
static inline __m128i rotl32_sse2(__m128i x, int n) {
    return _mm_or_si128(_mm_slli_epi32(x, n), _mm_srli_epi32(x, 32 - n));
}

// 2路并行处理函数（简化版）
void sm3_hash_2way_sse2(const uint8_t *data1, size_t len1,
                        const uint8_t *data2, size_t len2,
                        uint8_t *digest1, uint8_t *digest2) {
    // 为了简化，这里使用串行实现
    // 实际应用中应该实现完整的2路并行版本
    sm3_hash(data1, len1, digest1);
    sm3_hash(data2, len2, digest2);
}

#else

void sm3_hash_2way_sse2(const uint8_t *data1, size_t len1,
                        const uint8_t *data2, size_t len2,
                        uint8_t *digest1, uint8_t *digest2) {
    sm3_hash(data1, len1, digest1);
    sm3_hash(data2, len2, digest2);
}

#endif
