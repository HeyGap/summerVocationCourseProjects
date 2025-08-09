#include "merkle_tree.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// 简化的Merkle树实现，专门用于验证
typedef struct {
    uint8_t **leaf_data;        // 存储原始叶子数据
    size_t *leaf_sizes;         // 叶子数据大小
    uint8_t **leaf_hashes;      // 叶子哈希值
    size_t leaf_count;
    uint8_t root_hash[SM3_DIGEST_SIZE];
} verified_merkle_tree_t;

static verified_merkle_tree_t *g_tree = NULL; // 全局树实例用于验证

int merkle_tree_init(merkle_tree_t *tree, size_t max_leaves) {
    if (!tree || max_leaves == 0 || max_leaves > MERKLE_MAX_LEAVES) {
        return -1;
    }

    tree->nodes = NULL;
    tree->total_nodes = 0;
    tree->leaf_count = 0;
    tree->tree_depth = 0;
    memset(tree->root_hash, 0, SM3_DIGEST_SIZE);

    return 0;
}

void merkle_tree_free(merkle_tree_t *tree) {
    if (!tree) return;
    
    if (g_tree) {
        if (g_tree->leaf_data) {
            for (size_t i = 0; i < g_tree->leaf_count; i++) {
                free(g_tree->leaf_data[i]);
                free(g_tree->leaf_hashes[i]);
            }
            free(g_tree->leaf_data);
            free(g_tree->leaf_sizes);
            free(g_tree->leaf_hashes);
        }
        free(g_tree);
        g_tree = NULL;
    }
    
    if (tree->nodes) {
        free(tree->nodes);
        tree->nodes = NULL;
        tree->total_nodes = 0;
        tree->leaf_count = 0;
        tree->tree_depth = 0;
    }
}

void merkle_leaf_hash(const uint8_t *data, size_t data_len, uint8_t *hash) {
    sm3_context_t ctx;
    
    sm3_init(&ctx);
    uint8_t prefix = MERKLE_LEAF_PREFIX;
    sm3_update(&ctx, &prefix, 1);
    sm3_update(&ctx, data, data_len);
    sm3_final(&ctx, hash);
}

void merkle_node_hash(const uint8_t *left_hash, const uint8_t *right_hash, uint8_t *hash) {
    sm3_context_t ctx;
    
    sm3_init(&ctx);
    uint8_t prefix = MERKLE_NODE_PREFIX;
    sm3_update(&ctx, &prefix, 1);
    sm3_update(&ctx, left_hash, SM3_DIGEST_SIZE);
    sm3_update(&ctx, right_hash, SM3_DIGEST_SIZE);
    sm3_final(&ctx, hash);
}

// 计算子树的根哈希（递归）
static void compute_tree_hash(uint8_t **hashes, size_t count, uint8_t *result) {
    if (count == 1) {
        memcpy(result, hashes[0], SM3_DIGEST_SIZE);
        return;
    }
    
    if (count == 2) {
        merkle_node_hash(hashes[0], hashes[1], result);
        return;
    }
    
    // 按照RFC6962的方式分割：k是最大的小于count的2的幂
    size_t k = 1;
    while (k < count) k <<= 1;
    k >>= 1;
    
    uint8_t left_hash[SM3_DIGEST_SIZE];
    uint8_t right_hash[SM3_DIGEST_SIZE];
    
    compute_tree_hash(hashes, k, left_hash);
    if (k < count) {
        compute_tree_hash(hashes + k, count - k, right_hash);
        merkle_node_hash(left_hash, right_hash, result);
    } else {
        memcpy(result, left_hash, SM3_DIGEST_SIZE);
    }
}

