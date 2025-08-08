// 必须在所有头文件之前定义特性宏
#ifndef _WIN32
    #define _POSIX_C_SOURCE 200112L
    #define _DEFAULT_SOURCE
    #define _BSD_SOURCE
#endif

#include "../include/utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// 系统相关的包含
#ifdef _WIN32
    #include <windows.h>
    #include <wincrypt.h>
    #include <io.h>
    #include <fcntl.h>
#else
    #include <time.h>
    #include <unistd.h>
    #include <fcntl.h>
    #include <sys/types.h>
    #include <sys/stat.h>
#endif

// 十六进制转换实现

void bytes_to_hex(const uint8_t *data, size_t len, char *hex_str) {
    static const char hex_chars[] = "0123456789abcdef";
    
    for (size_t i = 0; i < len; i++) {
        hex_str[i * 2] = hex_chars[data[i] >> 4];
        hex_str[i * 2 + 1] = hex_chars[data[i] & 0x0f];
    }
    hex_str[len * 2] = '\0';
}

int hex_to_bytes(const char *hex_str, uint8_t *data, size_t max_len) {
    size_t hex_len = strlen(hex_str);
    
    if (hex_len % 2 != 0) {
        return -1; // 奇数长度
    }
    
    size_t byte_len = hex_len / 2;
    if (byte_len > max_len) {
        return -1; // 缓冲区不足
    }
    
    for (size_t i = 0; i < byte_len; i++) {
        char high = hex_str[i * 2];
        char low = hex_str[i * 2 + 1];
        
        if (!isxdigit(high) || !isxdigit(low)) {
            return -1; // 无效字符
        }
        
        uint8_t high_val, low_val;
        
        if (high >= '0' && high <= '9') {
            high_val = high - '0';
        } else if (high >= 'a' && high <= 'f') {
            high_val = high - 'a' + 10;
        } else if (high >= 'A' && high <= 'F') {
            high_val = high - 'A' + 10;
        } else {
            return -1;
        }
        
        if (low >= '0' && low <= '9') {
            low_val = low - '0';
        } else if (low >= 'a' && low <= 'f') {
            low_val = low - 'a' + 10;
        } else if (low >= 'A' && low <= 'F') {
            low_val = low - 'A' + 10;
        } else {
            return -1;
        }
        
        data[i] = (high_val << 4) | low_val;
    }
    
    return byte_len;
}

// 随机数生成实现

int generate_random(uint8_t *data, size_t len) {
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) {
        // 回退到伪随机数
        srand(time(NULL));
        for (size_t i = 0; i < len; i++) {
            data[i] = rand() & 0xff;
        }
        return 0;
    }
    
    ssize_t result = read(fd, data, len);
    close(fd);
    
    return (result == (ssize_t)len) ? 0 : -1;
}

int generate_random_key(uint8_t key[16]) {
    return generate_random(key, 16);
}

int generate_random_iv(uint8_t *iv, size_t len) {
    return generate_random(iv, len);
}

// 时间测量实现

void get_timestamp(timestamp_t *ts) {
    ts->cycles = rdtsc();
    
#ifdef _WIN32
    LARGE_INTEGER freq, counter;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&counter);
    ts->seconds = (double)counter.QuadPart / freq.QuadPart;
#else
    // 尝试使用高精度时钟
    #if defined(_POSIX_TIMERS) && (_POSIX_TIMERS > 0)
        struct timespec tp;
        if (clock_gettime(CLOCK_MONOTONIC, &tp) == 0) {
            ts->seconds = tp.tv_sec + tp.tv_nsec / 1e9;
        } else if (clock_gettime(CLOCK_REALTIME, &tp) == 0) {
            ts->seconds = tp.tv_sec + tp.tv_nsec / 1e9;
        } else {
            // 备用方案：使用clock()
            ts->seconds = (double)clock() / CLOCKS_PER_SEC;
        }
    #else
        // 如果没有高精度时钟支持，使用标准clock()
        ts->seconds = (double)clock() / CLOCKS_PER_SEC;
    #endif
#endif
}

void calc_time_diff(const timestamp_t *start, const timestamp_t *end, timestamp_t *diff) {
    diff->cycles = end->cycles - start->cycles;
    diff->seconds = end->seconds - start->seconds;
}

// 安全内存操作实现

int secure_memcmp(const void *a, const void *b, size_t n) {
    const uint8_t *pa = (const uint8_t*)a;
    const uint8_t *pb = (const uint8_t*)b;
    uint8_t result = 0;

    for (size_t i = 0; i < n; i++) {
        result |= pa[i] ^ pb[i];
    }

    return result != 0 ? -1 : 0;
}

void secure_zero(void *ptr, size_t len) {
    volatile uint8_t *p = (volatile uint8_t*)ptr;
    while (len--) {
        *p++ = 0;
    }
}

// 文件I/O实现

ssize_t read_file(const char *filename, uint8_t *data, size_t max_len) {
    FILE *fp = fopen(filename, "rb");
    if (fp == NULL) {
        return -1;
    }
    
    if (data == NULL) {
        // 只返回文件大小
        fseek(fp, 0, SEEK_END);
        long size = ftell(fp);
        fclose(fp);
        return size;
    }
    
    size_t bytes_read = fread(data, 1, max_len, fp);
    fclose(fp);
    
    return bytes_read;
}

