#include "merkle_tree.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    // 测试5个叶子节点
    const char *test_leaves[] = {
        "leaf_0", "leaf_1", "leaf_2", "leaf_3", "leaf_4"
    };
    const uint8_t *leaves[5];
    size_t leaf_sizes[5];
    
    for (int i = 0; i < 5; i++) {
        leaves[i] = (const uint8_t*)test_leaves[i];
        leaf_sizes[i] = strlen(test_leaves[i]);
    }
    
    // 初始化和构建树
    merkle_tree_t tree;
    if (merkle_tree_init(&tree, 5) != 0) {
        printf("Failed to init tree\n");
        return 1;
    }
    
    if (merkle_tree_build(&tree, leaves, leaf_sizes, 5) != 0) {
        printf("Failed to build tree\n");
        return 1;
    }
    
    merkle_tree_print_stats(&tree);
    
    // 测试所有叶子的包含性证明
    printf("\nTesting inclusion proofs...\n");
    for (size_t i = 0; i < 5; i++) {
        merkle_audit_path_t proof;
        
        if (merkle_tree_generate_inclusion_proof(&tree, i, &proof) != 0) {
            printf("Failed to generate proof for leaf %zu\n", i);
            continue;
        }
        
        int verified = merkle_tree_verify_inclusion_proof(
            leaves[i], leaf_sizes[i], &proof, tree.root_hash);
        
        printf("Leaf %zu: %s\n", i, verified ? "PASSED" : "FAILED");
        
        if (i == 0) {
            printf("  Proof details for leaf 0:\n");
            merkle_audit_path_print(&proof);
        }
    }
    
    merkle_tree_free(&tree);
    return 0;
}
