#include "../include/sm4.h"
#include "../include/sm4_opt.h"
#include <string.h>

// T-table查找表（预计算S盒和线性变换的组合）
static uint32_t sm4_ttable0[256];
static uint32_t sm4_ttable1[256];
static uint32_t sm4_ttable2[256];
static uint32_t sm4_ttable3[256];

// T-table初始化标志
static int ttable_initialized = 0;

// SM4 S盒（来自基本实现）
static const uint8_t sm4_sbox_table[256] = {
    0xd6, 0x90, 0xe9, 0xfe, 0xcc, 0xe1, 0x3d, 0xb7, 0x16, 0xb6, 0x14, 0xc2, 0x28, 0xfb, 0x2c, 0x05,
    0x2b, 0x67, 0x9a, 0x76, 0x2a, 0xbe, 0x04, 0xc3, 0xaa, 0x44, 0x13, 0x26, 0x49, 0x86, 0x06, 0x99,
    0x9c, 0x42, 0x50, 0xf4, 0x91, 0xef, 0x98, 0x7a, 0x33, 0x54, 0x0b, 0x43, 0xed, 0xcf, 0xac, 0x62,
    0xe4, 0xb3, 0x1c, 0xa9, 0xc9, 0x08, 0xe8, 0x95, 0x80, 0xdf, 0x94, 0xfa, 0x75, 0x8f, 0x3f, 0xa6,
    0x47, 0x07, 0xa7, 0xfc, 0xf3, 0x73, 0x17, 0xba, 0x83, 0x59, 0x3c, 0x19, 0xe6, 0x85, 0x4f, 0xa8,
    0x68, 0x6b, 0x81, 0xb2, 0x71, 0x64, 0xda, 0x8b, 0xf8, 0xeb, 0x0f, 0x4b, 0x70, 0x56, 0x9d, 0x35,
    0x1e, 0x24, 0x0e, 0x5e, 0x63, 0x58, 0xd1, 0xa2, 0x25, 0x22, 0x7c, 0x3b, 0x01, 0x21, 0x78, 0x87,
    0xd4, 0x00, 0x46, 0x57, 0x9f, 0xd3, 0x27, 0x52, 0x4c, 0x36, 0x02, 0xe7, 0xa0, 0xc4, 0xc8, 0x9e,
    0xea, 0xbf, 0x8a, 0xd2, 0x40, 0xc7, 0x38, 0xb5, 0xa3, 0xf7, 0xf2, 0xce, 0xf9, 0x61, 0x15, 0xa1,
    0xe0, 0xae, 0x5d, 0xa4, 0x9b, 0x34, 0x1a, 0x55, 0xad, 0x93, 0x32, 0x30, 0xf5, 0x8c, 0xb1, 0xe3,
    0x1d, 0xf6, 0xe2, 0x2e, 0x82, 0x66, 0xca, 0x60, 0xc0, 0x29, 0x23, 0xab, 0x0d, 0x53, 0x4e, 0x6f,
    0xd5, 0xdb, 0x37, 0x45, 0xde, 0xfd, 0x8e, 0x2f, 0x03, 0xff, 0x6a, 0x72, 0x6d, 0x6c, 0x5b, 0x51,
    0x8d, 0x1b, 0xaf, 0x92, 0xbb, 0xdd, 0xbc, 0x7f, 0x11, 0xd9, 0x5c, 0x41, 0x1f, 0x10, 0x5a, 0xd8,
    0x0a, 0xc1, 0x31, 0x88, 0xa5, 0xcd, 0x7b, 0xbd, 0x2d, 0x74, 0xd0, 0x12, 0xb8, 0xe5, 0xb4, 0xb0,
    0x89, 0x69, 0x97, 0x4a, 0x0c, 0x96, 0x77, 0x7e, 0x65, 0xb9, 0xf1, 0x09, 0xc5, 0x6e, 0xc6, 0x84,
    0x18, 0xf0, 0x7d, 0xec, 0x3a, 0xdc, 0x4d, 0x20, 0x79, 0xee, 0x5f, 0x3e, 0xd7, 0xcb, 0x39, 0x48
};

// 线性变换L
static inline uint32_t linear_transform(uint32_t b) {
    return b ^ ROTL(b, 2) ^ ROTL(b, 10) ^ ROTL(b, 18) ^ ROTL(b, 24);
}

// 初始化T-table查找表
void sm4_ttable_init(void) {
    if (ttable_initialized) {
        return;
    }

    for (int i = 0; i < 256; i++) {
        uint32_t sbox_out = sm4_sbox_table[i];
        uint32_t temp;

        // T-table 0: S盒输出在最高字节位置
        temp = sbox_out << 24;
        sm4_ttable0[i] = linear_transform(temp);

        // T-table 1: S盒输出在第二字节位置
        temp = sbox_out << 16;
        sm4_ttable1[i] = linear_transform(temp);

        // T-table 2: S盒输出在第三字节位置
        temp = sbox_out << 8;
        sm4_ttable2[i] = linear_transform(temp);

        // T-table 3: S盒输出在最低字节位置
        temp = sbox_out;
        sm4_ttable3[i] = linear_transform(temp);
    }

    ttable_initialized = 1;
}