int write_file(const char *filename, const uint8_t *data, size_t len) {
    FILE *fp = fopen(filename, "wb");
    if (fp == NULL) {
        return -1;
    }
    
    size_t bytes_written = fwrite(data, 1, len, fp);
    fclose(fp);
    
    return (bytes_written == len) ? 0 : -1;
}

// 测试向量定义

static const sm4_test_vector sm4_test_vectors[] = {
    {
        "SM4 Standard Test Vector 1",
        {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10},
        {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10},
        {0x68, 0x1e, 0xdf, 0x34, 0xd2, 0x06, 0x96, 0x5e, 0x86, 0xb3, 0xe9, 0x4f, 0x53, 0x6e, 0x42, 0x46}
    },
    {
        "SM4 Different Key Test",
        {0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10, 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef},
        {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f},
        {0xf7, 0x66, 0x67, 0x8f, 0x13, 0xf0, 0x1a, 0xde, 0xac, 0x1b, 0x3e, 0xa9, 0x55, 0xad, 0xb5, 0x94}
    }
};

static const gcm_test_vector gcm_test_vectors[] = {
    {
        "SM4-GCM Test Vector 1",
        {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef, 0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10},
        (const uint8_t[]){0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00},
        12,
        NULL,
        0,
        (const uint8_t[]){0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00},
        16,
        (const uint8_t[]){0x59, 0x52, 0x98, 0xc7, 0xc6, 0xfd, 0x27, 0x1f, 0x04, 0x02, 0xf8, 0x04, 0xc3, 0x3d, 0x3f, 0x66},
        (const uint8_t[]){0x60, 0x23, 0xa2, 0x39, 0x4d, 0x6f, 0xef, 0x1e, 0xaa, 0x8c, 0x2d, 0x64, 0x95, 0xd8, 0x4b, 0x01},
        16
    }
};

const sm4_test_vector *get_sm4_test_vector(int index) {
    if (index < 0 || index >= (int)(sizeof(sm4_test_vectors) / sizeof(sm4_test_vectors[0]))) {
        return NULL;
    }
    return &sm4_test_vectors[index];
}

const gcm_test_vector *get_gcm_test_vector(int index) {
    if (index < 0 || index >= (int)(sizeof(gcm_test_vectors) / sizeof(gcm_test_vectors[0]))) {
        return NULL;
    }
    return &gcm_test_vectors[index];
}

int get_sm4_test_vector_count(void) {
    return sizeof(sm4_test_vectors) / sizeof(sm4_test_vectors[0]);
}

int get_gcm_test_vector_count(void) {
    return sizeof(gcm_test_vectors) / sizeof(gcm_test_vectors[0]);
}

// 性能统计实现

void perf_stats_init(perf_stats *stats) {
    memset(stats, 0, sizeof(*stats));
}

void perf_stats_add(perf_stats *stats, uint64_t bytes, uint64_t cycles, double seconds) {
    stats->total_bytes += bytes;
    stats->total_cycles += cycles;
    stats->total_time += seconds;
}

void perf_stats_calc(perf_stats *stats) {
    if (stats->total_bytes > 0) {
        stats->cycles_per_byte = (double)stats->total_cycles / stats->total_bytes;
        stats->mbps = (stats->total_bytes / (1024.0 * 1024.0)) / stats->total_time;
        stats->ops_per_second = stats->total_bytes / (16.0 * stats->total_time); // 假设每个操作处理16字节
    }
}

void perf_stats_print(const perf_stats *stats, const char *name) {
    printf("=== %s Performance ===\n", name);
    printf("Total bytes:     %lu\n", (unsigned long)stats->total_bytes);
    printf("Total cycles:    %lu\n", (unsigned long)stats->total_cycles);
    printf("Total time:      %.6f seconds\n", stats->total_time);
    printf("Cycles/byte:     %.2f\n", stats->cycles_per_byte);
    printf("Throughput:      %.2f MB/s\n", stats->mbps);
    printf("Operations/sec:  %.2f\n", stats->ops_per_second);
    printf("\n");
}

// 调试输出实现

void print_bytes(const char *name, const uint8_t *data, size_t len) {
    printf("%s (%zu bytes):\n", name, len);
    
    for (size_t i = 0; i < len; i++) {
        if (i % 16 == 0 && i > 0) {
            printf("\n");
        }
        printf("%02x ", data[i]);
    }
    printf("\n\n");
}

void print_uint32_array(const char *name, const uint32_t *data, size_t count) {
    printf("%s (%zu elements):\n", name, count);
    
    for (size_t i = 0; i < count; i++) {
        if (i % 8 == 0 && i > 0) {
            printf("\n");
        }
        printf("0x%08x ", data[i]);
    }
    printf("\n\n");
}

// 错误处理实现

const char *utils_strerror(int error_code) {
    switch (error_code) {
        case UTILS_SUCCESS:
            return "Success";
        case UTILS_ERROR:
            return "General error";
        case UTILS_ERROR_INVALID_PARAM:
            return "Invalid parameter";
        case UTILS_ERROR_INSUFFICIENT_BUFFER:
            return "Insufficient buffer space";
        case UTILS_ERROR_FILE_IO:
            return "File I/O error";
        case UTILS_ERROR_RANDOM:
            return "Random number generation error";
        default:
            return "Unknown error";
    }
}