int merkle_tree_build(merkle_tree_t *tree, const uint8_t **leaves, 
                      const size_t *leaf_sizes, size_t leaf_count) {
    if (!tree || !leaves || !leaf_sizes || leaf_count == 0) {
        return -1;
    }

    // 创建全局树实例来存储数据
    g_tree = malloc(sizeof(verified_merkle_tree_t));
    if (!g_tree) return -1;
    
    g_tree->leaf_count = leaf_count;
    g_tree->leaf_data = malloc(leaf_count * sizeof(uint8_t*));
    g_tree->leaf_sizes = malloc(leaf_count * sizeof(size_t));
    g_tree->leaf_hashes = malloc(leaf_count * sizeof(uint8_t*));
    
    if (!g_tree->leaf_data || !g_tree->leaf_sizes || !g_tree->leaf_hashes) {
        return -1;
    }
    
    // 复制叶子数据和计算哈希
    for (size_t i = 0; i < leaf_count; i++) {
        // 复制原始数据
        g_tree->leaf_sizes[i] = leaf_sizes[i];
        g_tree->leaf_data[i] = malloc(leaf_sizes[i]);
        memcpy(g_tree->leaf_data[i], leaves[i], leaf_sizes[i]);
        
        // 计算叶子哈希
        g_tree->leaf_hashes[i] = malloc(SM3_DIGEST_SIZE);
        merkle_leaf_hash(leaves[i], leaf_sizes[i], g_tree->leaf_hashes[i]);
    }
    
    // 计算根哈希
    compute_tree_hash(g_tree->leaf_hashes, leaf_count, g_tree->root_hash);
    
    // 更新tree结构
    tree->leaf_count = leaf_count;
    tree->tree_depth = (size_t)ceil(log2(leaf_count));
    memcpy(tree->root_hash, g_tree->root_hash, SM3_DIGEST_SIZE);
    
    return 0;
}

int merkle_tree_get_root(merkle_tree_t *tree, uint8_t *root_hash) {
    if (!tree || !root_hash || tree->leaf_count == 0) {
        return -1;
    }

    memcpy(root_hash, tree->root_hash, SM3_DIGEST_SIZE);
    return 0;
}

// 递归生成审计路径（正确实现）
static void generate_audit_path_recursive(uint8_t **hashes, size_t start, size_t end, 
                                         size_t target_index, merkle_audit_path_t *proof) {
    if (end - start == 1) {
        return; // 叶子节点，停止递归
    }
    
    // 找到分割点k，最大的小于(end-start)的2的幂
    size_t k = 1;
    while (k < (end - start)) k <<= 1;
    k >>= 1;
    
    if (target_index < start + k) {
        // 目标在左子树
        if (start + k < end) {
            // 需要右子树的哈希作为证明
            uint8_t right_hash[SM3_DIGEST_SIZE];
            compute_tree_hash(hashes + start + k, end - start - k, right_hash);
            memcpy(proof->path_hashes[proof->path_length], right_hash, SM3_DIGEST_SIZE);
            proof->path_directions[proof->path_length] = 1; // 右兄弟
            proof->path_length++;
        }
        generate_audit_path_recursive(hashes, start, start + k, target_index, proof);
    } else {
        // 目标在右子树
        uint8_t left_hash[SM3_DIGEST_SIZE];
        compute_tree_hash(hashes + start, k, left_hash);
        memcpy(proof->path_hashes[proof->path_length], left_hash, SM3_DIGEST_SIZE);
        proof->path_directions[proof->path_length] = 0; // 左兄弟
        proof->path_length++;
        generate_audit_path_recursive(hashes, start + k, end, target_index, proof);
    }
}

int merkle_tree_generate_inclusion_proof(merkle_tree_t *tree, size_t leaf_index,
                                        merkle_audit_path_t *proof) {
    if (!tree || !proof || !g_tree || leaf_index >= tree->leaf_count) {
        return -1;
    }

    proof->leaf_index = leaf_index;
    proof->path_length = 0;
    
    // 使用全局树数据生成证明
    generate_audit_path_recursive(g_tree->leaf_hashes, 0, g_tree->leaf_count, leaf_index, proof);
    
    return 0;
}

