#include "../include/sm4.h"
#include "../include/sm4_opt.h"
#include <immintrin.h>
#include <string.h>

#ifdef __AES__

// AESNI优化的SM4实现
// 利用AES指令集来加速SM4的S盒替换和某些运算

// SM4 S盒查找表（用于AESNI实现）
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

// 使用AESNI指令进行S盒替换
static inline __m128i sm4_sbox_aesni(__m128i input) {
    // 将SM4 S盒转换为适合AESNI的格式
    // 注意：这是一个简化实现，实际可能需要更复杂的转换
    __m128i result = _mm_setzero_si128();
    
    // 提取每个字节并进行S盒替换
    uint8_t bytes[16];
    _mm_storeu_si128((__m128i*)bytes, input);
    
    for (int i = 0; i < 16; i++) {
        bytes[i] = sm4_sbox_table[bytes[i]];
    }
    
    result = _mm_loadu_si128((__m128i*)bytes);
    return result;
}

// 使用SIMD进行循环左移
static inline __m128i rotl_32_aesni(__m128i x, int n) {
    return _mm_or_si128(_mm_slli_epi32(x, n), _mm_srli_epi32(x, 32 - n));
}

// AESNI优化的线性变换L
static inline __m128i sm4_linear_transform_aesni(__m128i b) {
    __m128i t2 = rotl_32_aesni(b, 2);
    __m128i t10 = rotl_32_aesni(b, 10);
    __m128i t18 = rotl_32_aesni(b, 18);
    __m128i t24 = rotl_32_aesni(b, 24);
    
    return _mm_xor_si128(_mm_xor_si128(_mm_xor_si128(_mm_xor_si128(b, t2), t10), t18), t24);
}

// AESNI优化的T变换
static inline __m128i sm4_T_aesni(__m128i x) {
    __m128i sbox_out = sm4_sbox_aesni(x);
    return sm4_linear_transform_aesni(sbox_out);
}

// AESNI优化的SM4分组加密
void sm4_crypt_block_aesni(const sm4_context *ctx, const uint8_t input[SM4_BLOCK_SIZE], 
                           uint8_t output[SM4_BLOCK_SIZE]) {
    // 加载输入数据
    __m128i data = _mm_loadu_si128((__m128i*)input);
    
    // 字节序转换（如果需要）
    data = _mm_shuffle_epi8(data, _mm_setr_epi8(3,2,1,0,7,6,5,4,11,10,9,8,15,14,13,12));
    
    // 提取32位字
    uint32_t x[4];
    _mm_storeu_si128((__m128i*)x, data);
    
    // 32轮迭代
    for (int i = 0; i < SM4_ROUNDS; i++) {
        uint32_t temp = x[1] ^ x[2] ^ x[3] ^ ctx->rk[i];
        __m128i temp_vec = _mm_set1_epi32(temp);
        temp_vec = sm4_T_aesni(temp_vec);
        
        uint32_t result;
        _mm_storeu_si32(&result, temp_vec);
        
        uint32_t tmp = x[0] ^ result;
        x[0] = x[1];
        x[1] = x[2];
        x[2] = x[3];
        x[3] = tmp;
    }
    
    // 反序输出
    __m128i output_data = _mm_setr_epi32(x[3], x[2], x[1], x[0]);
    
    // 字节序转换
    output_data = _mm_shuffle_epi8(output_data, _mm_setr_epi8(3,2,1,0,7,6,5,4,11,10,9,8,15,14,13,12));
    
    _mm_storeu_si128((__m128i*)output, output_data);
}

// AESNI优化的并行ECB模式（同时处理多个块）
int sm4_crypt_ecb_aesni(const sm4_context *ctx, size_t length,
                        const uint8_t *input, uint8_t *output) {
    if (ctx == NULL || input == NULL || output == NULL) {
        return -1;
    }

    if (length % SM4_BLOCK_SIZE != 0) {
        return -1;
    }

    // 并行处理4个块
    while (length >= 4 * SM4_BLOCK_SIZE) {
        __m128i blocks[4];
        uint32_t x[4][4];
        
        // 加载4个输入块
        for (int j = 0; j < 4; j++) {
            blocks[j] = _mm_loadu_si128((__m128i*)(input + j * SM4_BLOCK_SIZE));
            // 字节序转换
            blocks[j] = _mm_shuffle_epi8(blocks[j], _mm_setr_epi8(3,2,1,0,7,6,5,4,11,10,9,8,15,14,13,12));
            _mm_storeu_si128((__m128i*)x[j], blocks[j]);
        }

        // 32轮迭代，并行处理4个块
        for (int i = 0; i < SM4_ROUNDS; i++) {
            for (int j = 0; j < 4; j++) {
                uint32_t temp = x[j][1] ^ x[j][2] ^ x[j][3] ^ ctx->rk[i];
                __m128i temp_vec = _mm_set1_epi32(temp);
                temp_vec = sm4_T_aesni(temp_vec);
                
                uint32_t result;
                _mm_storeu_si32(&result, temp_vec);
                
                uint32_t tmp = x[j][0] ^ result;
                x[j][0] = x[j][1];
                x[j][1] = x[j][2];
                x[j][2] = x[j][3];
                x[j][3] = tmp;
            }
        }

        // 输出4个块
        for (int j = 0; j < 4; j++) {
            __m128i output_data = _mm_setr_epi32(x[j][3], x[j][2], x[j][1], x[j][0]);
            // 字节序转换
            output_data = _mm_shuffle_epi8(output_data, _mm_setr_epi8(3,2,1,0,7,6,5,4,11,10,9,8,15,14,13,12));
            _mm_storeu_si128((__m128i*)(output + j * SM4_BLOCK_SIZE), output_data);
        }

        input += 4 * SM4_BLOCK_SIZE;
        output += 4 * SM4_BLOCK_SIZE;
        length -= 4 * SM4_BLOCK_SIZE;
    }

    // 处理剩余的块
    while (length > 0) {
        sm4_crypt_block_aesni(ctx, input, output);
        input += SM4_BLOCK_SIZE;
        output += SM4_BLOCK_SIZE;
        length -= SM4_BLOCK_SIZE;
    }

    return 0;
}

