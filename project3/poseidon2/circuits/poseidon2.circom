pragma circom 2.0.0;

// Poseidon2哈希算法电路实现
// 参数: (n,t,d) = (256,3,5)
// n = 256: 字段大小 (BN254曲线素数域)
// t = 3: 状态宽度 (3个字段元素)
// d = 5: S盒指数

// 模运算组件
template ModAdd() {
    signal input a;
    signal input b;
    signal output out;
    
    out <-- (a + b) % 21888242871839275222246405745257275088548364400416034343698204186575808495617;
    out === a + b - (a + b) \ 21888242871839275222246405745257275088548364400416034343698204186575808495617;
}

template ModMul() {
    signal input a;
    signal input b;
    signal output out;
    
    out <-- (a * b) % 21888242871839275222246405745257275088548364400416034343698204186575808495617;
    out === a * b - (a * b) \ 21888242871839275222246405745257275088548364400416034343698204186575808495617;
}

// S-box组件: x^5
template SBox() {
    signal input in;
    signal output out;
    
    signal x2;
    signal x4;
    
    component mul1 = ModMul();
    mul1.a <== in;
    mul1.b <== in;
    x2 <== mul1.out;
    
    component mul2 = ModMul();
    mul2.a <== x2;
    mul2.b <== x2;
    x4 <== mul2.out;
    
    component mul3 = ModMul();
    mul3.a <== x4;
    mul3.b <== in;
    out <== mul3.out;
}

// 线性层组件 (MDS矩阵)
template LinearLayer() {
    signal input in[3];
    signal output out[3];
    
    // MDS矩阵 3x3，针对Poseidon2优化的矩阵
    // 使用简化的MDS矩阵减少约束数量
    component add1[3];
    component add2[3];
    component mul1[3];
    component mul2[3];
    
    // 第一行: [2, 1, 1]
    for (var i = 0; i < 3; i++) {
        add1[i] = ModAdd();
        mul1[i] = ModMul();
    }
    
    mul1[0].a <== 2;
    mul1[0].b <== in[0];
    add1[0].a <== mul1[0].out;
    add1[0].b <== in[1];
    add2[0] = ModAdd();
    add2[0].a <== add1[0].out;
    add2[0].b <== in[2];
    out[0] <== add2[0].out;
    
    // 第二行: [1, 2, 1]  
    add1[1].a <== in[0];
    mul1[1].a <== 2;
    mul1[1].b <== in[1];
    add1[1].b <== mul1[1].out;
    add2[1] = ModAdd();
    add2[1].a <== add1[1].out;
    add2[1].b <== in[2];
    out[1] <== add2[1].out;
    
    // 第三行: [1, 1, 2]
    add1[2].a <== in[0];
    add1[2].b <== in[1];
    mul1[2].a <== 2;
    mul1[2].b <== in[2];
    add2[2] = ModAdd();
    add2[2].a <== add1[2].out;
    add2[2].b <== mul1[2].out;
    out[2] <== add2[2].out;
}

// 部分轮函数 (只有第一个元素应用S-box)
template PartialRound(round) {
    signal input state[3];
    signal output newState[3];
    
    // 轮常数 (简化版本，实际应使用标准常数)
    var roundConstants[3] = [
        (round * 7 + 1) % 21888242871839275222246405745257275088548364400416034343698204186575808495617,
        (round * 11 + 3) % 21888242871839275222246405745257275088548364400416034343698204186575808495617,
        (round * 13 + 5) % 21888242871839275222246405745257275088548364400416034343698204186575808495617
    ];
    
    // 加轮常数
    component addRC[3];
    signal afterRC[3];
    for (var i = 0; i < 3; i++) {
        addRC[i] = ModAdd();
        addRC[i].a <== state[i];
        addRC[i].b <== roundConstants[i];
        afterRC[i] <== addRC[i].out;
    }
    
    // 只对第一个元素应用S-box
    component sbox = SBox();
    sbox.in <== afterRC[0];
    signal afterSBox[3];
    afterSBox[0] <== sbox.out;
    afterSBox[1] <== afterRC[1];
    afterSBox[2] <== afterRC[2];
    
    // 线性层
    component linear = LinearLayer();
    for (var i = 0; i < 3; i++) {
        linear.in[i] <== afterSBox[i];
    }
    for (var i = 0; i < 3; i++) {
        newState[i] <== linear.out[i];
    }
}

