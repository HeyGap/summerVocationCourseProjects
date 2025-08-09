#include "merkle_tree.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

void test_small_tree() {
    printf("=== Testing Small Tree (5 leaves) ===\n");
    
    const char *test_leaves[] = {
        "leaf_0", "leaf_1", "leaf_2", "leaf_3", "leaf_4"
    };
    const uint8_t *leaves[5];
    size_t leaf_sizes[5];
    
    for (int i = 0; i < 5; i++) {
        leaves[i] = (const uint8_t*)test_leaves[i];
        leaf_sizes[i] = strlen(test_leaves[i]);
    }
    
    // 构建树
    merkle_tree_t tree;
    merkle_tree_init(&tree, 5);
    merkle_tree_build(&tree, leaves, leaf_sizes, 5);
    merkle_tree_print_stats(&tree);
    
    // 测试所有包含性证明
    int passed = 0;
    for (size_t i = 0; i < 5; i++) {
        merkle_audit_path_t proof;
        merkle_tree_generate_inclusion_proof(&tree, i, &proof);
        
        int verified = merkle_tree_verify_inclusion_proof(
            leaves[i], leaf_sizes[i], &proof, tree.root_hash);
        
        if (verified) passed++;
        printf("Leaf %zu: %s\n", i, verified ? "PASS" : "FAIL");
    }
    
    printf("Inclusion proof test: %d/5 passed\n\n", passed);
    merkle_tree_free(&tree);
}

void test_large_tree() {
    printf("=== Testing Large Tree (100,000 leaves) ===\n");
    
    const size_t leaf_count = 100000;
    const uint8_t **leaves = malloc(leaf_count * sizeof(uint8_t*));
    size_t *leaf_sizes = malloc(leaf_count * sizeof(size_t));
    
    // 生成叶子数据
    for (size_t i = 0; i < leaf_count; i++) {
        char buffer[32];
        snprintf(buffer, sizeof(buffer), "leaf_%zu", i);
        
        leaf_sizes[i] = strlen(buffer);
        leaves[i] = malloc(leaf_sizes[i]);
        memcpy((void*)leaves[i], buffer, leaf_sizes[i]);
    }
    
    printf("Generated %zu leaves\n", leaf_count);
    
    // 构建树（计时）
    clock_t start = clock();
    merkle_tree_t tree;
    merkle_tree_init(&tree, leaf_count);
    merkle_tree_build(&tree, leaves, leaf_sizes, leaf_count);
    clock_t end = clock();
    
    double build_time = ((double)(end - start)) / CLOCKS_PER_SEC;
    merkle_tree_print_stats(&tree);
    printf("Tree build time: %.3f seconds\n", build_time);
    
    // 测试随机位置的包含性证明
    printf("Testing random inclusion proofs...\n");
    srand(42);
    int test_count = 10;
    int passed = 0;
    
    start = clock();
    for (int i = 0; i < test_count; i++) {
        size_t test_index = rand() % leaf_count;
        
        merkle_audit_path_t proof;
        merkle_tree_generate_inclusion_proof(&tree, test_index, &proof);
        
        int verified = merkle_tree_verify_inclusion_proof(
            leaves[test_index], leaf_sizes[test_index], &proof, tree.root_hash);
        
        if (verified) passed++;
        printf("Test %d (leaf %zu): %s\n", i+1, test_index, verified ? "PASS" : "FAIL");
    }
    end = clock();
    
    double proof_time = ((double)(end - start)) / CLOCKS_PER_SEC;
    printf("Random proof tests: %d/%d passed\n", passed, test_count);
    printf("Proof generation+verification time: %.6f seconds per proof\n", 
           proof_time / test_count);
    
    // 清理内存
    for (size_t i = 0; i < leaf_count; i++) {
        free((void*)leaves[i]);
    }
    free(leaves);
    free(leaf_sizes);
    merkle_tree_free(&tree);
    printf("\n");
}

void test_non_inclusion() {
    printf("=== Testing Non-inclusion Proof ===\n");
    
    const char *test_leaves[] = {"A", "B", "C", "D", "E"};
    const uint8_t *leaves[5];
    size_t leaf_sizes[5];
    
    for (int i = 0; i < 5; i++) {
        leaves[i] = (const uint8_t*)test_leaves[i];
        leaf_sizes[i] = strlen(test_leaves[i]);
    }
    
    merkle_tree_t tree;
    merkle_tree_init(&tree, 5);
    merkle_tree_build(&tree, leaves, leaf_sizes, 5);
    
    // 生成不存在性证明（使用边界叶子）
    uint8_t target_hash[SM3_DIGEST_SIZE];
    merkle_leaf_hash((const uint8_t*)"NON_EXISTENT", 12, target_hash);
    
    merkle_audit_path_t left_proof, right_proof;
    merkle_tree_generate_non_inclusion_proof(&tree, target_hash, &left_proof, &right_proof);
    
    int verified = merkle_tree_verify_non_inclusion_proof(
        target_hash,
        leaves[0], leaf_sizes[0], &left_proof,
        leaves[4], leaf_sizes[4], &right_proof,
        tree.root_hash
    );
    
    printf("Non-inclusion proof for 'NON_EXISTENT': %s\n", verified ? "PASS" : "FAIL");
    
    merkle_tree_free(&tree);
    printf("\n");
}

int main() {
    printf("Merkle Tree Implementation Test Suite\n");
    printf("=====================================\n\n");
    
    test_small_tree();
    test_large_tree();
    test_non_inclusion();
    
    printf("All tests completed!\n");
    return 0;
}
