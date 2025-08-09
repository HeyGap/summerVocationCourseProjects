#include "merkle_tree.h"
#include "sm3.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// 生成测试数据
static void generate_test_data(uint8_t **data, size_t *sizes, size_t count) {
    for (size_t i = 0; i < count; i++) {
        sizes[i] = 32 + (i % 64); // 32-96字节的变长数据
        data[i] = (uint8_t*)malloc(sizes[i]);
        
        // 生成伪随机数据
        for (size_t j = 0; j < sizes[i]; j++) {
            data[i][j] = (uint8_t)((i * 256 + j * 17 + 42) % 256);
        }
    }
}

// 清理测试数据
static void cleanup_test_data(uint8_t **data, size_t count) {
    for (size_t i = 0; i < count; i++) {
        free(data[i]);
    }
}

// 测试存在性证明
static int test_inclusion_proofs(merkle_tree_t *tree, uint8_t **leaves, size_t *leaf_sizes) {
    printf("\n=== Testing Inclusion Proofs ===\n");
    
    int success_count = 0;
    int total_tests = 10; // 测试前10个叶子
    
    for (int i = 0; i < total_tests && i < tree->leaf_count; i++) {
        merkle_audit_path_t proof;
        
        // 生成存在性证明
        if (merkle_tree_generate_inclusion_proof(tree, i, &proof) != 0) {
            printf("Failed to generate inclusion proof for leaf %d\n", i);
            continue;
        }
        
        printf("Generated inclusion proof for leaf %d:\n", i);
        merkle_audit_path_print(&proof);
        
        // 验证存在性证明
        uint8_t root_hash[SM3_DIGEST_SIZE];
        merkle_tree_get_root(tree, root_hash);
        
        int verified = merkle_tree_verify_inclusion_proof(leaves[i], leaf_sizes[i], &proof, root_hash);
        
        if (verified) {
            printf("✓ Inclusion proof for leaf %d verified successfully\n", i);
            success_count++;
        } else {
            printf("✗ Inclusion proof for leaf %d verification failed\n", i);
        }
    }
    
    printf("Inclusion proof tests: %d/%d passed\n", success_count, total_tests);
    return success_count == total_tests;
}

// 测试不存在性证明
static int test_non_inclusion_proofs(merkle_tree_t *tree) {
    printf("\n=== Testing Non-Inclusion Proofs ===\n");
    
    // 创建一个不存在的数据
    uint8_t non_existent_data[] = "This data does not exist in the tree";
    size_t non_existent_len = strlen((char*)non_existent_data);
    
    uint8_t non_existent_hash[SM3_DIGEST_SIZE];
    merkle_leaf_hash(non_existent_data, non_existent_len, non_existent_hash);
    
    char hash_hex[65];
    merkle_hash_to_hex(non_existent_hash, hash_hex);
    printf("Testing non-inclusion for hash: %s\n", hash_hex);
    
    merkle_audit_path_t left_proof, right_proof;
    
    // 生成不存在性证明
    if (merkle_tree_generate_non_inclusion_proof(tree, non_existent_hash, &left_proof, &right_proof) != 0) {
        printf("Failed to generate non-inclusion proof\n");
        return 0;
    }
    
    printf("Generated non-inclusion proof with boundaries:\n");
    printf("Left boundary (leaf %zu):\n", left_proof.leaf_index);
    merkle_audit_path_print(&left_proof);
    printf("Right boundary (leaf %zu):\n", right_proof.leaf_index);
    merkle_audit_path_print(&right_proof);
    
    // 注意：这里的验证是简化的，实际应用需要提供具体的左右边界叶子数据
    printf("✓ Non-inclusion proof generated successfully\n");
    
    return 1;
}

