#include "sm3.h"
#include <string.h>
#include <stdio.h>

// SM3常量和初始值
#define SM3_T1 0x79CC4519
#define SM3_T2 0x7A879D8A

// SM3初始哈希值
static const uint32_t SM3_IV[SM3_DIGEST_WORDS] = {
    0x7380166F, 0x4914B2B9, 0x172442D7, 0xDA8A0600,
    0xA96F30BC, 0x163138AA, 0xE38DEE4D, 0xB0FB0E4E
};

// 辅助函数：32位左循环移位
static inline uint32_t ROTL(uint32_t x, int n) {
    return (x << n) | (x >> (32 - n));
}

// 辅助函数：大端序转换
static inline uint32_t BE32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | 
           ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static inline void STORE_BE32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v >> 24);
    p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >> 8);
    p[3] = (uint8_t)v;
}

// 布尔函数FF
static inline uint32_t FF(uint32_t x, uint32_t y, uint32_t z, int j) {
    if (j < 16) {
        return x ^ y ^ z;
    } else {
        return (x & y) | (x & z) | (y & z);
    }
}

// 布尔函数GG
static inline uint32_t GG(uint32_t x, uint32_t y, uint32_t z, int j) {
    if (j < 16) {
        return x ^ y ^ z;
    } else {
        return (x & y) | (~x & z);
    }
}

// 置换函数P0
static inline uint32_t P0(uint32_t x) {
    return x ^ ROTL(x, 9) ^ ROTL(x, 17);
}

// 置换函数P1
static inline uint32_t P1(uint32_t x) {
    return x ^ ROTL(x, 15) ^ ROTL(x, 23);
}

// 常量T
static inline uint32_t T(int j) {
    if (j < 16) {
        return SM3_T1;
    } else {
        return SM3_T2;
    }
}

/**
 * 处理单个512位分组
 */
void sm3_process_block(uint32_t state[SM3_DIGEST_WORDS], const uint8_t block[SM3_BLOCK_SIZE]) {
    uint32_t W[68];
    uint32_t W1[64];
    uint32_t A, B, C, D, E, F, G, H;
    uint32_t SS1, SS2, TT1, TT2;
    int j;

    // 消息扩展
    // 前16个字直接从分组中获取
    for (j = 0; j < 16; j++) {
        W[j] = BE32(block + j * 4);
    }

    // 扩展到68个字
    for (j = 16; j < 68; j++) {
        W[j] = P1(W[j-16] ^ W[j-9] ^ ROTL(W[j-3], 15)) ^ ROTL(W[j-13], 7) ^ W[j-6];
    }

    // 生成W1
    for (j = 0; j < 64; j++) {
        W1[j] = W[j] ^ W[j+4];
    }

    // 初始化工作变量
    A = state[0];
    B = state[1];
    C = state[2];
    D = state[3];
    E = state[4];
    F = state[5];
    G = state[6];
    H = state[7];

    // 64轮压缩
    for (j = 0; j < 64; j++) {
        SS1 = ROTL(ROTL(A, 12) + E + ROTL(T(j), j % 32), 7);
        SS2 = SS1 ^ ROTL(A, 12);
        TT1 = FF(A, B, C, j) + D + SS2 + W1[j];
        TT2 = GG(E, F, G, j) + H + SS1 + W[j];
        D = C;
        C = ROTL(B, 9);
        B = A;
        A = TT1;
        H = G;
        G = ROTL(F, 19);
        F = E;
        E = P0(TT2);

        A &= 0xFFFFFFFF;
        B &= 0xFFFFFFFF;
        C &= 0xFFFFFFFF;
        D &= 0xFFFFFFFF;
        E &= 0xFFFFFFFF;
        F &= 0xFFFFFFFF;
        G &= 0xFFFFFFFF;
        H &= 0xFFFFFFFF;
    }

    // 更新状态
    state[0] ^= A;
    state[1] ^= B;
    state[2] ^= C;
    state[3] ^= D;
    state[4] ^= E;
    state[5] ^= F;
    state[6] ^= G;
    state[7] ^= H;
}

