pragma circom 2.0.0;

// Poseidon2哈希算法的不同参数配置
// 支持 (n,t,d) = (256,2,5) 和 (256,3,5)

include "simple_poseidon2.circom";

// 参数 (256,2,5) - 2个输入元素
template Poseidon2_t2() {
    signal input preimage[1];  // 只有1个输入元素
    signal output hash;
    
    // 状态: [preimage[0], 0, 0]
    signal state[5][2];  // 简化到5轮: 1+2+2
    
    state[0][0] <== preimage[0];
    state[0][1] <== 0;
    
    // 2个完整轮
    component fullRound1[2];
    for (var i = 0; i < 2; i++) {
        fullRound1[i] = FullRound2(i);
        fullRound1[i].state[0] <== state[i][0];
        fullRound1[i].state[1] <== state[i][1];
        state[i + 1][0] <== fullRound1[i].newState[0];
        state[i + 1][1] <== fullRound1[i].newState[1];
    }
    
    // 1个部分轮
    component partialRound = PartialRound2(2);
    partialRound.state[0] <== state[2][0];
    partialRound.state[1] <== state[2][1];
    state[3][0] <== partialRound.newState[0];
    state[3][1] <== partialRound.newState[1];
    
    // 2个完整轮
    component fullRound2[2];
    for (var i = 0; i < 2; i++) {
        fullRound2[i] = FullRound2(i + 3);
        fullRound2[i].state[0] <== state[i + 3][0];
        fullRound2[i].state[1] <== state[i + 3][1];
        state[i + 4][0] <== fullRound2[i].newState[0];
        state[i + 4][1] <== fullRound2[i].newState[1];
    }
    
    hash <== state[4][0];
}

// t=2的完整轮
template FullRound2(round) {
    signal input state[2];
    signal output newState[2];
    
    var roundConstants[2] = [round + 1, round + 2];
    
    // 加轮常数 + S-box
    component sbox[2];
    signal afterSBox[2];
    for (var i = 0; i < 2; i++) {
        sbox[i] = SBox();
        sbox[i].in <== state[i] + roundConstants[i];
        afterSBox[i] <== sbox[i].out;
    }
    
    // 简化的2x2线性层
    component linear = LinearLayer2();
    linear.in[0] <== afterSBox[0];
    linear.in[1] <== afterSBox[1];
    newState[0] <== linear.out[0];
    newState[1] <== linear.out[1];
}

// t=2的部分轮
template PartialRound2(round) {
    signal input state[2];
    signal output newState[2];
    
    var roundConstants[2] = [round + 10, round + 20];
    
    // 只对第一个元素应用S-box
    component sbox = SBox();
    sbox.in <== state[0] + roundConstants[0];
    
    signal afterSBox[2];
    afterSBox[0] <== sbox.out;
    afterSBox[1] <== state[1] + roundConstants[1];
    
    // 线性层
    component linear = LinearLayer2();
    linear.in[0] <== afterSBox[0];
    linear.in[1] <== afterSBox[1];
    newState[0] <== linear.out[0];
    newState[1] <== linear.out[1];
}

// 2x2线性层
template LinearLayer2() {
    signal input in[2];
    signal output out[2];
    
    // 简单的2x2 MDS矩阵
    out[0] <== 2 * in[0] + in[1];
    out[1] <== in[0] + 2 * in[1];
}

// t=2的零知识证明
template Poseidon2ZKProof_t2() {
    signal input hashValue;
    signal private input preimage[1];
    
    component hasher = Poseidon2_t2();
    hasher.preimage[0] <== preimage[0];
    
    hashValue === hasher.hash;
}

// 参数对比测试电路
template ParameterComparison() {
    signal input preimage1[1];  // t=2的输入
    signal input preimage2[2];  // t=3的输入
    
    signal output hash_t2;      // t=2的哈希
    signal output hash_t3;      // t=3的哈希
    
    // t=2版本
    component hasher2 = Poseidon2_t2();
    hasher2.preimage[0] <== preimage1[0];
    hash_t2 <== hasher2.hash;
    
    // t=3版本 (使用简化版本)
    component hasher3 = SimplePoseidon2Hash();
    hasher3.preimage[0] <== preimage2[0];
    hasher3.preimage[1] <== preimage2[1];
    hash_t3 <== hasher3.hash;
    
    // 可以添加更多分析逻辑
}

// 性能测试电路
template PerformanceTest() {
    signal input inputs[4];
    signal output results[4];
    
    // 测试不同配置的性能
    component test1 = Poseidon2_t2();
    test1.preimage[0] <== inputs[0];
    results[0] <== test1.hash;
    
    component test2 = Poseidon2_t2();
    test2.preimage[0] <== inputs[1];
    results[1] <== test2.hash;
    
    component test3 = SimplePoseidon2Hash();
    test3.preimage[0] <== inputs[2];
    test3.preimage[1] <== inputs[3];
    results[2] <== test3.hash;
    
    // 批量测试
    results[3] <== results[0] + results[1] + results[2];
}

// 安全性测试电路 - 测试哈希的雪崩效应
template AvalancheTest() {
    signal input original[2];
    signal input modified[2];  // 只有1位不同
    
    signal output originalHash;
    signal output modifiedHash;
    signal output difference;
    
    component hasher1 = SimplePoseidon2Hash();
    hasher1.preimage[0] <== original[0];
    hasher1.preimage[1] <== original[1];
    originalHash <== hasher1.hash;
    
    component hasher2 = SimplePoseidon2Hash();
    hasher2.preimage[0] <== modified[0];
    hasher2.preimage[1] <== modified[1];
    modifiedHash <== hasher2.hash;
    
    // 计算差值 (简化)
    difference <== originalHash - modifiedHash;
}

// 可以选择不同的主电路进行测试
// component main = Poseidon2ZKProof_t2();
// component main = ParameterComparison(); 
// component main = PerformanceTest();
component main = AvalancheTest();
