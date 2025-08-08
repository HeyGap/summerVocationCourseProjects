pragma circom 2.0.0;

// 简化的Poseidon2哈希算法电路实现 (用于测试)
// 参数: (n,t,d) = (256,3,5)
// 减少轮数以便快速测试

// 模运算组件
template ModAdd() {
    signal input a;
    signal input b;
    signal output out;
    
    out <== (a + b) % 21888242871839275222246405745257275088548364400416034343698204186575808495617;
}

template ModMul() {
    signal input a;
    signal input b;
    signal output out;
    
    out <== (a * b) % 21888242871839275222246405745257275088548364400416034343698204186575808495617;
}

// S-box组件: x^5
template SBox() {
    signal input in;
    signal output out;
    
    signal x2 <== in * in;
    signal x4 <== x2 * x2;
    out <== x4 * in;
}

// 简化的线性层组件
template SimpleLinearLayer() {
    signal input in[3];
    signal output out[3];
    
    // 简化的混合矩阵
    out[0] <== 2 * in[0] + in[1] + in[2];
    out[1] <== in[0] + 2 * in[1] + in[2];
    out[2] <== in[0] + in[1] + 2 * in[2];
}

// 完整轮函数
template FullRound(round) {
    signal input state[3];
    signal output newState[3];
    
    // 简化的轮常数
    var roundConstants[3] = [round + 1, round + 2, round + 3];
    
    // 加轮常数
    signal afterRC[3];
    afterRC[0] <== state[0] + roundConstants[0];
    afterRC[1] <== state[1] + roundConstants[1];
    afterRC[2] <== state[2] + roundConstants[2];
    
    // S-box层
    component sbox[3];
    signal afterSBox[3];
    for (var i = 0; i < 3; i++) {
        sbox[i] = SBox();
        sbox[i].in <== afterRC[i];
        afterSBox[i] <== sbox[i].out;
    }
    
    // 线性层
    component linear = SimpleLinearLayer();
    for (var i = 0; i < 3; i++) {
        linear.in[i] <== afterSBox[i];
    }
    for (var i = 0; i < 3; i++) {
        newState[i] <== linear.out[i];
    }
}

// 部分轮函数
template PartialRound(round) {
    signal input state[3];
    signal output newState[3];
    
    // 简化的轮常数
    var roundConstants[3] = [round + 10, round + 20, round + 30];
    
    // 加轮常数
    signal afterRC[3];
    afterRC[0] <== state[0] + roundConstants[0];
    afterRC[1] <== state[1] + roundConstants[1];
    afterRC[2] <== state[2] + roundConstants[2];
    
    // 只对第一个元素应用S-box
    component sbox = SBox();
    sbox.in <== afterRC[0];
    signal afterSBox[3];
    afterSBox[0] <== sbox.out;
    afterSBox[1] <== afterRC[1];
    afterSBox[2] <== afterRC[2];
    
    // 线性层
    component linear = SimpleLinearLayer();
    for (var i = 0; i < 3; i++) {
        linear.in[i] <== afterSBox[i];
    }
    for (var i = 0; i < 3; i++) {
        newState[i] <== linear.out[i];
    }
}

// 简化的Poseidon2哈希函数
template SimplePoseidon2Hash() {
    signal input preimage[2];
    signal output hash;
    
    // 初始状态
    signal state[9][3];  // 8轮: 2个完整轮 + 4个部分轮 + 2个完整轮
    
    state[0][0] <== preimage[0];
    state[0][1] <== preimage[1];
    state[0][2] <== 0;
    
    // 前2个完整轮
    component fullRound1[2];
    for (var i = 0; i < 2; i++) {
        fullRound1[i] = FullRound(i);
        for (var j = 0; j < 3; j++) {
            fullRound1[i].state[j] <== state[i][j];
        }
        for (var j = 0; j < 3; j++) {
            state[i + 1][j] <== fullRound1[i].newState[j];
        }
    }
    
    // 4个部分轮
    component partialRound[4];
    for (var i = 0; i < 4; i++) {
        partialRound[i] = PartialRound(i + 2);
        for (var j = 0; j < 3; j++) {
            partialRound[i].state[j] <== state[i + 2][j];
        }
        for (var j = 0; j < 3; j++) {
            state[i + 3][j] <== partialRound[i].newState[j];
        }
    }
    
    // 后2个完整轮
    component fullRound2[2];
    for (var i = 0; i < 2; i++) {
        fullRound2[i] = FullRound(i + 6);
        for (var j = 0; j < 3; j++) {
            fullRound2[i].state[j] <== state[i + 6][j];
        }
        for (var j = 0; j < 3; j++) {
            state[i + 7][j] <== fullRound2[i].newState[j];
        }
    }
    
    // 输出
    hash <== state[8][0];
}

// 零知识证明电路
template SimplePoseidon2ZKProof() {
    signal input hashValue;           // 公开输入
    signal input preimage[2]; // 隐私输入
    
    component hasher = SimplePoseidon2Hash();
    hasher.preimage[0] <== preimage[0];
    hasher.preimage[1] <== preimage[1];
    
    hashValue === hasher.hash;
}

component main = SimplePoseidon2ZKProof();
