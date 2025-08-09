#include "sm3_opt.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <immintrin.h>

#ifdef __x86_64__
#include <cpuid.h>
#endif

// 为不支持posix_memalign的系统提供替代实现
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200112L
#endif
#include <errno.h>

// ========== CPU特性检测 ==========

cpu_features_t sm3_detect_cpu_features(void) {
    cpu_features_t features = {0, 0, 0};
    
#ifdef __x86_64__
    unsigned int eax, ebx, ecx, edx;
    
    // 检查CPUID支持
    if (__get_cpuid(1, &eax, &ebx, &ecx, &edx)) {
        features.sse2_support = (edx & (1 << 26)) != 0;
        features.aes_support = (ecx & (1 << 25)) != 0;
    }
    
    // 检查AVX2支持
    if (__get_cpuid_count(7, 0, &eax, &ebx, &ecx, &edx)) {
        features.avx2_support = (ebx & (1 << 5)) != 0;
    }
#endif
    
    return features;
}

// ========== 基础优化工具函数 ==========

// 对齐内存分配
void* sm3_aligned_alloc(size_t size, size_t alignment) {
#ifdef _WIN32
    return _aligned_malloc(size, alignment);
#elif defined(__APPLE__) || defined(__FreeBSD__)
    void *ptr;
    if (posix_memalign(&ptr, alignment, size) != 0) {
        return NULL;
    }
    return ptr;
#else
    void *ptr;
    if (posix_memalign(&ptr, alignment, size) != 0) {
        return NULL;
    }
    return ptr;
#endif
}

void sm3_aligned_free(void* ptr) {
#ifdef _WIN32
    _aligned_free(ptr);
#else
    free(ptr);
#endif
}

// ========== AVX2优化的消息扩展 ==========

void sm3_message_schedule_avx2(const uint8_t block[64], uint32_t W[68]) {
#ifdef __AVX2__
    int j;
    
    // 前16个字直接从分组中获取（大端序转换）
    for (j = 0; j < 16; j++) {
        W[j] = __builtin_bswap32(((uint32_t*)block)[j]);
    }
    
    // 扩展到68个字 - 使用标量版本确保正确性
    for (j = 16; j < 68; j++) {
        uint32_t temp = W[j-16] ^ W[j-9] ^ ((W[j-3] << 15) | (W[j-3] >> 17));
        W[j] = (temp ^ ((temp << 15) | (temp >> 17)) ^ ((temp << 23) | (temp >> 9))) ^
               ((W[j-13] << 7) | (W[j-13] >> 25)) ^ W[j-6];
    }
#else
    // 回退到基础实现
    int j;
    for (j = 0; j < 16; j++) {
        W[j] = __builtin_bswap32(((uint32_t*)block)[j]);
    }
    for (j = 16; j < 68; j++) {
        uint32_t temp = W[j-16] ^ W[j-9] ^ ((W[j-3] << 15) | (W[j-3] >> 17));
        W[j] = (temp ^ ((temp << 15) | (temp >> 17)) ^ ((temp << 23) | (temp >> 9))) ^
               ((W[j-13] << 7) | (W[j-13] >> 25)) ^ W[j-6];
    }
#endif
}

// ========== AVX2优化的块处理 ==========

