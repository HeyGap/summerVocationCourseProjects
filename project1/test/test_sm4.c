#include "../include/sm4.h"
#include "../include/sm4_opt.h"
#include "../include/utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

// 测试基本SM4功能
static int test_sm4_basic(void) {
    printf("Testing SM4 basic implementation...\n");
    
    int test_count = get_sm4_test_vector_count();
    int passed = 0;
    
    for (int i = 0; i < test_count; i++) {
        const sm4_test_vector *tv = get_sm4_test_vector(i);
        assert(tv != NULL);
        
        printf("  Test Vector %d: %s\n", i + 1, tv->name);
        
        sm4_context ctx;
        uint8_t output[SM4_BLOCK_SIZE];
        
        // 测试加密
        if (sm4_init(&ctx, tv->key, 1) != 0) {
            printf("    FAIL: Failed to initialize encryption context\n");
            continue;
        }
        
        sm4_crypt_block(&ctx, tv->plaintext, output);
        
        if (memcmp(output, tv->ciphertext, SM4_BLOCK_SIZE) != 0) {
            printf("    FAIL: Encryption mismatch\n");
            print_bytes("    Expected", tv->ciphertext, SM4_BLOCK_SIZE);
            print_bytes("    Got", output, SM4_BLOCK_SIZE);
            continue;
        }
        
        // 测试解密
        if (sm4_init(&ctx, tv->key, 0) != 0) {
            printf("    FAIL: Failed to initialize decryption context\n");
            continue;
        }
        
        sm4_crypt_block(&ctx, tv->ciphertext, output);
        
        if (memcmp(output, tv->plaintext, SM4_BLOCK_SIZE) != 0) {
            printf("    FAIL: Decryption mismatch\n");
            print_bytes("    Expected", tv->plaintext, SM4_BLOCK_SIZE);
            print_bytes("    Got", output, SM4_BLOCK_SIZE);
            continue;
        }
        
        printf("    PASS\n");
        passed++;
    }
    
    printf("SM4 Basic Test: %d/%d passed\n\n", passed, test_count);
    return passed == test_count;
}

// 测试ECB模式
static int test_sm4_ecb(void) {
    printf("Testing SM4 ECB mode...\n");
    
    uint8_t key[16] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10
    };
    
    uint8_t plaintext[32] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10,
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10
    };
    
    uint8_t ciphertext[32];
    uint8_t decrypted[32];
    
    sm4_context enc_ctx, dec_ctx;
    
    // 初始化上下文
    if (sm4_init(&enc_ctx, key, 1) != 0 || sm4_init(&dec_ctx, key, 0) != 0) {
        printf("  FAIL: Failed to initialize contexts\n");
        return 0;
    }
    
    // ECB加密
    if (sm4_crypt_ecb(&enc_ctx, 32, plaintext, ciphertext) != 0) {
        printf("  FAIL: ECB encryption failed\n");
        return 0;
    }
    
    // ECB解密
    if (sm4_crypt_ecb(&dec_ctx, 32, ciphertext, decrypted) != 0) {
        printf("  FAIL: ECB decryption failed\n");
        return 0;
    }
    
    // 验证结果
    if (memcmp(plaintext, decrypted, 32) != 0) {
        printf("  FAIL: Decrypted text doesn't match original\n");
        return 0;
    }
    
    printf("  PASS: ECB mode working correctly\n\n");
    return 1;
}

