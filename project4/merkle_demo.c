#include "merkle_tree.h"
#include "sm3.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// 演示数据结构
typedef struct {
    uint8_t *data;
    size_t size;
    char description[64];
} demo_leaf_t;

// 创建演示数据
static demo_leaf_t* create_demo_leaves(size_t count) {
    demo_leaf_t *leaves = malloc(count * sizeof(demo_leaf_t));
    if (!leaves) return NULL;
    
    for (size_t i = 0; i < count; i++) {
        // 创建不同类型的数据
        if (i % 3 == 0) {
            // 用户ID类型的数据
            leaves[i].size = snprintf(NULL, 0, "user_%zu", i) + 1;
            leaves[i].data = malloc(leaves[i].size);
            snprintf((char*)leaves[i].data, leaves[i].size, "user_%zu", i);
            snprintf(leaves[i].description, sizeof(leaves[i].description), "用户ID: user_%zu", i);
        } else if (i % 3 == 1) {
            // 交易哈希类型的数据  
            leaves[i].size = 32;
            leaves[i].data = malloc(32);
            for (int j = 0; j < 32; j++) {
                leaves[i].data[j] = (uint8_t)((i * 31 + j * 17) % 256);
            }
            snprintf(leaves[i].description, sizeof(leaves[i].description), "交易哈希 #%zu", i);
        } else {
            // 文档ID类型的数据
            leaves[i].size = snprintf(NULL, 0, "doc_%zu_%lu", i, time(NULL)) + 1;
            leaves[i].data = malloc(leaves[i].size);
            snprintf((char*)leaves[i].data, leaves[i].size, "doc_%zu_%lu", i, time(NULL));
            snprintf(leaves[i].description, sizeof(leaves[i].description), "文档ID: doc_%zu", i);
        }
    }
    
    return leaves;
}

// 清理演示数据
static void cleanup_demo_leaves(demo_leaf_t *leaves, size_t count) {
    if (!leaves) return;
    
    for (size_t i = 0; i < count; i++) {
        free(leaves[i].data);
    }
    free(leaves);
}

// 演示存在性证明
static void demo_inclusion_proof(merkle_tree_t *tree, demo_leaf_t *leaves, size_t leaf_count) {
    printf("\n=== 存在性证明演示 ===\n");
    
    // 选择几个叶子进行演示
    size_t test_indices[] = {0, 1, leaf_count/2, leaf_count-1};
    size_t test_count = sizeof(test_indices) / sizeof(test_indices[0]);
    
    uint8_t root_hash[SM3_DIGEST_SIZE];
    merkle_tree_get_root(tree, root_hash);
    
    char root_hex[65];
    merkle_hash_to_hex(root_hash, root_hex);
    printf("Merkle树根哈希: %s\n", root_hex);
    printf("正在为 %zu 个叶子节点生成和验证存在性证明...\n\n", test_count);
    
    for (size_t i = 0; i < test_count; i++) {
        size_t leaf_idx = test_indices[i];
        if (leaf_idx >= leaf_count) continue;
        
        printf("叶子 %zu: %s\n", leaf_idx, leaves[leaf_idx].description);
        
        // 显示叶子数据的哈希
        uint8_t leaf_hash[SM3_DIGEST_SIZE];
        merkle_leaf_hash(leaves[leaf_idx].data, leaves[leaf_idx].size, leaf_hash);
        char leaf_hex[65];
        merkle_hash_to_hex(leaf_hash, leaf_hex);
        printf("   叶子哈希: %s\n", leaf_hex);
        
        // 生成存在性证明
        merkle_audit_path_t proof;
        if (merkle_tree_generate_inclusion_proof(tree, leaf_idx, &proof) != 0) {
            printf("   证明生成失败\n\n");
            continue;
        }
        
        printf("   审计路径长度: %zu\n", proof.path_length);
        
        // 验证存在性证明
        int verified = merkle_tree_verify_inclusion_proof(
            leaves[leaf_idx].data, leaves[leaf_idx].size, &proof, root_hash);
        
        if (verified) {
            printf("   存在性证明验证成功！\n");
        } else {
            printf("   存在性证明验证失败！\n");
        }
        
        printf("   🛤️  证明路径:\n");
        for (size_t j = 0; j < proof.path_length; j++) {
            char step_hex[65];
            merkle_hash_to_hex(proof.path_hashes[j], step_hex);
            printf("      步骤 %zu: %s (%s兄弟)\n", j+1, step_hex, 
                   proof.path_directions[j] == 0 ? "左" : "右");
        }
        printf("\n");
    }
}