void sm3_process_block_avx2(uint32_t state[8], const uint8_t block[64]) {
    uint32_t W[68];
    uint32_t W1[64];
    uint32_t A, B, C, D, E, F, G, H;
    uint32_t SS1, SS2, TT1, TT2;
    int j;

    // 消息扩展 - 使用基础实现确保正确性
    for (j = 0; j < 16; j++) {
        W[j] = __builtin_bswap32(((uint32_t*)block)[j]);
    }
    for (j = 16; j < 68; j++) {
        uint32_t temp = W[j-16] ^ W[j-9] ^ ((W[j-3] << 15) | (W[j-3] >> 17));
        W[j] = (temp ^ ((temp << 15) | (temp >> 17)) ^ ((temp << 23) | (temp >> 9))) ^
               ((W[j-13] << 7) | (W[j-13] >> 25)) ^ W[j-6];
    }

    // 生成W1数组
    for (j = 0; j < 64; j++) {
        W1[j] = W[j] ^ W[j+4];
    }

    // 初始化工作变量
    A = state[0]; B = state[1]; C = state[2]; D = state[3];
    E = state[4]; F = state[5]; G = state[6]; H = state[7];

    // 64轮压缩 - 4轮循环展开优化
    for (j = 0; j < 64; j += 4) {
        // 第1轮
        {
            uint32_t T_val = (j < 16) ? 0x79CC4519 : 0x7A879D8A;
            uint32_t rotl_T = ((T_val << (j % 32)) | (T_val >> (32 - (j % 32))));
            SS1 = (((A << 12) | (A >> 20)) + E + rotl_T);
            SS1 = ((SS1 << 7) | (SS1 >> 25));
            SS2 = SS1 ^ ((A << 12) | (A >> 20));
            TT1 = ((j < 16) ? (A ^ B ^ C) : ((A & B) | (A & C) | (B & C))) + D + SS2 + W1[j];
            TT2 = ((j < 16) ? (E ^ F ^ G) : ((E & F) | (~E & G))) + H + SS1 + W[j];
            D = C; C = ((B << 9) | (B >> 23)); B = A; A = TT1;
            H = G; G = ((F << 19) | (F >> 13)); F = E;
            E = TT2 ^ ((TT2 << 9) | (TT2 >> 23)) ^ ((TT2 << 17) | (TT2 >> 15));
        }
        
        // 第2轮
        {
            uint32_t T_val = ((j+1) < 16) ? 0x79CC4519 : 0x7A879D8A;
            uint32_t rotl_T = ((T_val << ((j+1) % 32)) | (T_val >> (32 - ((j+1) % 32))));
            SS1 = (((A << 12) | (A >> 20)) + E + rotl_T);
            SS1 = ((SS1 << 7) | (SS1 >> 25));
            SS2 = SS1 ^ ((A << 12) | (A >> 20));
            TT1 = (((j+1) < 16) ? (A ^ B ^ C) : ((A & B) | (A & C) | (B & C))) + D + SS2 + W1[j+1];
            TT2 = (((j+1) < 16) ? (E ^ F ^ G) : ((E & F) | (~E & G))) + H + SS1 + W[j+1];
            D = C; C = ((B << 9) | (B >> 23)); B = A; A = TT1;
            H = G; G = ((F << 19) | (F >> 13)); F = E;
            E = TT2 ^ ((TT2 << 9) | (TT2 >> 23)) ^ ((TT2 << 17) | (TT2 >> 15));
        }
        
        // 第3轮
        {
            uint32_t T_val = ((j+2) < 16) ? 0x79CC4519 : 0x7A879D8A;
            uint32_t rotl_T = ((T_val << ((j+2) % 32)) | (T_val >> (32 - ((j+2) % 32))));
            SS1 = (((A << 12) | (A >> 20)) + E + rotl_T);
            SS1 = ((SS1 << 7) | (SS1 >> 25));
            SS2 = SS1 ^ ((A << 12) | (A >> 20));
            TT1 = (((j+2) < 16) ? (A ^ B ^ C) : ((A & B) | (A & C) | (B & C))) + D + SS2 + W1[j+2];
            TT2 = (((j+2) < 16) ? (E ^ F ^ G) : ((E & F) | (~E & G))) + H + SS1 + W[j+2];
            D = C; C = ((B << 9) | (B >> 23)); B = A; A = TT1;
            H = G; G = ((F << 19) | (F >> 13)); F = E;
            E = TT2 ^ ((TT2 << 9) | (TT2 >> 23)) ^ ((TT2 << 17) | (TT2 >> 15));
        }
        
        // 第4轮
        {
            uint32_t T_val = ((j+3) < 16) ? 0x79CC4519 : 0x7A879D8A;
            uint32_t rotl_T = ((T_val << ((j+3) % 32)) | (T_val >> (32 - ((j+3) % 32))));
            SS1 = (((A << 12) | (A >> 20)) + E + rotl_T);
            SS1 = ((SS1 << 7) | (SS1 >> 25));
            SS2 = SS1 ^ ((A << 12) | (A >> 20));
            TT1 = (((j+3) < 16) ? (A ^ B ^ C) : ((A & B) | (A & C) | (B & C))) + D + SS2 + W1[j+3];
            TT2 = (((j+3) < 16) ? (E ^ F ^ G) : ((E & F) | (~E & G))) + H + SS1 + W[j+3];
            D = C; C = ((B << 9) | (B >> 23)); B = A; A = TT1;
            H = G; G = ((F << 19) | (F >> 13)); F = E;
            E = TT2 ^ ((TT2 << 9) | (TT2 >> 23)) ^ ((TT2 << 17) | (TT2 >> 15));
        }
    }

    // 更新状态
    state[0] ^= A; state[1] ^= B; state[2] ^= C; state[3] ^= D;
    state[4] ^= E; state[5] ^= F; state[6] ^= G; state[7] ^= H;
}

