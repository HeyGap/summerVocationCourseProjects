#include "merkle_tree.h"
#include "sm3.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// 简单验证测试
int main() {
    printf("RFC6962 Merkle Tree Verification Test\n");
    printf("=====================================\n");
    
    // 创建测试数据
    const char* test_data[] = {
        "Hello",
        "World", 
        "Merkle",
        "Tree",
        "Test"
    };
    size_t data_count = sizeof(test_data) / sizeof(test_data[0]);
    
    printf("Building Merkle tree with %zu leaves...\n", data_count);
    
    // 准备输入
    const uint8_t **leaves = malloc(data_count * sizeof(uint8_t*));
    size_t *leaf_sizes = malloc(data_count * sizeof(size_t));
    
    for (size_t i = 0; i < data_count; i++) {
        leaves[i] = (const uint8_t*)test_data[i];
        leaf_sizes[i] = strlen(test_data[i]);
    }
    
    // 构建树
    merkle_tree_t tree;
    if (merkle_tree_init(&tree, data_count) != 0) {
        printf("Failed to initialize tree\n");
        return 1;
    }
    
    if (merkle_tree_build(&tree, leaves, leaf_sizes, data_count) != 0) {
        printf("Failed to build tree\n");
        return 1;
    }
    
    printf("Tree built successfully!\n");
    merkle_tree_print_stats(&tree);
    
    // 测试存在性证明
    printf("\nTesting inclusion proofs:\n");
    int all_passed = 1;
    
    for (size_t i = 0; i < data_count; i++) {
        printf("Testing leaf %zu: \"%s\"\n", i, test_data[i]);
        
        // 生成证明
        merkle_audit_path_t proof;
        if (merkle_tree_generate_inclusion_proof(&tree, i, &proof) != 0) {
            printf("  Failed to generate proof\n");
            all_passed = 0;
            continue;
        }
        
        // 验证证明
        uint8_t root_hash[SM3_DIGEST_SIZE];
        merkle_tree_get_root(&tree, root_hash);
        
        int verified = merkle_tree_verify_inclusion_proof(
            leaves[i], leaf_sizes[i], &proof, root_hash);
        
        if (verified) {
            printf("  Proof verified successfully! Path length: %zu\n", proof.path_length);
        } else {
            printf("  Proof verification FAILED!\n");
            all_passed = 0;
        }
    }
    
    // 测试不存在性证明
    printf("\nTesting non-inclusion proof:\n");
    const char* non_existent = "NotInTree";
    uint8_t target_hash[SM3_DIGEST_SIZE];
    merkle_leaf_hash((const uint8_t*)non_existent, strlen(non_existent), target_hash);
    
    merkle_audit_path_t left_proof, right_proof;
    if (merkle_tree_generate_non_inclusion_proof(&tree, target_hash, &left_proof, &right_proof) == 0) {
        printf("Non-inclusion proof generated successfully\n");
        printf("Left boundary: leaf %zu\n", left_proof.leaf_index);
        printf("Right boundary: leaf %zu\n", right_proof.leaf_index);
    } else {
        printf("Failed to generate non-inclusion proof\n");
        all_passed = 0;
    }
    
    // 总结
    printf("\n=== Test Results ===\n");
    if (all_passed) {
        printf("All tests PASSED!\n");
        printf("Merkle tree implementation is CORRECT\n");
    } else {
        printf("Some tests FAILED!\n");
        printf("Implementation needs fixes\n");
    }
    
    // 性能测试
    printf("\n=== Performance Test ===\n");
    const size_t perf_sizes[] = {10, 100, 1000, 10000};
    const size_t perf_count = sizeof(perf_sizes) / sizeof(perf_sizes[0]);
    
    printf("Scale      Build(ms)  Proof(ms)  Depth\n");
    printf("---------- ---------- ---------- -----\n");
    
    for (size_t t = 0; t < perf_count; t++) {
        size_t size = perf_sizes[t];
        
        // 创建测试数据
        const uint8_t **perf_leaves = malloc(size * sizeof(uint8_t*));
        size_t *perf_sizes_arr = malloc(size * sizeof(size_t));
        
        for (size_t i = 0; i < size; i++) {
            static char buffer[32];
            snprintf(buffer, sizeof(buffer), "data_%zu", i);
            perf_sizes_arr[i] = strlen(buffer) + 1;
            perf_leaves[i] = malloc(perf_sizes_arr[i]);
            memcpy((void*)perf_leaves[i], buffer, perf_sizes_arr[i]);
        }
        
        merkle_tree_t perf_tree;
        merkle_tree_init(&perf_tree, size);
        
        // 测量构建时间
        clock_t start = clock();
        merkle_tree_build(&perf_tree, perf_leaves, perf_sizes_arr, size);
        clock_t build_time = clock() - start;
        
        // 测量证明生成时间
        merkle_audit_path_t perf_proof;
        start = clock();
        merkle_tree_generate_inclusion_proof(&perf_tree, size/2, &perf_proof);
        clock_t proof_time = clock() - start;
        
        double build_ms = ((double)build_time / CLOCKS_PER_SEC) * 1000;
        double proof_ms = ((double)proof_time / CLOCKS_PER_SEC) * 1000;
        
        printf("%-10zu %-10.2f %-10.2f %-5zu\n", size, build_ms, proof_ms, perf_tree.tree_depth);
        
        // 清理
        merkle_tree_free(&perf_tree);
        for (size_t i = 0; i < size; i++) {
            free((void*)perf_leaves[i]);
        }
        free(perf_leaves);
        free(perf_sizes_arr);
    }
    
    // 清理
    merkle_tree_free(&tree);
    free(leaves);
    free(leaf_sizes);
    
    return all_passed ? 0 : 1;
}