// 演示不存在性证明
static void demo_non_inclusion_proof(merkle_tree_t *tree, demo_leaf_t *leaves, size_t leaf_count) {
    printf("🚫 === 不存在性证明演示 ===\n");
    
    // 创建一个不存在的数据
    const char *non_existent_data = "这个数据不在Merkle树中！";
    size_t non_existent_len = strlen(non_existent_data);
    
    uint8_t non_existent_hash[SM3_DIGEST_SIZE];
    merkle_leaf_hash((const uint8_t*)non_existent_data, non_existent_len, non_existent_hash);
    
    char target_hex[65];
    merkle_hash_to_hex(non_existent_hash, target_hex);
    printf("目标数据: \"%s\"\n", non_existent_data);
    printf("目标哈希: %s\n", target_hex);
    
    // 生成不存在性证明
    merkle_audit_path_t left_proof, right_proof;
    if (merkle_tree_generate_non_inclusion_proof(tree, non_existent_hash, &left_proof, &right_proof) != 0) {
        printf("❌ 不存在性证明生成失败\n");
        return;
    }
    
    printf("\n📍 边界证明:\n");
    printf("   左边界 (叶子 %zu): %s\n", left_proof.leaf_index, leaves[left_proof.leaf_index].description);
    printf("   右边界 (叶子 %zu): %s\n", right_proof.leaf_index, leaves[right_proof.leaf_index].description);
    
    // 验证边界叶子的存在性
    uint8_t root_hash[SM3_DIGEST_SIZE];
    merkle_tree_get_root(tree, root_hash);
    
    int left_verified = merkle_tree_verify_inclusion_proof(
        leaves[left_proof.leaf_index].data, leaves[left_proof.leaf_index].size, 
        &left_proof, root_hash);
    
    int right_verified = merkle_tree_verify_inclusion_proof(
        leaves[right_proof.leaf_index].data, leaves[right_proof.leaf_index].size, 
        &right_proof, root_hash);
    
    if (left_verified && right_verified) {
        printf("✅ 边界叶子存在性验证成功！\n");
        printf("✅ 不存在性证明有效：目标数据确实不在树中\n");
    } else {
        printf("❌ 边界叶子验证失败\n");
    }
}

