const fs = require("fs");
const crypto = require("crypto");

// Poseidon2哈希测试
async function testPoseidon2() {
    console.log("开始Poseidon2哈希电路测试...\n");
    
    // 1. 编译电路
    console.log("1. 编译电路...");
    
    // 2. 生成见证
    console.log("2. 生成见证...");
    
    // 测试输入
    const preimage = [
        "123456789",  // 第一个原象元素
        "987654321"   // 第二个原象元素
    ];
    
    console.log("原象:", preimage);
    
    // 计算哈希值 (这里使用简化计算)
    const hashValue = calculateSimplePoseidon2Hash(preimage);
    console.log("计算的哈希值:", hashValue);
    
    const input = {
        "hashValue": hashValue,
        "preimage": preimage
    };
    
    // 写入输入文件
    fs.writeFileSync("./build/input.json", JSON.stringify(input, null, 2));
    
    console.log("输入数据已保存到 input.json");
    
    return { preimage, hashValue };
}

// 简化的Poseidon2哈希计算 (用于测试)
function calculateSimplePoseidon2Hash(preimage) {
    // 这是一个简化的模拟实现，实际应该与电路保持一致
    const p = 21888242871839275222246405745257275088548364400416034343698204186575808495617n;
    
    // 确保输入是整数字符串
    const input0 = preimage[0].toString().replace(/\./g, '');
    const input1 = preimage[1].toString().replace(/\./g, '');
    
    let state = [
        BigInt(input0) % p,
        BigInt(input1) % p,
        0n
    ];
    
    // 8轮简化处理
    for (let round = 0; round < 8; round++) {
        // 加轮常数
        if (round < 2 || round >= 6) {
            // 完整轮
            state[0] = (state[0] + BigInt(round + 1)) % p;
            state[1] = (state[1] + BigInt(round + 2)) % p;
            state[2] = (state[2] + BigInt(round + 3)) % p;
            
            // S-box (x^5)
            state[0] = modPow(state[0], 5n, p);
            state[1] = modPow(state[1], 5n, p);
            state[2] = modPow(state[2], 5n, p);
        } else {
            // 部分轮
            state[0] = (state[0] + BigInt(round + 10)) % p;
            state[1] = (state[1] + BigInt(round + 20)) % p;
            state[2] = (state[2] + BigInt(round + 30)) % p;
            
            // 只对第一个元素应用S-box
            state[0] = modPow(state[0], 5n, p);
        }
        
        // 线性层 (简化混合)
        const newState = [
            (2n * state[0] + state[1] + state[2]) % p,
            (state[0] + 2n * state[1] + state[2]) % p,
            (state[0] + state[1] + 2n * state[2]) % p
        ];
        state = newState;
    }
    
    return state[0].toString();
}

// 模幂运算
function modPow(base, exp, mod) {
    let result = 1n;
    base = base % mod;
    while (exp > 0n) {
        if (exp % 2n === 1n) {
            result = (result * base) % mod;
        }
        exp = exp >> 1n;
        base = (base * base) % mod;
    }
    return result;
}

// Groth16证明生成
async function generateProof() {
    console.log("\n3. 生成Groth16证明...");
    
    try {
        // 这里需要先完成trusted setup
        console.log("注意: 需要先运行trusted setup生成proving key和verification key");
        console.log("命令: snarkjs powersoftau new bn128 12 pot12_0000.ptau");
        console.log("      snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau");
        console.log("      snarkjs powersoftau prepare phase2 pot12_0001.ptau pot12_final.ptau");
        console.log("      snarkjs groth16 setup simple_poseidon2.r1cs pot12_final.ptau simple_poseidon2_0000.zkey");
        console.log("      snarkjs zkey contribute simple_poseidon2_0000.zkey simple_poseidon2_0001.zkey");
        console.log("      snarkjs zkey export verificationkey simple_poseidon2_0001.zkey verification_key.json");
        
    } catch (error) {
        console.error("证明生成失败:", error);
    }
}

// 主测试函数
async function main() {
    try {
        const testResult = await testPoseidon2();
        await generateProof();
        
        console.log("\n测试完成!");
        console.log("原象:", testResult.preimage);
        console.log("哈希值:", testResult.hashValue);
        
    } catch (error) {
        console.error("测试失败:", error);
    }
}

if (require.main === module) {
    main();
}

module.exports = { testPoseidon2, calculateSimplePoseidon2Hash };