// 测试CBC模式
static int test_sm4_cbc(void) {
    printf("Testing SM4 CBC mode...\n");
    
    uint8_t key[16] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10
    };
    
    uint8_t iv_enc[16] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f
    };
    
    uint8_t iv_dec[16];
    memcpy(iv_dec, iv_enc, 16);
    
    uint8_t plaintext[32] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10,
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10
    };
    
    uint8_t ciphertext[32];
    uint8_t decrypted[32];
    
    sm4_context enc_ctx, dec_ctx;
    
    // 初始化加密上下文
    if (sm4_init(&enc_ctx, key, 1) != 0) {
        printf("  FAIL: Failed to initialize encryption context\n");
        return 0;
    }
    
    // 初始化解密上下文
    if (sm4_init(&dec_ctx, key, 0) != 0) {
        printf("  FAIL: Failed to initialize decryption context\n");
        return 0;
    }
    
    // CBC加密
    if (sm4_crypt_cbc(&enc_ctx, 1, 32, iv_enc, plaintext, ciphertext) != 0) {
        printf("  FAIL: CBC encryption failed\n");
        return 0;
    }
    
    // CBC解密
    if (sm4_crypt_cbc(&dec_ctx, 0, 32, iv_dec, ciphertext, decrypted) != 0) {
        printf("  FAIL: CBC decryption failed\n");
        return 0;
    }
    
    // 验证结果
    if (memcmp(plaintext, decrypted, 32) != 0) {
        printf("  FAIL: Decrypted text doesn't match original\n");
        return 0;
    }
    
    printf("  PASS: CBC mode working correctly\n\n");
    return 1;
}

// 测试CTR模式
static int test_sm4_ctr(void) {
    printf("Testing SM4 CTR mode...\n");
    
    uint8_t key[16] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10
    };
    
    uint8_t nonce_counter[16] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0a, 0x0b, 0x00, 0x00, 0x00, 0x01
    };
    
    uint8_t stream_block[16];
    size_t nc_off = 0;
    
    char plaintext[] = "Hello, SM4-CTR mode! This is a test message.";
    size_t text_len = strlen(plaintext);
    uint8_t *ciphertext = malloc(text_len);
    uint8_t *decrypted = malloc(text_len);
    
    if (ciphertext == NULL || decrypted == NULL) {
        printf("  FAIL: Memory allocation failed\n");
        free(ciphertext);
        free(decrypted);
        return 0;
    }
    
    sm4_context ctx;
    
    // 初始化上下文（CTR模式总是使用加密）
    if (sm4_init(&ctx, key, 1) != 0) {
        printf("  FAIL: Failed to initialize context\n");
        free(ciphertext);
        free(decrypted);
        return 0;
    }
    
    // CTR加密
    uint8_t nonce_counter_enc[16];
    memcpy(nonce_counter_enc, nonce_counter, 16);
    if (sm4_crypt_ctr(&ctx, text_len, &nc_off, nonce_counter_enc, stream_block, 
                      (const uint8_t*)plaintext, ciphertext) != 0) {
        printf("  FAIL: CTR encryption failed\n");
        free(ciphertext);
        free(decrypted);
        return 0;
    }
    
    // CTR解密（重置计数器）
    memcpy(nonce_counter_enc, nonce_counter, 16);
    nc_off = 0;
    if (sm4_crypt_ctr(&ctx, text_len, &nc_off, nonce_counter_enc, stream_block, 
                      ciphertext, decrypted) != 0) {
        printf("  FAIL: CTR decryption failed\n");
        free(ciphertext);
        free(decrypted);
        return 0;
    }
    
    // 验证结果
    if (memcmp(plaintext, decrypted, text_len) != 0) {
        printf("  FAIL: Decrypted text doesn't match original\n");
        free(ciphertext);
        free(decrypted);
        return 0;
    }
    
    printf("  PASS: CTR mode working correctly\n\n");
    free(ciphertext);
    free(decrypted);
    return 1;
}