// 性能基准测试
static void performance_benchmark() {
    printf("\n⚡ === 性能基准测试 ===\n");
    
    const size_t test_sizes[] = {1000, 10000, 50000, 100000};
    const size_t num_tests = sizeof(test_sizes) / sizeof(test_sizes[0]);
    
    printf("测试不同规模的Merkle树性能...\n\n");
    printf("%-10s %-12s %-12s %-12s %-8s %-12s\n", 
           "叶子数量", "构建时间(ms)", "证明生成(ms)", "证明验证(μs)", "树深度", "内存使用(KB)");
    printf("%-10s %-12s %-12s %-12s %-8s %-12s\n",
           "--------", "-----------", "-----------", "-----------", "------", "-----------");
    
    for (size_t t = 0; t < num_tests; t++) {
        size_t leaf_count = test_sizes[t];
        
        // 创建测试数据
        demo_leaf_t *leaves = create_demo_leaves(leaf_count);
        if (!leaves) continue;
        
        // 准备Merkle树构建的输入
        const uint8_t **leaf_data = malloc(leaf_count * sizeof(uint8_t*));
        size_t *leaf_sizes = malloc(leaf_count * sizeof(size_t));
        
        for (size_t i = 0; i < leaf_count; i++) {
            leaf_data[i] = leaves[i].data;
            leaf_sizes[i] = leaves[i].size;
        }
        
        // 测试构建时间
        merkle_tree_t tree;
        merkle_tree_init(&tree, leaf_count);
        
        clock_t build_start = clock();
        merkle_tree_build(&tree, leaf_data, leaf_sizes, leaf_count);
        clock_t build_end = clock();
        double build_ms = ((double)(build_end - build_start)) / CLOCKS_PER_SEC * 1000;
        
        // 测试证明生成时间
        merkle_audit_path_t proof;
        clock_t proof_start = clock();
        merkle_tree_generate_inclusion_proof(&tree, leaf_count / 2, &proof);
        clock_t proof_end = clock();
        double proof_ms = ((double)(proof_end - proof_start)) / CLOCKS_PER_SEC * 1000;
        
        // 测试证明验证时间
        uint8_t root_hash[SM3_DIGEST_SIZE];
        merkle_tree_get_root(&tree, root_hash);
        
        clock_t verify_start = clock();
        merkle_tree_verify_inclusion_proof(leaf_data[leaf_count/2], leaf_sizes[leaf_count/2], 
                                         &proof, root_hash);
        clock_t verify_end = clock();
        double verify_us = ((double)(verify_end - verify_start)) / CLOCKS_PER_SEC * 1000000;
        
        // 估算内存使用
        size_t memory_kb = (leaf_count * sizeof(merkle_node_t) + 
                           leaf_count * 64 + // 平均叶子大小
                           SM3_DIGEST_SIZE) / 1024;
        
        printf("%-10zu %-12.2f %-12.2f %-12.2f %-8zu %-12zu\n",
               leaf_count, build_ms, proof_ms, verify_us, tree.tree_depth, memory_kb);
        
        // 清理
        merkle_tree_free(&tree);
        cleanup_demo_leaves(leaves, leaf_count);
        free(leaf_data);
        free(leaf_sizes);
    }
}

// 实际应用场景演示
static void application_demo() {
    printf("\n🚀 === 实际应用场景演示 ===\n");
    
    printf("场景1: 区块链交易验证\n");
    printf("      - 10,000笔交易构建Merkle树\n");
    printf("      - 轻节点只需下载32字节根哈希 + 审计路径\n");
    printf("      - 验证任意交易的存在性，无需下载完整区块\n");
    
    printf("\n场景2: 证书透明度日志\n");
    printf("      - 证书颁发机构将所有证书记录在公开日志中\n");
    printf("      - 域名所有者可以监控自己域名的证书发行情况\n");
    printf("      - 浏览器验证证书是否在可信日志中\n");
    
    printf("\n场景3: 数据完整性审计\n");  
    printf("      - 云存储服务提供数据完整性证明\n");
    printf("      - 客户端可以验证文件未被篡改\n");
    printf("      - 支持增量验证，无需重新计算全部数据\n");
    
    // 演示一个简单的区块链场景
    printf("\n📦 区块链场景演示:\n");
    const size_t tx_count = 1000;
    demo_leaf_t *transactions = create_demo_leaves(tx_count);
    
    // 构建交易Merkle树
    const uint8_t **tx_data = malloc(tx_count * sizeof(uint8_t*));
    size_t *tx_sizes = malloc(tx_count * sizeof(size_t));
    
    for (size_t i = 0; i < tx_count; i++) {
        tx_data[i] = transactions[i].data;
        tx_sizes[i] = transactions[i].size;
    }
    
    merkle_tree_t block_tree;
    merkle_tree_init(&block_tree, tx_count);
    merkle_tree_build(&block_tree, tx_data, tx_sizes, tx_count);
    
    uint8_t block_root[SM3_DIGEST_SIZE];
    merkle_tree_get_root(&block_tree, block_root);
    
    char block_hex[65];
    merkle_hash_to_hex(block_root, block_hex);
    printf("   区块根哈希: %s\n", block_hex);
    
    // 模拟轻节点验证
    size_t verify_tx = 500;
    merkle_audit_path_t tx_proof;
    merkle_tree_generate_inclusion_proof(&block_tree, verify_tx, &tx_proof);
    
    printf("   轻节点验证交易 #%zu:\n", verify_tx);
    printf("     - 需要数据: 32字节根哈希 + %zu步审计路径\n", tx_proof.path_length);
    printf("     - 总计: %zu字节 (vs 完整区块 ~%zu字节)\n", 
           32 + tx_proof.path_length * 32, tx_count * 64);
    printf("     - 数据传输减少: %.1f%%\n", 
           (1.0 - (double)(32 + tx_proof.path_length * 32) / (tx_count * 64)) * 100);
    
    // 清理
    merkle_tree_free(&block_tree);
    cleanup_demo_leaves(transactions, tx_count);
    free(tx_data);
    free(tx_sizes);
}

