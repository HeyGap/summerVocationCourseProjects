#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "sm3.h"
#include "sm3_opt.h"

void print_usage(const char *prog_name) {
    printf("用法: %s [选项]\n", prog_name);
    printf("选项:\n");
    printf("  -h, --help     显示此帮助信息\n");
    printf("  -v, --verify   验证优化实现的正确性\n");
    printf("  -b, --bench    运行性能基准测试\n");
    printf("  -c, --compare  比较不同实现的性能\n");
    printf("  -m, --multi    测试多流并行哈希\n");
    printf("  -a, --all      运行所有测试\n");
    printf("  -t <text>      计算指定文本的SM3哈希\n");
}

void test_basic_functionality() {
    printf("=== 基本功能测试 ===\n");
    
    const char *test_strings[] = {
        "abc",
        "abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd",
        "hello world",
        ""
    };
    int num_tests = sizeof(test_strings) / sizeof(test_strings[0]);
    
    for (int i = 0; i < num_tests; i++) {
        uint8_t digest[SM3_DIGEST_SIZE];
        const uint8_t *data = (const uint8_t*)test_strings[i];
        size_t len = strlen(test_strings[i]);
        
        sm3_hash(data, len, digest);
        
        printf("输入: \"%s\"\n", test_strings[i]);
        printf("SM3:  ");
        sm3_print_digest(digest);
        printf("\n");
    }
}

void test_optimization_comparison() {
    printf("=== 优化实现比较测试 ===\n");
    
    const char *test_data = "这是一个用于测试SM3哈希算法优化实现的较长文本字符串，"
                           "它包含了中文字符和英文字符，用于验证不同SIMD优化版本的正确性和性能。"
                           "We will test various SIMD optimizations including SSE2 and AVX2 implementations.";
    
    size_t len = strlen(test_data);
    const uint8_t *data = (const uint8_t*)test_data;
    
    uint8_t digest_basic[SM3_DIGEST_SIZE];
    uint8_t digest_sse2[SM3_DIGEST_SIZE];
    uint8_t digest_avx2[SM3_DIGEST_SIZE];
    uint8_t digest_auto[SM3_DIGEST_SIZE];
    
    printf("测试数据长度: %zu 字节\n\n", len);
    
    // 测试不同实现
    sm3_hash(data, len, digest_basic);
    sm3_opt_hash(data, len, digest_sse2, SM3_IMPL_SSE2);
    sm3_opt_hash(data, len, digest_avx2, SM3_IMPL_AVX2);
    sm3_opt_hash(data, len, digest_auto, SM3_IMPL_AUTO);
    
    printf("基础实现结果: ");
    sm3_print_digest(digest_basic);
    
    printf("SSE2优化结果: ");
    sm3_print_digest(digest_sse2);
    
    printf("AVX2优化结果: ");
    sm3_print_digest(digest_avx2);
    
    printf("自动选择结果: ");
    sm3_print_digest(digest_auto);
    
    // 验证结果一致性
    int sse2_ok = memcmp(digest_basic, digest_sse2, SM3_DIGEST_SIZE) == 0;
    int avx2_ok = memcmp(digest_basic, digest_avx2, SM3_DIGEST_SIZE) == 0;
    int auto_ok = memcmp(digest_basic, digest_auto, SM3_DIGEST_SIZE) == 0;
    
    printf("\n结果验证:\n");
    printf("  SSE2优化: %s\n", sse2_ok ? "✓ 正确" : "✗ 错误");
    printf("  AVX2优化: %s\n", avx2_ok ? "✓ 正确" : "✗ 错误");
    printf("  自动选择: %s\n", auto_ok ? "✓ 正确" : "✗ 错误");
}