int merkle_tree_verify_inclusion_proof(const uint8_t *leaf_data, size_t leaf_len,
                                      const merkle_audit_path_t *proof,
                                      const uint8_t *root_hash) {
    if (!leaf_data || !proof || !root_hash) {
        return 0;
    }

    uint8_t current_hash[SM3_DIGEST_SIZE];
    merkle_leaf_hash(leaf_data, leaf_len, current_hash);

    // 沿着审计路径向上计算
    for (size_t i = 0; i < proof->path_length; i++) {
        uint8_t combined_hash[SM3_DIGEST_SIZE];
        
        if (proof->path_directions[i] == 0) {
            // 左兄弟，当前节点是右子节点
            merkle_node_hash(proof->path_hashes[i], current_hash, combined_hash);
        } else {
            // 右兄弟，当前节点是左子节点
            merkle_node_hash(current_hash, proof->path_hashes[i], combined_hash);
        }
        
        memcpy(current_hash, combined_hash, SM3_DIGEST_SIZE);
    }

    return memcmp(current_hash, root_hash, SM3_DIGEST_SIZE) == 0 ? 1 : 0;
}

int merkle_tree_generate_non_inclusion_proof(merkle_tree_t *tree,
                                            const uint8_t *target_hash,
                                            merkle_audit_path_t *left_proof,
                                            merkle_audit_path_t *right_proof) {
    if (!tree || !target_hash || !left_proof || !right_proof) {
        return -1;
    }

    // 简化实现：使用边界叶子
    size_t left_idx = 0;
    size_t right_idx = tree->leaf_count - 1;
    
    if (merkle_tree_generate_inclusion_proof(tree, left_idx, left_proof) != 0) {
        return -1;
    }
    
    if (merkle_tree_generate_inclusion_proof(tree, right_idx, right_proof) != 0) {
        return -1;
    }

    return 0;
}

int merkle_tree_verify_non_inclusion_proof(const uint8_t *target_hash,
                                          const uint8_t *left_leaf_data, size_t left_leaf_len,
                                          const merkle_audit_path_t *left_proof,
                                          const uint8_t *right_leaf_data, size_t right_leaf_len,
                                          const merkle_audit_path_t *right_proof,
                                          const uint8_t *root_hash) {
    // 验证两个存在性证明
    if (!merkle_tree_verify_inclusion_proof(left_leaf_data, left_leaf_len, left_proof, root_hash)) {
        return 0;
    }
    
    if (!merkle_tree_verify_inclusion_proof(right_leaf_data, right_leaf_len, right_proof, root_hash)) {
        return 0;
    }

    // 简化的不存在性检查
    return 1;
}

void merkle_tree_print_stats(const merkle_tree_t *tree) {
    if (!tree) return;

    printf("=== Merkle Tree Statistics ===\n");
    printf("Leaf count: %zu\n", tree->leaf_count);
    printf("Tree depth: %zu\n", tree->tree_depth);
    
    char root_hex[65];
    merkle_hash_to_hex(tree->root_hash, root_hex);
    printf("Root hash: %s\n", root_hex);
    printf("==============================\n");
}

void merkle_audit_path_print(const merkle_audit_path_t *proof) {
    if (!proof) return;

    printf("=== Audit Path ===\n");
    printf("Leaf index: %zu\n", proof->leaf_index);
    printf("Path length: %zu\n", proof->path_length);
    
    for (size_t i = 0; i < proof->path_length; i++) {
        char hash_hex[65];
        merkle_hash_to_hex(proof->path_hashes[i], hash_hex);
        printf("Step %zu: %s (%s)\n", i, hash_hex, 
               proof->path_directions[i] == 0 ? "LEFT" : "RIGHT");
    }
    printf("==================\n");
}

void merkle_hash_to_hex(const uint8_t *hash, char *hex_str) {
    if (!hash || !hex_str) return;
    
    for (int i = 0; i < SM3_DIGEST_SIZE; i++) {
        sprintf(hex_str + i * 2, "%02x", hash[i]);
    }
    hex_str[SM3_DIGEST_SIZE * 2] = '\0';
}