// ========== SSE2优化的块处理 ==========

void sm3_process_block_sse2(uint32_t state[8], const uint8_t block[64]) {
    // 暂时使用基础实现确保正确性
    sm3_process_block(state, block);
}

// ========== 批量块处理 ==========

void sm3_process_blocks_batch(uint32_t state[8], const uint8_t *blocks, size_t num_blocks) {
    size_t i;
    const uint8_t *current_block = blocks;
    
    // 使用预取优化
    for (i = 0; i < num_blocks; i++) {
        // 预取下一个块
        if (i + 1 < num_blocks) {
            __builtin_prefetch(current_block + 64, 0, 3);
        }
        
        // 根据CPU特性选择最优实现
        cpu_features_t features = sm3_detect_cpu_features();
        if (features.avx2_support) {
            sm3_process_block_avx2(state, current_block);
        } else if (features.sse2_support) {
            sm3_process_block_sse2(state, current_block);
        } else {
            sm3_process_block(state, current_block);
        }
        
        current_block += 64;
    }
}

// ========== 优化的SM3上下文实现 ==========

void sm3_opt_init(sm3_opt_context_t *ctx, sm3_impl_type_t impl_type) {
    sm3_init(&ctx->base);
    
    if (impl_type == SM3_IMPL_AUTO) {
        cpu_features_t features = sm3_detect_cpu_features();
        if (features.avx2_support) {
            ctx->impl_type = SM3_IMPL_AVX2;
            ctx->process_block_func = sm3_process_block_avx2;
        } else if (features.sse2_support) {
            ctx->impl_type = SM3_IMPL_SSE2;
            ctx->process_block_func = sm3_process_block_sse2;
        } else {
            ctx->impl_type = SM3_IMPL_BASIC;
            ctx->process_block_func = sm3_process_block;
        }
    } else {
        ctx->impl_type = impl_type;
        switch (impl_type) {
            case SM3_IMPL_AVX2:
                ctx->process_block_func = sm3_process_block_avx2;
                break;
            case SM3_IMPL_SSE2:
                ctx->process_block_func = sm3_process_block_sse2;
                break;
            default:
                ctx->process_block_func = sm3_process_block;
                break;
        }
    }
}

void sm3_opt_update(sm3_opt_context_t *ctx, const uint8_t *data, size_t len) {
    if (len == 0) return;

    ctx->base.count += len;

    // 处理缓冲区中的数据
    if (ctx->base.buffer_len > 0) {
        size_t need = SM3_BLOCK_SIZE - ctx->base.buffer_len;
        size_t copy = (len < need) ? len : need;
        
        memcpy(ctx->base.buffer + ctx->base.buffer_len, data, copy);
        ctx->base.buffer_len += copy;
        data += copy;
        len -= copy;

        if (ctx->base.buffer_len == SM3_BLOCK_SIZE) {
            ctx->process_block_func(ctx->base.state, ctx->base.buffer);
            ctx->base.buffer_len = 0;
        }
    }

    // 批量处理完整的块
    if (len >= SM3_BLOCK_SIZE) {
        size_t num_blocks = len / SM3_BLOCK_SIZE;
        size_t batch_size = num_blocks * SM3_BLOCK_SIZE;
        
        // 对多个块使用批量处理
        sm3_process_blocks_batch(ctx->base.state, data, num_blocks);
        
        data += batch_size;
        len -= batch_size;
    }

    // 保存剩余数据
    if (len > 0) {
        memcpy(ctx->base.buffer + ctx->base.buffer_len, data, len);
        ctx->base.buffer_len += len;
    }
}

void sm3_opt_final(sm3_opt_context_t *ctx, uint8_t *digest) {
    sm3_final(&ctx->base, digest);
}

void sm3_opt_hash(const uint8_t *data, size_t len, uint8_t *digest, sm3_impl_type_t impl_type) {
    sm3_opt_context_t ctx;
    sm3_opt_init(&ctx, impl_type);
    sm3_opt_update(&ctx, data, len);
    sm3_opt_final(&ctx, digest);
}