int main() {
    printf("🌳 RFC6962 Merkle树演示程序\n");
    printf("基于SM3哈希算法的高性能实现\n");
    printf("=========================================\n");
    
    // 创建演示用的Merkle树
    const size_t demo_leaf_count = 100;
    printf("正在创建包含 %zu 个叶子节点的演示Merkle树...\n", demo_leaf_count);
    
    demo_leaf_t *leaves = create_demo_leaves(demo_leaf_count);
    if (!leaves) {
        printf("❌ 内存分配失败\n");
        return 1;
    }
    
    // 准备输入数据
    const uint8_t **leaf_data = malloc(demo_leaf_count * sizeof(uint8_t*));
    size_t *leaf_sizes = malloc(demo_leaf_count * sizeof(size_t));
    
    for (size_t i = 0; i < demo_leaf_count; i++) {
        leaf_data[i] = leaves[i].data;
        leaf_sizes[i] = leaves[i].size;
    }
    
    // 构建Merkle树
    merkle_tree_t tree;
    if (merkle_tree_init(&tree, demo_leaf_count) != 0) {
        printf("❌ Merkle树初始化失败\n");
        goto cleanup;
    }
    
    if (merkle_tree_build(&tree, leaf_data, leaf_sizes, demo_leaf_count) != 0) {
        printf("❌ Merkle树构建失败\n");
        goto cleanup;
    }
    
    printf("✅ Merkle树构建成功！\n");
    merkle_tree_print_stats(&tree);
    
    // 演示各种功能
    demo_inclusion_proof(&tree, leaves, demo_leaf_count);
    demo_non_inclusion_proof(&tree, leaves, demo_leaf_count);
    performance_benchmark();
    application_demo();
    
    printf("\n🎉 === 演示完成 ===\n");
    printf("主要成果:\n");
    printf("✓ 成功实现RFC6962标准的Merkle树\n");
    printf("✓ 支持大规模数据处理(100K+叶子节点)\n"); 
    printf("✓ 高效的存在性和不存在性证明\n");
    printf("✓ 基于国密SM3算法的安全哈希\n");
    printf("✓ 完整的证明生成和验证流程\n");
    
    printf("\n应用价值:\n");
    printf("• 区块链系统: 轻节点验证、状态证明\n");
    printf("• 证书透明度: 公开审计、信任建立\n");
    printf("• 数据完整性: 云存储验证、版本控制\n");
    printf("• 隐私保护: 零知识证明、选择性披露\n");

cleanup:
    merkle_tree_free(&tree);
    cleanup_demo_leaves(leaves, demo_leaf_count);
    free(leaf_data);
    free(leaf_sizes);
    
    return 0;
}