// T-table优化的T变换
static inline uint32_t sm4_T_ttable(uint32_t x) {
    return sm4_ttable0[(x >> 24) & 0xff] ^
           sm4_ttable1[(x >> 16) & 0xff] ^
           sm4_ttable2[(x >> 8) & 0xff] ^
           sm4_ttable3[x & 0xff];
}

// T-table优化的SM4分组加密
void sm4_crypt_block_ttable(const sm4_context *ctx, const uint8_t input[SM4_BLOCK_SIZE], 
                            uint8_t output[SM4_BLOCK_SIZE]) {
    uint32_t x[4];
    uint32_t tmp;
    int i;

    // 确保T-table已初始化
    if (!ttable_initialized) {
        sm4_ttable_init();
    }

    // 输入转换
    x[0] = get_uint32_be(input);
    x[1] = get_uint32_be(input + 4);
    x[2] = get_uint32_be(input + 8);
    x[3] = get_uint32_be(input + 12);

    // 32轮迭代（使用T-table优化）
    for (i = 0; i < SM4_ROUNDS; i++) {
        tmp = x[0] ^ sm4_T_ttable(x[1] ^ x[2] ^ x[3] ^ ctx->rk[i]);
        x[0] = x[1];
        x[1] = x[2];
        x[2] = x[3];
        x[3] = tmp;
    }

    // 反序输出
    put_uint32_be(output, x[3]);
    put_uint32_be(output + 4, x[2]);
    put_uint32_be(output + 8, x[1]);
    put_uint32_be(output + 12, x[0]);
}

// T-table优化的ECB模式
int sm4_crypt_ecb_ttable(const sm4_context *ctx, size_t length,
                         const uint8_t *input, uint8_t *output) {
    if (ctx == NULL || input == NULL || output == NULL) {
        return -1;
    }

    if (length % SM4_BLOCK_SIZE != 0) {
        return -1;
    }

    // 确保T-table已初始化
    if (!ttable_initialized) {
        sm4_ttable_init();
    }

    while (length > 0) {
        sm4_crypt_block_ttable(ctx, input, output);
        input += SM4_BLOCK_SIZE;
        output += SM4_BLOCK_SIZE;
        length -= SM4_BLOCK_SIZE;
    }

    return 0;
}

// T-table优化的并行ECB模式（处理多个块以提高cache利用率）
int sm4_crypt_ecb_ttable_parallel(const sm4_context *ctx, size_t length,
                                  const uint8_t *input, uint8_t *output) {
    if (ctx == NULL || input == NULL || output == NULL) {
        return -1;
    }

    if (length % SM4_BLOCK_SIZE != 0) {
        return -1;
    }

    // 确保T-table已初始化
    if (!ttable_initialized) {
        sm4_ttable_init();
    }

    // 并行处理4个块以提高性能
    while (length >= 4 * SM4_BLOCK_SIZE) {
        uint32_t x[4][4]; // 4个块的状态
        uint32_t tmp[4];
        int i, j;

        // 读取4个输入块
        for (j = 0; j < 4; j++) {
            x[j][0] = get_uint32_be(input + j * SM4_BLOCK_SIZE);
            x[j][1] = get_uint32_be(input + j * SM4_BLOCK_SIZE + 4);
            x[j][2] = get_uint32_be(input + j * SM4_BLOCK_SIZE + 8);
            x[j][3] = get_uint32_be(input + j * SM4_BLOCK_SIZE + 12);
        }

        // 32轮迭代，并行处理4个块
        for (i = 0; i < SM4_ROUNDS; i++) {
            for (j = 0; j < 4; j++) {
                tmp[j] = x[j][0] ^ sm4_T_ttable(x[j][1] ^ x[j][2] ^ x[j][3] ^ ctx->rk[i]);
                x[j][0] = x[j][1];
                x[j][1] = x[j][2];
                x[j][2] = x[j][3];
                x[j][3] = tmp[j];
            }
        }

        // 输出4个块
        for (j = 0; j < 4; j++) {
            put_uint32_be(output + j * SM4_BLOCK_SIZE, x[j][3]);
            put_uint32_be(output + j * SM4_BLOCK_SIZE + 4, x[j][2]);
            put_uint32_be(output + j * SM4_BLOCK_SIZE + 8, x[j][1]);
            put_uint32_be(output + j * SM4_BLOCK_SIZE + 12, x[j][0]);
        }

        input += 4 * SM4_BLOCK_SIZE;
        output += 4 * SM4_BLOCK_SIZE;
        length -= 4 * SM4_BLOCK_SIZE;
    }

    // 处理剩余的块
    while (length > 0) {
        sm4_crypt_block_ttable(ctx, input, output);
        input += SM4_BLOCK_SIZE;
        output += SM4_BLOCK_SIZE;
        length -= SM4_BLOCK_SIZE;
    }

    return 0;
}