void test_multiway_parallel() {
    printf("=== 多流并行测试 ===\n");
    
    const char *data_streams[] = {
        "第一个数据流 - Stream 1",
        "第二个数据流 - Stream 2 with more data",
        "第三个数据流 - Stream 3 has even longer content for testing",
        "第四个数据流 - Stream 4 contains the longest test content to verify multiway parallel processing"
    };
    
    size_t lengths[4];
    uint8_t digest_serial[4][SM3_DIGEST_SIZE];
    uint8_t digest_parallel[4][SM3_DIGEST_SIZE];
    
    printf("测试4路并行哈希计算...\n\n");
    
    // 串行计算
    printf("串行计算结果:\n");
    for (int i = 0; i < 4; i++) {
        lengths[i] = strlen(data_streams[i]);
        sm3_hash((const uint8_t*)data_streams[i], lengths[i], digest_serial[i]);
        
        printf("流%d: ", i + 1);
        sm3_print_digest(digest_serial[i]);
    }
    
    // 并行计算
    printf("\n4路并行计算结果:\n");
    sm3_hash_4way_avx2((const uint8_t*)data_streams[0], lengths[0],
                       (const uint8_t*)data_streams[1], lengths[1],
                       (const uint8_t*)data_streams[2], lengths[2],
                       (const uint8_t*)data_streams[3], lengths[3],
                       digest_parallel[0], digest_parallel[1],
                       digest_parallel[2], digest_parallel[3]);
    
    for (int i = 0; i < 4; i++) {
        printf("流%d: ", i + 1);
        sm3_print_digest(digest_parallel[i]);
    }
    
    // 验证结果
    printf("\n结果验证:\n");
    int all_correct = 1;
    for (int i = 0; i < 4; i++) {
        int correct = memcmp(digest_serial[i], digest_parallel[i], SM3_DIGEST_SIZE) == 0;
        printf("  流%d: %s\n", i + 1, correct ? "✓ 正确" : "✗ 错误");
        if (!correct) all_correct = 0;
    }
    
    printf("\n总体结果: %s\n", all_correct ? "✓ 4路并行计算正确" : "✗ 4路并行计算有误");
}

void demo_cpu_features() {
    printf("=== CPU特性检测 ===\n");
    
    cpu_features_t features = sm3_detect_cpu_features();
    
    printf("当前CPU支持的特性:\n");
    printf("  SSE2指令集: %s\n", features.sse2_support ? "✓ 支持" : "✗ 不支持");
    printf("  AVX2指令集: %s\n", features.avx2_support ? "✓ 支持" : "✗ 不支持");
    printf("  AES指令集:  %s\n", features.aes_support ? "✓ 支持" : "✗ 不支持");
    
    printf("\n推荐的优化策略:\n");
    if (features.avx2_support) {
        printf("  - 使用AVX2优化实现，支持4路并行处理\n");
        printf("  - 可以使用256位SIMD寄存器进行向量化计算\n");
    } else if (features.sse2_support) {
        printf("  - 使用SSE2优化实现，支持2路并行处理\n");
        printf("  - 可以使用128位SIMD寄存器进行向量化计算\n");
    } else {
        printf("  - 使用基础标量实现\n");
        printf("  - 建议升级CPU以获得更好的性能\n");
    }
}

int main(int argc, char *argv[]) {
    printf("SM3哈希算法SIMD优化实现演示\n");
    printf("================================\n\n");
    
    if (argc == 1) {
        // 默认运行所有基本测试
        demo_cpu_features();
        printf("\n");
        test_basic_functionality();
        printf("\n");
        test_optimization_comparison();
        printf("\n");
        test_multiway_parallel();
        return 0;
    }
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        }
        else if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verify") == 0) {
            if (!sm3_verify_optimizations()) {
                printf("验证失败！\n");
                return 1;
            }
            printf("所有优化实现验证通过！\n");
        }
        else if (strcmp(argv[i], "-b") == 0 || strcmp(argv[i], "--bench") == 0) {
            // 创建测试数据
            size_t test_size = 1024 * 1024;  // 1MB
            uint8_t *test_data = malloc(test_size);
            if (test_data) {
                for (size_t j = 0; j < test_size; j++) {
                    test_data[j] = (uint8_t)(j & 0xFF);
                }
                sm3_run_benchmarks(test_data, test_size, 10);
                free(test_data);
            }
        }
        else if (strcmp(argv[i], "-c") == 0 || strcmp(argv[i], "--compare") == 0) {
            test_optimization_comparison();
        }
        else if (strcmp(argv[i], "-m") == 0 || strcmp(argv[i], "--multi") == 0) {
            test_multiway_parallel();
        }
        else if (strcmp(argv[i], "-a") == 0 || strcmp(argv[i], "--all") == 0) {
            demo_cpu_features();
            printf("\n");
            
            if (sm3_verify_optimizations()) {
                printf("✓ 所有优化实现验证通过\n\n");
            } else {
                printf("✗ 优化实现验证失败\n\n");
            }
            
            test_optimization_comparison();
            printf("\n");
            test_multiway_parallel();
            printf("\n");
            sm3_comprehensive_benchmark();
        }
        else if (strcmp(argv[i], "-t") == 0 && i + 1 < argc) {
            // 计算指定文本的哈希
            const char *text = argv[i + 1];
            uint8_t digest[SM3_DIGEST_SIZE];
            sm3_hash((const uint8_t*)text, strlen(text), digest);
            
            printf("输入文本: \"%s\"\n", text);
            printf("SM3哈希:  ");
            sm3_print_digest(digest);
            i++; // 跳过文本参数
        }
        else {
            printf("未知选项: %s\n", argv[i]);
            print_usage(argv[0]);
            return 1;
        }
    }
    
    return 0;
}