// 测试优化实现
static int test_sm4_optimizations(void) {
    printf("Testing SM4 optimizations...\n");
    
    uint8_t key[16];
    generate_random_key(key);
    
    size_t test_size = 1024; // 1KB测试数据
    uint8_t *test_data = malloc(test_size);
    uint8_t *output_basic = malloc(test_size);
    uint8_t *output_opt = malloc(test_size);
    
    if (test_data == NULL || output_basic == NULL || output_opt == NULL) {
        printf("  FAIL: Memory allocation failed\n");
        free(test_data);
        free(output_basic);
        free(output_opt);
        return 0;
    }
    
    generate_random(test_data, test_size);
    
    // 基本实现
    sm4_context basic_ctx;
    if (sm4_init(&basic_ctx, key, 1) != 0) {
        printf("  FAIL: Failed to initialize basic context\n");
        free(test_data);
        free(output_basic);
        free(output_opt);
        return 0;
    }
    
    if (sm4_crypt_ecb(&basic_ctx, test_size, test_data, output_basic) != 0) {
        printf("  FAIL: Basic ECB encryption failed\n");
        free(test_data);
        free(output_basic);
        free(output_opt);
        return 0;
    }
    
    // 优化实现
    sm4_opt_context opt_ctx;
    if (sm4_opt_init(&opt_ctx, key, 1) != 0) {
        printf("  FAIL: Failed to initialize optimized context\n");
        free(test_data);
        free(output_basic);
        free(output_opt);
        return 0;
    }
    
    if (sm4_opt_crypt_ecb(&opt_ctx, test_size, test_data, output_opt) != 0) {
        printf("  FAIL: Optimized ECB encryption failed\n");
        free(test_data);
        free(output_basic);
        free(output_opt);
        return 0;
    }
    
    // 比较结果
    if (memcmp(output_basic, output_opt, test_size) != 0) {
        printf("  FAIL: Optimized result doesn't match basic implementation\n");
        free(test_data);
        free(output_basic);
        free(output_opt);
        return 0;
    }
    
    printf("  PASS: Optimized implementations produce correct results\n\n");
    
    // 显示CPU特性
    printf("  Detected CPU features:\n");
    printf("    SSE2:        %s\n", opt_ctx.features.has_sse2 ? "Yes" : "No");
    printf("    SSSE3:       %s\n", opt_ctx.features.has_ssse3 ? "Yes" : "No");
    printf("    AES-NI:      %s\n", opt_ctx.features.has_aesni ? "Yes" : "No");
    printf("    AVX:         %s\n", opt_ctx.features.has_avx ? "Yes" : "No");
    printf("    AVX2:        %s\n", opt_ctx.features.has_avx2 ? "Yes" : "No");
    printf("\n");
    
    free(test_data);
    free(output_basic);
    free(output_opt);
    return 1;
}

// 压力测试
static int test_sm4_stress(void) {
    printf("Running SM4 stress test...\n");
    
    uint8_t key[16];
    generate_random_key(key);
    
    sm4_context ctx;
    if (sm4_init(&ctx, key, 1) != 0) {
        printf("  FAIL: Failed to initialize context\n");
        return 0;
    }
    
    // 测试大量小块加密
    for (int i = 0; i < 1000; i++) {
        uint8_t plaintext[16];
        uint8_t ciphertext[16];
        uint8_t decrypted[16];
        
        generate_random(plaintext, 16);
        
        // 加密
        sm4_crypt_block(&ctx, plaintext, ciphertext);
        
        // 解密
        sm4_context dec_ctx;
        sm4_init(&dec_ctx, key, 0);
        sm4_crypt_block(&dec_ctx, ciphertext, decrypted);
        
        // 验证
        if (memcmp(plaintext, decrypted, 16) != 0) {
            printf("  FAIL: Mismatch at iteration %d\n", i);
            return 0;
        }
    }
    
    printf("  PASS: 1000 encryption/decryption cycles completed successfully\n\n");
    return 1;
}

int main(void) {
    printf("=== SM4 Implementation Test Suite ===\n\n");
    
    int tests_passed = 0;
    int total_tests = 6;
    
    // 运行所有测试
    tests_passed += test_sm4_basic();
    tests_passed += test_sm4_ecb();
    tests_passed += test_sm4_cbc();
    tests_passed += test_sm4_ctr();
    tests_passed += test_sm4_optimizations();
    tests_passed += test_sm4_stress();
    
    // 输出总结
    printf("=== Test Summary ===\n");
    printf("Tests passed: %d/%d\n", tests_passed, total_tests);
    
    if (tests_passed == total_tests) {
        printf("All tests PASSED! ✓\n");
        return 0;
    } else {
        printf("Some tests FAILED! ✗\n");
        return 1;
    }
}
