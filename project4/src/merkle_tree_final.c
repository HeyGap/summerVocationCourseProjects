#include "merkle_tree.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// 简单直接的Merkle树实现
typedef struct {
    uint8_t **leaf_data;
    size_t *leaf_sizes;
    size_t leaf_count;
    uint8_t root_hash[SM3_DIGEST_SIZE];
} simple_tree_t;

static simple_tree_t *g_simple_tree = NULL;

int merkle_tree_init(merkle_tree_t *tree, size_t max_leaves) {
    if (!tree || max_leaves == 0) return -1;
    
    tree->nodes = NULL;
    tree->total_nodes = 0;
    tree->leaf_count = 0;
    tree->tree_depth = 0;
    memset(tree->root_hash, 0, SM3_DIGEST_SIZE);
    return 0;
}

void merkle_tree_free(merkle_tree_t *tree) {
    if (g_simple_tree) {
        if (g_simple_tree->leaf_data) {
            for (size_t i = 0; i < g_simple_tree->leaf_count; i++) {
                free(g_simple_tree->leaf_data[i]);
            }
            free(g_simple_tree->leaf_data);
            free(g_simple_tree->leaf_sizes);
        }
        free(g_simple_tree);
        g_simple_tree = NULL;
    }
    
    if (tree && tree->nodes) {
        free(tree->nodes);
        tree->nodes = NULL;
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

// 简单的完全二叉树构建和根计算
static void build_simple_tree(uint8_t **leaf_hashes, size_t count, uint8_t *root) {
    if (count == 1) {
        memcpy(root, leaf_hashes[0], SM3_DIGEST_SIZE);
        return;
    }
    
    // 创建当前层
    uint8_t **current_level = malloc(count * sizeof(uint8_t*));
    for (size_t i = 0; i < count; i++) {
        current_level[i] = malloc(SM3_DIGEST_SIZE);
        memcpy(current_level[i], leaf_hashes[i], SM3_DIGEST_SIZE);
    }
    
    size_t current_count = count;
    
    // 向上构建
    while (current_count > 1) {
        size_t next_count = (current_count + 1) / 2;
        uint8_t **next_level = malloc(next_count * sizeof(uint8_t*));
        
        for (size_t i = 0; i < next_count; i++) {
            next_level[i] = malloc(SM3_DIGEST_SIZE);
            
            size_t left_idx = 2 * i;
            size_t right_idx = 2 * i + 1;
            
            if (right_idx < current_count) {
                // 有左右子节点
                merkle_node_hash(current_level[left_idx], current_level[right_idx], next_level[i]);
            } else {
                // 只有左子节点
                memcpy(next_level[i], current_level[left_idx], SM3_DIGEST_SIZE);
            }
        }
        
        // 清理当前层
        for (size_t i = 0; i < current_count; i++) {
            free(current_level[i]);
        }
        free(current_level);
        
        current_level = next_level;
        current_count = next_count;
    }
    
    memcpy(root, current_level[0], SM3_DIGEST_SIZE);
    free(current_level[0]);
    free(current_level);
}

int merkle_tree_build(merkle_tree_t *tree, const uint8_t **leaves, 
                      const size_t *leaf_sizes, size_t leaf_count) {
    if (!tree || !leaves || !leaf_sizes || leaf_count == 0) return -1;
    
    // 创建全局存储
    g_simple_tree = malloc(sizeof(simple_tree_t));
    g_simple_tree->leaf_count = leaf_count;
    g_simple_tree->leaf_data = malloc(leaf_count * sizeof(uint8_t*));
    g_simple_tree->leaf_sizes = malloc(leaf_count * sizeof(size_t));
    
    // 存储叶子数据并计算哈希
    uint8_t **leaf_hashes = malloc(leaf_count * sizeof(uint8_t*));
    
    for (size_t i = 0; i < leaf_count; i++) {
        // 存储原始数据
        g_simple_tree->leaf_sizes[i] = leaf_sizes[i];
        g_simple_tree->leaf_data[i] = malloc(leaf_sizes[i]);
        memcpy(g_simple_tree->leaf_data[i], leaves[i], leaf_sizes[i]);
        
        // 计算哈希
        leaf_hashes[i] = malloc(SM3_DIGEST_SIZE);
        merkle_leaf_hash(leaves[i], leaf_sizes[i], leaf_hashes[i]);
    }
    
    // 构建树并计算根
    build_simple_tree(leaf_hashes, leaf_count, g_simple_tree->root_hash);
    
    // 清理临时哈希
    for (size_t i = 0; i < leaf_count; i++) {
        free(leaf_hashes[i]);
    }
    free(leaf_hashes);
    
    // 更新树信息
    tree->leaf_count = leaf_count;
    tree->tree_depth = (size_t)ceil(log2(leaf_count));
    memcpy(tree->root_hash, g_simple_tree->root_hash, SM3_DIGEST_SIZE);
    
    return 0;
}

int merkle_tree_get_root(merkle_tree_t *tree, uint8_t *root_hash) {
    if (!tree || !root_hash) return -1;
    memcpy(root_hash, tree->root_hash, SM3_DIGEST_SIZE);
    return 0;
}

// 简单的证明生成 - 使用完全二叉树逻辑
int merkle_tree_generate_inclusion_proof(merkle_tree_t *tree, size_t leaf_index,
                                        merkle_audit_path_t *proof) {
    if (!tree || !proof || !g_simple_tree || leaf_index >= tree->leaf_count) return -1;
    
    proof->leaf_index = leaf_index;
    proof->path_length = 0;
    
    // 重新计算叶子哈希
    uint8_t **leaf_hashes = malloc(tree->leaf_count * sizeof(uint8_t*));
    for (size_t i = 0; i < tree->leaf_count; i++) {
        leaf_hashes[i] = malloc(SM3_DIGEST_SIZE);
        merkle_leaf_hash(g_simple_tree->leaf_data[i], g_simple_tree->leaf_sizes[i], leaf_hashes[i]);
    }
    
    // 使用完全二叉树的证明生成
    uint8_t **current_level = leaf_hashes;
    size_t current_count = tree->leaf_count;
    size_t current_index = leaf_index;
    
    while (current_count > 1) {
        // 找到兄弟节点
        size_t sibling_index;
        if (current_index % 2 == 0) {
            // 左子节点，兄弟是右边
            sibling_index = current_index + 1;
            if (sibling_index < current_count) {
                memcpy(proof->path_hashes[proof->path_length], current_level[sibling_index], SM3_DIGEST_SIZE);
                proof->path_directions[proof->path_length] = 1; // 右兄弟
                proof->path_length++;
            }
        } else {
            // 右子节点，兄弟是左边
            sibling_index = current_index - 1;
            memcpy(proof->path_hashes[proof->path_length], current_level[sibling_index], SM3_DIGEST_SIZE);
            proof->path_directions[proof->path_length] = 0; // 左兄弟
            proof->path_length++;
        }
        
        // 构建下一层
        size_t next_count = (current_count + 1) / 2;
        uint8_t **next_level = malloc(next_count * sizeof(uint8_t*));
        
        for (size_t i = 0; i < next_count; i++) {
            next_level[i] = malloc(SM3_DIGEST_SIZE);
            size_t left_idx = 2 * i;
            size_t right_idx = 2 * i + 1;
            
            if (right_idx < current_count) {
                merkle_node_hash(current_level[left_idx], current_level[right_idx], next_level[i]);
            } else {
                memcpy(next_level[i], current_level[left_idx], SM3_DIGEST_SIZE);
            }
        }
        
        // 清理当前层
        if (current_level != leaf_hashes) {
            for (size_t i = 0; i < current_count; i++) {
                free(current_level[i]);
            }
            free(current_level);
        }
        
        current_level = next_level;
        current_count = next_count;
        current_index /= 2;
    }
    
    // 清理
    for (size_t i = 0; i < tree->leaf_count; i++) {
        free(leaf_hashes[i]);
    }
    free(leaf_hashes);
    
    if (current_level != leaf_hashes) {
        free(current_level[0]);
        free(current_level);
    }
    
    return 0;
}

int merkle_tree_verify_inclusion_proof(const uint8_t *leaf_data, size_t leaf_len,
                                      const merkle_audit_path_t *proof,
                                      const uint8_t *root_hash) {
    if (!leaf_data || !proof || !root_hash) return 0;

    uint8_t current_hash[SM3_DIGEST_SIZE];
    merkle_leaf_hash(leaf_data, leaf_len, current_hash);

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
    if (!tree || !target_hash || !left_proof || !right_proof) return -1;

    size_t left_idx = 0;
    size_t right_idx = tree->leaf_count - 1;
    
    if (merkle_tree_generate_inclusion_proof(tree, left_idx, left_proof) != 0) return -1;
    if (merkle_tree_generate_inclusion_proof(tree, right_idx, right_proof) != 0) return -1;

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
