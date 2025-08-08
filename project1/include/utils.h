#ifndef UTILS_H
#define UTILS_H

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

// 包含系统头文件以获取ssize_t定义
#ifdef _WIN32
    #include <io.h>
    #include <basetsd.h>
    typedef SSIZE_T ssize_t;
#else
    #include <sys/types.h>
    #include <unistd.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif

// 十六进制转换

/**
 * 将字节数组转换为十六进制字符串
 * @param data 字节数组
 * @param len 数组长度
 * @param hex_str 输出字符串缓冲区(至少需要len*2+1字节)
 */
void bytes_to_hex(const uint8_t *data, size_t len, char *hex_str);

/**
 * 将十六进制字符串转换为字节数组
 * @param hex_str 十六进制字符串
 * @param data 输出字节数组
 * @param max_len 数组最大长度
 * @return 实际转换的字节数，-1表示错误
 */
int hex_to_bytes(const char *hex_str, uint8_t *data, size_t max_len);

// 随机数生成

/**
 * 生成密码学安全随机数
 * @param data 输出缓冲区
 * @param len 长度
 * @return 0=成功, -1=失败
 */
int generate_random(uint8_t *data, size_t len);

/**
 * 生成随机密钥
 * @param key 密钥缓冲区(16字节)
 * @return 0=成功, -1=失败
 */
int generate_random_key(uint8_t key[16]);

/**
 * 生成随机IV
 * @param iv IV缓冲区
 * @param len IV长度
 * @return 0=成功, -1=失败
 */
int generate_random_iv(uint8_t *iv, size_t len);

// 时间测量

/**
 * 高精度时间戳
 */
typedef struct {
    uint64_t cycles;
    double seconds;
} timestamp_t;

/**
 * 获取当前时间戳
 * @param ts 时间戳结构体
 */
void get_timestamp(timestamp_t *ts);

/**
 * 计算时间差
 * @param start 开始时间
 * @param end 结束时间
 * @param diff 时间差输出
 */
void calc_time_diff(const timestamp_t *start, const timestamp_t *end, timestamp_t *diff);

/**
 * 获取CPU周期计数
 * @return CPU周期数
 */
static inline uint64_t rdtsc(void) {
#if defined(__i386__) || defined(__x86_64__)
    uint32_t lo, hi;
    __asm__ __volatile__ ("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
#else
    return 0; // 其他架构的实现
#endif
}

// 内存操作

/**
 * 安全内存比较(防御时间攻击)
 * @param a 内存块1
 * @param b 内存块2
 * @param n 比较长度
 * @return 0=相等, 非0=不等
 */
int secure_memcmp(const void *a, const void *b, size_t n);

/**
 * 安全清零内存
 * @param ptr 内存指针
 * @param len 长度
 */
void secure_zero(void *ptr, size_t len);

// 文件I/O

/**
 * 从文件读取数据
 * @param filename 文件名
 * @param data 数据缓冲区(如果为NULL则只返回文件大小)
 * @param max_len 缓冲区最大长度
 * @return 实际读取的字节数，-1表示错误
 */
ssize_t read_file(const char *filename, uint8_t *data, size_t max_len);

/**
 * 向文件写入数据
 * @param filename 文件名
 * @param data 数据
 * @param len 数据长度
 * @return 0=成功, -1=失败
 */
int write_file(const char *filename, const uint8_t *data, size_t len);

// 测试向量验证

/**
 * SM4测试向量结构
 */
typedef struct {
    const char *name;
    uint8_t key[16];
    uint8_t plaintext[16];
    uint8_t ciphertext[16];
} sm4_test_vector;

/**
 * GCM测试向量结构
 */
typedef struct {
    const char *name;
    uint8_t key[16];
    const uint8_t *iv;
    size_t iv_len;
    const uint8_t *aad;
    size_t aad_len;
    const uint8_t *plaintext;
    size_t plaintext_len;
    const uint8_t *ciphertext;
    const uint8_t *tag;
    size_t tag_len;
} gcm_test_vector;

/**
 * 获取SM4标准测试向量
 * @param index 测试向量索引
 * @return 测试向量指针，NULL表示无效索引
 */
const sm4_test_vector *get_sm4_test_vector(int index);

/**
 * 获取GCM测试向量
 * @param index 测试向量索引
 * @return 测试向量指针，NULL表示无效索引
 */
const gcm_test_vector *get_gcm_test_vector(int index);

/**
 * 获取SM4测试向量数量
 * @return 测试向量数量
 */
int get_sm4_test_vector_count(void);

/**
 * 获取GCM测试向量数量
 * @return 测试向量数量
 */
int get_gcm_test_vector_count(void);

// 性能统计

/**
 * 性能统计结构
 */
typedef struct {
    uint64_t total_bytes;
    uint64_t total_cycles;
    double total_time;
    double cycles_per_byte;
    double mbps;
    double ops_per_second;
} perf_stats;

/**
 * 初始化性能统计
 * @param stats 统计结构体
 */
void perf_stats_init(perf_stats *stats);

/**
 * 添加性能数据点
 * @param stats 统计结构体
 * @param bytes 处理的字节数
 * @param cycles CPU周期数
 * @param seconds 耗时(秒)
 */
void perf_stats_add(perf_stats *stats, uint64_t bytes, uint64_t cycles, double seconds);

/**
 * 计算性能指标
 * @param stats 统计结构体
 */
void perf_stats_calc(perf_stats *stats);

/**
 * 打印性能统计
 * @param stats 统计结构体
 * @param name 测试名称
 */
void perf_stats_print(const perf_stats *stats, const char *name);

// 调试输出

/**
 * 打印字节数组(十六进制格式)
 * @param name 数组名称
 * @param data 字节数组
 * @param len 数组长度
 */
void print_bytes(const char *name, const uint8_t *data, size_t len);

/**
 * 打印32位字数组
 * @param name 数组名称
 * @param data 32位字数组
 * @param count 数组元素数量
 */
void print_uint32_array(const char *name, const uint32_t *data, size_t count);

// 错误处理

#define UTILS_SUCCESS   0
#define UTILS_ERROR    -1
#define UTILS_ERROR_INVALID_PARAM -2
#define UTILS_ERROR_INSUFFICIENT_BUFFER -3
#define UTILS_ERROR_FILE_IO -4
#define UTILS_ERROR_RANDOM -5

/**
 * 获取错误描述
 * @param error_code 错误码
 * @return 错误描述字符串
 */
const char *utils_strerror(int error_code);

#ifdef __cplusplus
}
#endif

#endif /* UTILS_H */
