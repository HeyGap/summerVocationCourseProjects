#include "merkle_tree.h"
#include "sm3.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 手动验证Merkle树的正确性
void manual_verification() {
    printf("Manual Merkle Tree Verification\n");
    printf("===============================\n");
    
    // 简单的3个叶子例子
    const char* data[] = {"A", "B", "C"};
    uint8_t hashes[3][32];
    
    // 计算叶子哈希
    for (int i = 0; i < 3; i++) {
        merkle_leaf_hash((const uint8_t*)data[i], 1, hashes[i]);
        
        char hex[65];
        merkle_hash_to_hex(hashes[i], hex);
        printf("Leaf %d (\"%s\"): %s\n", i, data[i], hex);
    }
    
    // 手动计算内部节点
    uint8_t node_ab[32], node_c[32], root[32];
    
    // AB节点 = hash(0x01 || hash_A || hash_B)
    merkle_node_hash(hashes[0], hashes[1], node_ab);
    char hex_ab[65];
    merkle_hash_to_hex(node_ab, hex_ab);
    printf("Node AB: %s\n", hex_ab);
    
    // 按照RFC6962，C只有一个节点，所以直接复制
    memcpy(node_c, hashes[2], 32);
    char hex_c[65];
    merkle_hash_to_hex(node_c, hex_c);
    printf("Node C: %s\n", hex_c);
    
    // 根节点 = hash(0x01 || node_AB || node_C)
    merkle_node_hash(node_ab, node_c, root);
    char hex_root[65];
    merkle_hash_to_hex(root, hex_root);
    printf("Root: %s\n", hex_root);
    
    // 手动验证叶子A的证明
    printf("\nManual proof verification for leaf A:\n");
    printf("1. Start with leaf A hash: %s\n", hex_ab);
    
    // A的审计路径应该是: [hash_B, node_C]
    char hex_b[65];
    merkle_hash_to_hex(hashes[1], hex_b);
    printf("2. Combine with sibling B: %s\n", hex_b);
    
    uint8_t step1[32];
    merkle_node_hash(hashes[0], hashes[1], step1);
    char hex_step1[65];
    merkle_hash_to_hex(step1, hex_step1);
    printf("3. Result: %s\n", hex_step1);
    
    printf("4. Combine with sibling C: %s\n", hex_c);
    uint8_t step2[32];
    merkle_node_hash(step1, node_c, step2);
    char hex_step2[65];
    merkle_hash_to_hex(step2, hex_step2);
    printf("5. Final result: %s\n", hex_step2);
    
    if (memcmp(step2, root, 32) == 0) {
        printf("Manual verification PASSED!\n");
    } else {
        printf("Manual verification FAILED!\n");
    }
}

int main() {
    manual_verification();
    return 0;
}