// 完整轮函数 (所有元素都应用S-box)
template FullRound(round) {
    signal input state[3];
    signal output newState[3];
    
    // 轮常数
    var roundConstants[3] = [
        (round * 7 + 1) % 21888242871839275222246405745257275088548364400416034343698204186575808495617,
        (round * 11 + 3) % 21888242871839275222246405745257275088548364400416034343698204186575808495617,
        (round * 13 + 5) % 21888242871839275222246405745257275088548364400416034343698204186575808495617
    ];
    
    // 加轮常数
    component addRC[3];
    signal afterRC[3];
    for (var i = 0; i < 3; i++) {
        addRC[i] = ModAdd();
        addRC[i].a <== state[i];
        addRC[i].b <== roundConstants[i];
        afterRC[i] <== addRC[i].out;
    }
    
    // 对所有元素应用S-box
    component sbox[3];
    signal afterSBox[3];
    for (var i = 0; i < 3; i++) {
        sbox[i] = SBox();
        sbox[i].in <== afterRC[i];
        afterSBox[i] <== sbox[i].out;
    }
    
    // 线性层
    component linear = LinearLayer();
    for (var i = 0; i < 3; i++) {
        linear.in[i] <== afterSBox[i];
    }
    for (var i = 0; i < 3; i++) {
        newState[i] <== linear.out[i];
    }
}

// Poseidon2哈希函数主模板
template Poseidon2Hash() {
    signal input preimage[2];  // 2个字段元素作为输入 
    signal output hash;        // 1个字段元素作为输出
    
    // 初始状态: [preimage[0], preimage[1], 0]
    signal state[61][3];  // 总共60轮: 4个完整轮 + 52个部分轮 + 4个完整轮
    
    state[0][0] <== preimage[0];
    state[0][1] <== preimage[1];
    state[0][2] <== 0;
    
    // 前4个完整轮
    component fullRound1[4];
    for (var i = 0; i < 4; i++) {
        fullRound1[i] = FullRound(i);
        for (var j = 0; j < 3; j++) {
            fullRound1[i].state[j] <== state[i][j];
        }
        for (var j = 0; j < 3; j++) {
            state[i + 1][j] <== fullRound1[i].newState[j];
        }
    }
    
    // 52个部分轮
    component partialRound[52];
    for (var i = 0; i < 52; i++) {
        partialRound[i] = PartialRound(i + 4);
        for (var j = 0; j < 3; j++) {
            partialRound[i].state[j] <== state[i + 4][j];
        }
        for (var j = 0; j < 3; j++) {
            state[i + 5][j] <== partialRound[i].newState[j];
        }
    }
    
    // 后4个完整轮
    component fullRound2[4];
    for (var i = 0; i < 4; i++) {
        fullRound2[i] = FullRound(i + 56);
        for (var j = 0; j < 3; j++) {
            fullRound2[i].state[j] <== state[i + 56][j];
        }
        for (var j = 0; j < 3; j++) {
            state[i + 57][j] <== fullRound2[i].newState[j];
        }
    }
    
    // 输出第一个状态元素作为哈希值
    hash <== state[60][0];
}

// 零知识证明电路: 证明知道哈希原象
template Poseidon2ZKProof() {
    // 公开输入: 哈希值
    signal input hashValue;
    
    // 隐私输入: 哈希原象 
    signal private input preimage[2];
    
    // 计算哈希
    component hasher = Poseidon2Hash();
    hasher.preimage[0] <== preimage[0];
    hasher.preimage[1] <== preimage[1];
    
    // 验证哈希值匹配
    hashValue === hasher.hash;
}

// 主电路
component main = Poseidon2ZKProof();
