#ifndef SM4_H
#define SM4_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// SM4常数定义
#define SM4_BLOCK_SIZE 16    // 128 bits
#define SM4_KEY_SIZE   16    // 128 bits
#define SM4_ROUNDS     32    // 32轮

// SM4上下文结构
typedef struct {
    uint32_t rk[SM4_ROUNDS];  // 轮密钥
    int encrypt;              // 加密标志: 1=加密, 0=解密
} sm4_context;

// 基本接口函数

/**
 * 初始化SM4上下文
 * @param ctx SM4上下文
 * @param key 128位密钥
 * @param encrypt 1=加密模式, 0=解密模式
 * @return 0=成功, -1=失败
 */
int sm4_init(sm4_context *ctx, const uint8_t key[SM4_KEY_SIZE], int encrypt);

/**
 * SM4加密/解密单个分组
 * @param ctx SM4上下文
 * @param input 输入分组(16字节)
 * @param output 输出分组(16字节)
 */
void sm4_crypt_block(const sm4_context *ctx, const uint8_t input[SM4_BLOCK_SIZE], 
                     uint8_t output[SM4_BLOCK_SIZE]);

/**
 * SM4 ECB模式加密/解密
 * @param ctx SM4上下文
 * @param length 数据长度(必须是16的倍数)
 * @param input 输入数据
 * @param output 输出数据
 * @return 0=成功, -1=失败
 */
int sm4_crypt_ecb(const sm4_context *ctx, size_t length,
                  const uint8_t *input, uint8_t *output);

/**
 * SM4 CBC模式加密/解密
 * @param ctx SM4上下文
 * @param mode 1=加密, 0=解密
 * @param length 数据长度(必须是16的倍数)
 * @param iv 初始化向量(16字节，会被修改)
 * @param input 输入数据
 * @param output 输出数据
 * @return 0=成功, -1=失败
 */
int sm4_crypt_cbc(const sm4_context *ctx, int mode, size_t length,
                  uint8_t iv[SM4_BLOCK_SIZE], const uint8_t *input, uint8_t *output);

/**
 * SM4 CTR模式加密/解密
 * @param ctx SM4上下文(必须为加密模式)
 * @param length 数据长度
 * @param nc_off 流密码偏移量指针
 * @param nonce_counter 随机数计数器(16字节，会被修改)
 * @param stream_block 流密码块缓存(16字节)
 * @param input 输入数据
 * @param output 输出数据
 * @return 0=成功, -1=失败
 */
int sm4_crypt_ctr(const sm4_context *ctx, size_t length, size_t *nc_off,
                  uint8_t nonce_counter[SM4_BLOCK_SIZE], uint8_t stream_block[SM4_BLOCK_SIZE],
                  const uint8_t *input, uint8_t *output);

// 内部函数声明（可被优化版本重写）

/**
 * SM4密钥扩展
 * @param key 原始密钥(16字节)
 * @param rk 轮密钥数组(32个uint32_t)
 */
void sm4_setkey_enc(uint32_t rk[SM4_ROUNDS], const uint8_t key[SM4_KEY_SIZE]);

/**
 * 生成解密轮密钥（加密轮密钥逆序）
 * @param dk 解密轮密钥
 * @param ek 加密轮密钥
 */
void sm4_setkey_dec(uint32_t dk[SM4_ROUNDS], const uint32_t ek[SM4_ROUNDS]);

/**
 * SM4轮函数
 * @param x0,x1,x2,x3 输入状态字
 * @param rk 轮密钥
 * @return 轮函数输出
 */
uint32_t sm4_round_function(uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3, uint32_t rk);

/**
 * SM4 S盒替换
 * @param a 输入字节
 * @return S盒输出
 */
uint8_t sm4_sbox(uint8_t a);

/**
 * SM4线性变换L
 * @param b 输入32位字
 * @return 线性变换输出
 */
uint32_t sm4_linear_transform(uint32_t b);

/**
 * SM4密钥扩展线性变换L'
 * @param b 输入32位字
 * @return 密钥扩展线性变换输出
 */
uint32_t sm4_linear_transform_key(uint32_t b);

/**
 * SM4非线性变换τ (调试用)
 * @param a 输入32位字
 * @return 非线性变换输出
 */
uint32_t sm4_tau(uint32_t a);

// 字节序转换辅助函数
static inline uint32_t get_uint32_be(const uint8_t *data) {
    return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | 
           ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

static inline void put_uint32_be(uint8_t *data, uint32_t val) {
    data[0] = (uint8_t)(val >> 24);
    data[1] = (uint8_t)(val >> 16);
    data[2] = (uint8_t)(val >> 8);
    data[3] = (uint8_t)val;
}

// 循环移位宏
#define ROTL(x, n) (((x) << (n)) | ((x) >> (32 - (n))))

#ifdef __cplusplus
}
#endif

#endif /* SM4_H */