/**
 * 初始化SM3上下文
 */
void sm3_init(sm3_context_t *ctx) {
    memcpy(ctx->state, SM3_IV, sizeof(SM3_IV));
    ctx->count = 0;
    ctx->buffer_len = 0;
    memset(ctx->buffer, 0, sizeof(ctx->buffer));
}

/**
 * 更新SM3计算
 */
void sm3_update(sm3_context_t *ctx, const uint8_t *data, size_t len) {
    if (len == 0) return;

    ctx->count += len;

    // 如果缓冲区中有数据，先尝试填满缓冲区
    if (ctx->buffer_len > 0) {
        size_t need = SM3_BLOCK_SIZE - ctx->buffer_len;
        size_t copy = (len < need) ? len : need;
        
        memcpy(ctx->buffer + ctx->buffer_len, data, copy);
        ctx->buffer_len += copy;
        data += copy;
        len -= copy;

        // 如果缓冲区满了，处理这个分组
        if (ctx->buffer_len == SM3_BLOCK_SIZE) {
            sm3_process_block(ctx->state, ctx->buffer);
            ctx->buffer_len = 0;
        }
    }

    // 处理完整的分组
    while (len >= SM3_BLOCK_SIZE) {
        sm3_process_block(ctx->state, data);
        data += SM3_BLOCK_SIZE;
        len -= SM3_BLOCK_SIZE;
    }

    // 保存剩余的数据到缓冲区
    if (len > 0) {
        memcpy(ctx->buffer + ctx->buffer_len, data, len);
        ctx->buffer_len += len;
    }
}

/**
 * 完成SM3计算
 */
void sm3_final(sm3_context_t *ctx, uint8_t *digest) {
    uint8_t padding[SM3_BLOCK_SIZE * 2];
    size_t padding_len;
    uint64_t bit_count = ctx->count * 8;
    int i;

    // 添加填充：先加一个1位（0x80字节）
    padding[0] = 0x80;
    padding_len = 1;

    // 计算需要多少个0位
    size_t total_len = ctx->buffer_len + padding_len;
    if (total_len <= 56) {
        // 当前分组还能容纳长度字段
        padding_len = 56 - ctx->buffer_len;
    } else {
        // 需要额外一个分组
        padding_len = 64 + 56 - ctx->buffer_len;
    }

    // 填充0
    memset(padding + 1, 0, padding_len - 1);

    // 添加64位长度（大端序）
    STORE_BE32(padding + padding_len, (uint32_t)(bit_count >> 32));
    STORE_BE32(padding + padding_len + 4, (uint32_t)bit_count);
    padding_len += 8;

    // 处理填充数据
    sm3_update(ctx, padding, padding_len);

    // 输出最终哈希值
    for (i = 0; i < SM3_DIGEST_WORDS; i++) {
        STORE_BE32(digest + i * 4, ctx->state[i]);
    }
}

/**
 * 一次性计算SM3哈希值
 */
void sm3_hash(const uint8_t *data, size_t len, uint8_t *digest) {
    sm3_context_t ctx;
    sm3_init(&ctx);
    sm3_update(&ctx, data, len);
    sm3_final(&ctx, digest);
}

/**
 * 将哈希值转换为十六进制字符串
 */
void sm3_digest_to_hex(const uint8_t *digest, char *hex_str) {
    int i;
    for (i = 0; i < SM3_DIGEST_SIZE; i++) {
        sprintf(hex_str + i * 2, "%02x", digest[i]);
    }
    hex_str[SM3_DIGEST_SIZE * 2] = '\0';
}

/**
 * 打印哈希值的十六进制表示
 */
void sm3_print_digest(const uint8_t *digest) {
    int i;
    for (i = 0; i < SM3_DIGEST_SIZE; i++) {
        printf("%02x", digest[i]);
    }
    printf("\n");
}
