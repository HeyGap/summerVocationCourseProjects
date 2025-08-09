#ifndef MERKLE_TREE_H
#define MERKLE_TREE_H

#include <stdint.h>
#include <stddef.h>
#include "sm3.h"

#ifdef __cplusplus
extern "C" {
#endif

// RFC6962定义的域分离前缀
#define MERKLE_LEAF_PREFIX      0x00
#define MERKLE_NODE_PREFIX      0x01

// Merkle树最大深度（支持100万个叶子节点）
#define MERKLE_MAX_DEPTH        20
#define MERKLE_MAX_LEAVES       100000

// Merkle树节点结构
typedef struct {
    uint8_t hash[SM3_DIGEST_SIZE];
    int is_leaf;
    int level;
} merkle_node_t;

// Merkle树结构
typedef struct {
    merkle_node_t *nodes;           // 节点数组
    size_t total_nodes;             // 总节点数
    size_t leaf_count;              // 叶子节点数量
    size_t tree_depth;              // 树的深度
    uint8_t root_hash[SM3_DIGEST_SIZE]; // 根哈希
} merkle_tree_t;

// 审计路径结构
typedef struct {
    uint8_t path_hashes[MERKLE_MAX_DEPTH][SM3_DIGEST_SIZE];
    int path_directions[MERKLE_MAX_DEPTH]; // 0=左，1=右
    size_t path_length;
    size_t leaf_index;
} merkle_audit_path_t;

// 一致性证明结构
typedef struct {
    uint8_t proof_hashes[MERKLE_MAX_DEPTH][SM3_DIGEST_SIZE];
    size_t proof_length;
    size_t old_tree_size;
    size_t new_tree_size;
} merkle_consistency_proof_t;

/**
 * 初始化Merkle树
 * @param tree Merkle树指针
 * @param max_leaves 最大叶子节点数量
 * @return 0成功，-1失败
 */
int merkle_tree_init(merkle_tree_t *tree, size_t max_leaves);

/**
 * 释放Merkle树内存
 * @param tree Merkle树指针
 */
void merkle_tree_free(merkle_tree_t *tree);

/**
 * 计算叶子节点哈希（RFC6962格式）
 * @param data 叶子数据
 * @param data_len 数据长度
 * @param hash 输出哈希值
 */
void merkle_leaf_hash(const uint8_t *data, size_t data_len, uint8_t *hash);

/**
 * 计算内部节点哈希（RFC6962格式）
 * @param left_hash 左子树哈希
 * @param right_hash 右子树哈希
 * @param hash 输出哈希值
 */
void merkle_node_hash(const uint8_t *left_hash, const uint8_t *right_hash, uint8_t *hash);

/**
 * 构建Merkle树
 * @param tree Merkle树指针
 * @param leaves 叶子数据数组
 * @param leaf_sizes 每个叶子数据的大小
 * @param leaf_count 叶子数量
 * @return 0成功，-1失败
 */
int merkle_tree_build(merkle_tree_t *tree, const uint8_t **leaves, 
                      const size_t *leaf_sizes, size_t leaf_count);

/**
 * 获取Merkle树根哈希
 * @param tree Merkle树指针
 * @param root_hash 输出根哈希
 * @return 0成功，-1失败
 */
int merkle_tree_get_root(merkle_tree_t *tree, uint8_t *root_hash);

/**
 * 生成存在性证明（审计路径）
 * @param tree Merkle树指针
 * @param leaf_index 叶子索引
 * @param proof 输出审计路径
 * @return 0成功，-1失败
 */
int merkle_tree_generate_inclusion_proof(merkle_tree_t *tree, size_t leaf_index,
                                        merkle_audit_path_t *proof);

/**
 * 验证存在性证明
 * @param leaf_data 叶子数据
 * @param leaf_len 叶子数据长度
 * @param proof 审计路径
 * @param root_hash 根哈希
 * @return 1验证成功，0验证失败
 */
int merkle_tree_verify_inclusion_proof(const uint8_t *leaf_data, size_t leaf_len,
                                      const merkle_audit_path_t *proof,
                                      const uint8_t *root_hash);

/**
 * 生成一致性证明
 * @param old_tree 旧树
 * @param new_tree 新树
 * @param proof 输出一致性证明
 * @return 0成功，-1失败
 */
int merkle_tree_generate_consistency_proof(merkle_tree_t *old_tree, 
                                          merkle_tree_t *new_tree,
                                          merkle_consistency_proof_t *proof);

/**
 * 验证一致性证明
 * @param old_root 旧树根哈希
 * @param new_root 新树根哈希
 * @param proof 一致性证明
 * @return 1验证成功，0验证失败
 */
int merkle_tree_verify_consistency_proof(const uint8_t *old_root,
                                        const uint8_t *new_root,
                                        const merkle_consistency_proof_t *proof);

/**
 * 生成不存在性证明
 * 通过证明相邻叶子的存在来证明某个值不存在
 * @param tree Merkle树指针
 * @param target_hash 目标值的哈希
 * @param left_proof 左侧相邻元素的存在性证明
 * @param right_proof 右侧相邻元素的存在性证明
 * @return 0成功，-1失败
 */
int merkle_tree_generate_non_inclusion_proof(merkle_tree_t *tree,
                                            const uint8_t *target_hash,
                                            merkle_audit_path_t *left_proof,
                                            merkle_audit_path_t *right_proof);

/**
 * 验证不存在性证明
 * @param target_hash 目标值的哈希
 * @param left_leaf_data 左侧叶子数据
 * @param left_leaf_len 左侧叶子数据长度
 * @param left_proof 左侧存在性证明
 * @param right_leaf_data 右侧叶子数据
 * @param right_leaf_len 右侧叶子数据长度
 * @param right_proof 右侧存在性证明
 * @param root_hash 根哈希
 * @return 1验证成功，0验证失败
 */
int merkle_tree_verify_non_inclusion_proof(const uint8_t *target_hash,
                                          const uint8_t *left_leaf_data, size_t left_leaf_len,
                                          const merkle_audit_path_t *left_proof,
                                          const uint8_t *right_leaf_data, size_t right_leaf_len,
                                          const merkle_audit_path_t *right_proof,
                                          const uint8_t *root_hash);

/**
 * 打印Merkle树统计信息
 * @param tree Merkle树指针
 */
void merkle_tree_print_stats(const merkle_tree_t *tree);

/**
 * 打印审计路径
 * @param proof 审计路径指针
 */
void merkle_audit_path_print(const merkle_audit_path_t *proof);

/**
 * 将哈希转换为十六进制字符串
 * @param hash 哈希值
 * @param hex_str 输出字符串（至少65字节）
 */
void merkle_hash_to_hex(const uint8_t *hash, char *hex_str);

#ifdef __cplusplus
}
#endif

#endif // MERKLE_TREE_H