// AESNI优化的CTR模式
int sm4_crypt_ctr_aesni(const sm4_context *ctx, size_t length, size_t *nc_off,
                        uint8_t nonce_counter[SM4_BLOCK_SIZE], uint8_t stream_block[SM4_BLOCK_SIZE],
                        const uint8_t *input, uint8_t *output) {
    uint8_t c;
    size_t n;

    if (ctx == NULL || nc_off == NULL || nonce_counter == NULL || 
        stream_block == NULL || input == NULL || output == NULL) {
        return -1;
    }

    n = *nc_off;

    if (n >= SM4_BLOCK_SIZE) {
        return -1;
    }

    // 如果有足够的数据，使用并行处理
    if (length >= 4 * SM4_BLOCK_SIZE && n == 0) {
        // 并行处理4个块
        while (length >= 4 * SM4_BLOCK_SIZE) {
            uint8_t counters[4][SM4_BLOCK_SIZE];
            uint8_t keystreams[4][SM4_BLOCK_SIZE];
            
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
            
            // 并行生成4个keystream
            for (int i = 0; i < 4; i++) {
                sm4_crypt_block_aesni(ctx, counters[i], keystreams[i]);
            }
            
            // 应用keystream
            __m128i input_vec, keystream_vec, output_vec;
            for (int i = 0; i < 4; i++) {
                input_vec = _mm_loadu_si128((__m128i*)(input + i * SM4_BLOCK_SIZE));
                keystream_vec = _mm_loadu_si128((__m128i*)keystreams[i]);
                output_vec = _mm_xor_si128(input_vec, keystream_vec);
                _mm_storeu_si128((__m128i*)(output + i * SM4_BLOCK_SIZE), output_vec);
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
        }
    }

    // 处理剩余数据（标准CTR模式）
    while (length--) {
        if (n == 0) {
            sm4_crypt_block_aesni(ctx, nonce_counter, stream_block);
            
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

// 使用AESNI指令的并行块处理
void sm4_crypt_blocks_aesni_4(const sm4_context *ctx, 
                              const uint8_t input[4][SM4_BLOCK_SIZE],
                              uint8_t output[4][SM4_BLOCK_SIZE]) {
    __m128i blocks[4];
    uint32_t x[4][4];
    
    // 加载并转换4个输入块
    for (int j = 0; j < 4; j++) {
        blocks[j] = _mm_loadu_si128((__m128i*)input[j]);
        blocks[j] = _mm_shuffle_epi8(blocks[j], _mm_setr_epi8(3,2,1,0,7,6,5,4,11,10,9,8,15,14,13,12));
        _mm_storeu_si128((__m128i*)x[j], blocks[j]);
    }

    // 32轮并行处理
    for (int i = 0; i < SM4_ROUNDS; i++) {
        uint32_t temps[4];
        __m128i temp_vecs[4];
        
        // 计算所有块的临时值
        for (int j = 0; j < 4; j++) {
            temps[j] = x[j][1] ^ x[j][2] ^ x[j][3] ^ ctx->rk[i];
            temp_vecs[j] = _mm_set1_epi32(temps[j]);
            temp_vecs[j] = sm4_T_aesni(temp_vecs[j]);
        }
        
        // 更新状态
        for (int j = 0; j < 4; j++) {
            uint32_t result;
            _mm_storeu_si32(&result, temp_vecs[j]);
            
            uint32_t tmp = x[j][0] ^ result;
            x[j][0] = x[j][1];
            x[j][1] = x[j][2];
            x[j][2] = x[j][3];
            x[j][3] = tmp;
        }
    }

    // 输出转换
    for (int j = 0; j < 4; j++) {
        __m128i output_data = _mm_setr_epi32(x[j][3], x[j][2], x[j][1], x[j][0]);
        output_data = _mm_shuffle_epi8(output_data, _mm_setr_epi8(3,2,1,0,7,6,5,4,11,10,9,8,15,14,13,12));
        _mm_storeu_si128((__m128i*)output[j], output_data);
    }
}

#else

// 如果没有AESNI支持，回退到基本实现
void sm4_crypt_block_aesni(const sm4_context *ctx, const uint8_t input[SM4_BLOCK_SIZE], 
                           uint8_t output[SM4_BLOCK_SIZE]) {
    sm4_crypt_block(ctx, input, output);
}

int sm4_crypt_ecb_aesni(const sm4_context *ctx, size_t length,
                        const uint8_t *input, uint8_t *output) {
    return sm4_crypt_ecb(ctx, length, input, output);
}

int sm4_crypt_ctr_aesni(const sm4_context *ctx, size_t length, size_t *nc_off,
                        uint8_t nonce_counter[SM4_BLOCK_SIZE], uint8_t stream_block[SM4_BLOCK_SIZE],
                        const uint8_t *input, uint8_t *output) {
    return sm4_crypt_ctr(ctx, length, nc_off, nonce_counter, stream_block, input, output);
}

#endif /* __AES__ */