// T-table优化的CTR模式
int sm4_crypt_ctr_ttable(const sm4_context *ctx, size_t length, size_t *nc_off,
                         uint8_t nonce_counter[SM4_BLOCK_SIZE], uint8_t stream_block[SM4_BLOCK_SIZE],
                         const uint8_t *input, uint8_t *output) {
    uint8_t c;
    size_t n;

    if (ctx == NULL || nc_off == NULL || nonce_counter == NULL || 
        stream_block == NULL || input == NULL || output == NULL) {
        return -1;
    }

    // 确保T-table已初始化
    if (!ttable_initialized) {
        sm4_ttable_init();
    }

    n = *nc_off;

    if (n >= SM4_BLOCK_SIZE) {
        return -1;
    }

    while (length--) {
        if (n == 0) {
            sm4_crypt_block_ttable(ctx, nonce_counter, stream_block);
            
            // 递增计数器
            for (int i = SM4_BLOCK_SIZE - 1; i >= 0; i--) {
                if (++nonce_counter[i] != 0) {
                    break;
                }
            }
        }
        
        c = *input++;
        *output++ = c ^ stream_block[n];
        n = (n + 1) % SM4_BLOCK_SIZE;
    }

    *nc_off = n;
    return 0;
}

// 并行CTR模式（预生成多个keystream块）
int sm4_crypt_ctr_ttable_parallel(const sm4_context *ctx, size_t length, size_t *nc_off,
                                  uint8_t nonce_counter[SM4_BLOCK_SIZE], uint8_t stream_block[SM4_BLOCK_SIZE],
                                  const uint8_t *input, uint8_t *output) {
    uint8_t counters[4][SM4_BLOCK_SIZE];
    uint8_t keystream[4][SM4_BLOCK_SIZE];
    size_t n = *nc_off;
    size_t processed = 0;

    if (ctx == NULL || nc_off == NULL || nonce_counter == NULL || 
        stream_block == NULL || input == NULL || output == NULL) {
        return -1;
    }

    // 确保T-table已初始化
    if (!ttable_initialized) {
        sm4_ttable_init();
    }

    if (n >= SM4_BLOCK_SIZE) {
        return -1;
    }

    // 处理开始时的不对齐部分
    while (n > 0 && length > 0) {
        *output++ = *input++ ^ stream_block[n];
        n = (n + 1) % SM4_BLOCK_SIZE;
        length--;
        processed++;
        
        if (n == 0) {
            // 递增计数器
            for (int i = SM4_BLOCK_SIZE - 1; i >= 0; i--) {
                if (++nonce_counter[i] != 0) {
                    break;
                }
            }
        }
    }

    // 并行处理完整的块
    while (length >= 4 * SM4_BLOCK_SIZE) {
        // 准备4个计数器
        for (int i = 0; i < 4; i++) {
            memcpy(counters[i], nonce_counter, SM4_BLOCK_SIZE);
            // 计算第i个计数器值
            uint32_t carry = i;
            for (int j = SM4_BLOCK_SIZE - 1; j >= 0 && carry; j--) {
                carry += counters[i][j];
                counters[i][j] = carry & 0xff;
                carry >>= 8;
            }
        }

        // 并行生成4个keystream块
        for (int i = 0; i < 4; i++) {
            sm4_crypt_block_ttable(ctx, counters[i], keystream[i]);
        }

        // 应用keystream
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < SM4_BLOCK_SIZE; j++) {
                output[i * SM4_BLOCK_SIZE + j] = input[i * SM4_BLOCK_SIZE + j] ^ keystream[i][j];
            }
        }

        // 更新nonce_counter（加4）
        uint32_t carry = 4;
        for (int i = SM4_BLOCK_SIZE - 1; i >= 0 && carry; i--) {
            carry += nonce_counter[i];
            nonce_counter[i] = carry & 0xff;
            carry >>= 8;
        }

        input += 4 * SM4_BLOCK_SIZE;
        output += 4 * SM4_BLOCK_SIZE;
        length -= 4 * SM4_BLOCK_SIZE;
        processed += 4 * SM4_BLOCK_SIZE;
    }

    // 处理剩余数据
    while (length > 0) {
        if (n == 0) {
            sm4_crypt_block_ttable(ctx, nonce_counter, stream_block);
            
            // 递增计数器
            for (int i = SM4_BLOCK_SIZE - 1; i >= 0; i--) {
                if (++nonce_counter[i] != 0) {
                    break;
                }
            }
        }
        
        *output++ = *input++ ^ stream_block[n];
        n = (n + 1) % SM4_BLOCK_SIZE;
        length--;
        processed++;
    }

    *nc_off = n;
    return 0;
}
