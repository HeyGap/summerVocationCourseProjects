#ifndef SM3_H
#define SM3_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// SM3哈希值长度（字节）
#define SM3_DIGEST_SIZE     32
// SM3哈希值长度（32位字）
#define SM3_DIGEST_WORDS    8
// SM3分组长度（字节）
#define SM3_BLOCK_SIZE      64
// SM3分组长度（32位字）
#define SM3_BLOCK_WORDS     16

/**
 * SM3上下文结构体
 */
typedef struct {
    uint32_t state[SM3_DIGEST_WORDS];   // 中间哈希值
    uint8_t buffer[SM3_BLOCK_SIZE];     // 输入缓冲区
    uint64_t count;                     // 已处理的总字节数
    size_t buffer_len;                  // 缓冲区中的字节数
} sm3_context_t;

/**
 * 初始化SM3上下文
 * 
 * @param ctx SM3上下文指针
 */
void sm3_init(sm3_context_t *ctx);

/**
 * 更新SM3计算，处理输入数据
 * 
 * @param ctx SM3上下文指针
 * @param data 输入数据指针
 * @param len 输入数据长度（字节）
 */
void sm3_update(sm3_context_t *ctx, const uint8_t *data, size_t len);

/**
 * 完成SM3计算，输出最终哈希值
 * 
 * @param ctx SM3上下文指针
 * @param digest 输出哈希值的缓冲区（至少32字节）
 */
void sm3_final(sm3_context_t *ctx, uint8_t *digest);

/**
 * 一次性计算SM3哈希值
 * 
 * @param data 输入数据指针
 * @param len 输入数据长度（字节）
 * @param digest 输出哈希值的缓冲区（至少32字节）
 */
void sm3_hash(const uint8_t *data, size_t len, uint8_t *digest);

/**
 * 将哈希值转换为十六进制字符串
 * 
 * @param digest 哈希值（32字节）
 * @param hex_str 输出的十六进制字符串（至少65字节，包含结尾0）
 */
void sm3_digest_to_hex(const uint8_t *digest, char *hex_str);

/**
 * 打印哈希值的十六进制表示
 * 
 * @param digest 哈希值（32字节）
 */
void sm3_print_digest(const uint8_t *digest);

// 内部函数声明（供测试使用）
void sm3_process_block(uint32_t state[SM3_DIGEST_WORDS], const uint8_t block[SM3_BLOCK_SIZE]);

#ifdef __cplusplus
}
#endif

#endif // SM3_H