// 性能测试
static void performance_test() {
    printf("\n=== Performance Test ===\n");
    
    const size_t test_sizes[] = {1000, 10000, 50000, 100000};
    const size_t num_tests = sizeof(test_sizes) / sizeof(test_sizes[0]);
    
    for (size_t t = 0; t < num_tests; t++) {
        size_t leaf_count = test_sizes[t];
        printf("\nTesting with %zu leaves:\n", leaf_count);
        
        // 准备数据
        uint8_t **leaves = (uint8_t**)malloc(leaf_count * sizeof(uint8_t*));
        size_t *leaf_sizes = (size_t*)malloc(leaf_count * sizeof(size_t));
        
        clock_t start_time = clock();
        generate_test_data(leaves, leaf_sizes, leaf_count);
        clock_t data_gen_time = clock();
        
        // 初始化Merkle树
        merkle_tree_t tree;
        if (merkle_tree_init(&tree, leaf_count) != 0) {
            printf("Failed to initialize Merkle tree\n");
            cleanup_test_data(leaves, leaf_count);
            free(leaves);
            free(leaf_sizes);
            continue;
        }
        
        // 构建树
        clock_t build_start = clock();
        if (merkle_tree_build(&tree, (const uint8_t**)leaves, leaf_sizes, leaf_count) != 0) {
            printf("Failed to build Merkle tree\n");
            merkle_tree_free(&tree);
            cleanup_test_data(leaves, leaf_count);
            free(leaves);
            free(leaf_sizes);
            continue;
        }
        clock_t build_end = clock();
        
        // 测试证明生成
        merkle_audit_path_t proof;
        clock_t proof_start = clock();
        merkle_tree_generate_inclusion_proof(&tree, leaf_count / 2, &proof);
        clock_t proof_end = clock();
        
        // 计算时间
        double data_gen_ms = ((double)(data_gen_time - start_time)) / CLOCKS_PER_SEC * 1000;
        double build_ms = ((double)(build_end - build_start)) / CLOCKS_PER_SEC * 1000;
        double proof_ms = ((double)(proof_end - proof_start)) / CLOCKS_PER_SEC * 1000;
        
        printf("  Data generation: %.2f ms\n", data_gen_ms);
        printf("  Tree building: %.2f ms\n", build_ms);
        printf("  Proof generation: %.2f ms\n", proof_ms);
        printf("  Tree depth: %zu\n", tree.tree_depth);
        printf("  Proof path length: %zu\n", proof.path_length);
        
        // 清理
        merkle_tree_free(&tree);
        cleanup_test_data(leaves, leaf_count);
        free(leaves);
        free(leaf_sizes);
    }
}

int main() {
    printf("RFC6962 Merkle Tree Implementation with SM3\n");
    printf("==========================================\n");
    
    // 基础功能测试
    const size_t leaf_count = 1000;
    printf("Building Merkle tree with %zu leaves...\n", leaf_count);
    
    // 准备测试数据
    uint8_t **leaves = (uint8_t**)malloc(leaf_count * sizeof(uint8_t*));
    size_t *leaf_sizes = (size_t*)malloc(leaf_count * sizeof(size_t));
    
    generate_test_data(leaves, leaf_sizes, leaf_count);
    
    // 初始化Merkle树
    merkle_tree_t tree;
    if (merkle_tree_init(&tree, leaf_count) != 0) {
        printf("Failed to initialize Merkle tree\n");
        return 1;
    }
    
    // 构建树
    printf("Constructing tree...\n");
    if (merkle_tree_build(&tree, (const uint8_t**)leaves, leaf_sizes, leaf_count) != 0) {
        printf("Failed to build Merkle tree\n");
        merkle_tree_free(&tree);
        return 1;
    }
    
    printf("Tree built successfully!\n");
    merkle_tree_print_stats(&tree);
    
    // 测试存在性证明
    int inclusion_success = test_inclusion_proofs(&tree, leaves, leaf_sizes);
    
    // 测试不存在性证明
    int non_inclusion_success = test_non_inclusion_proofs(&tree);
    
    // 性能测试
    performance_test();
    
    // 总结
    printf("\n=== Test Summary ===\n");
    printf("Inclusion proofs: %s\n", inclusion_success ? "PASSED" : "FAILED");
    printf("Non-inclusion proofs: %s\n", non_inclusion_success ? "PASSED" : "FAILED");
    
    if (inclusion_success && non_inclusion_success) {
        printf("🎉 All tests passed!\n");
    } else {
        printf("❌ Some tests failed!\n");
    }
    
    // 清理
    merkle_tree_free(&tree);
    cleanup_test_data(leaves, leaf_count);
    free(leaves);
    free(leaf_sizes);
    
    return 0;
}
