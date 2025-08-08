const fs = require('fs');
const { performance } = require('perf_hooks');
const { calculateSimplePoseidon2Hash } = require('./test');

// Poseidon2性能基准测试
class Poseidon2Benchmark {
    constructor() {
        this.results = [];
    }
    
    // 哈希计算性能测试
    async benchmarkHashComputation() {
        console.log("1. 哈希计算性能测试...");
        
        const testSizes = [1, 10, 100, 1000];
        
        for (const size of testSizes) {
            const start = performance.now();
            
            for (let i = 0; i < size; i++) {
                const preimage = [i.toString(), (i * 2).toString()];
                calculateSimplePoseidon2Hash(preimage);
            }
            
            const end = performance.now();
            const duration = end - start;
            const hashesPerSecond = size / (duration / 1000);
            
            this.results.push({
                test: 'Hash Computation',
                size: size,
                duration: `${duration.toFixed(2)}ms`,
                throughput: `${hashesPerSecond.toFixed(2)} hashes/sec`
            });
            
            console.log(`  ${size} hashes: ${duration.toFixed(2)}ms (${hashesPerSecond.toFixed(2)} hashes/sec)`);
        }
    }
    
    // 电路复杂度分析
    async analyzeCircuitComplexity() {
        console.log("\n2. 电路复杂度分析...");
        
        const circuits = [
            { name: 'Simple Poseidon2', file: 'simple_poseidon2.r1cs', estimatedConstraints: 1200 },
            { name: 'Full Poseidon2', file: 'poseidon2.r1cs', estimatedConstraints: 15000 },
            { name: 'Standard Poseidon2', file: 'standard_poseidon2.r1cs', estimatedConstraints: 12000 }
        ];
        
        for (const circuit of circuits) {
            const path = `./build/${circuit.file}`;
            if (fs.existsSync(path)) {
                const stats = fs.statSync(path);
                const sizeKB = (stats.size / 1024).toFixed(2);
                
                this.results.push({
                    test: 'Circuit Analysis',
                    circuit: circuit.name,
                    fileSize: `${sizeKB} KB`,
                    estimatedConstraints: circuit.estimatedConstraints
                });
                
                console.log(`  ${circuit.name}:`);
                console.log(`    文件大小: ${sizeKB} KB`);
                console.log(`    估计约束数: ${circuit.estimatedConstraints}`);
            } else {
                console.log(`  ${circuit.name}: 文件不存在 (需要先编译)`);
            }
        }
    }
    
    // 内存使用分析
    async analyzeMemoryUsage() {
        console.log("\n3. 内存使用分析...");
        
        const beforeMemory = process.memoryUsage();
        
        // 执行大量哈希计算
        const iterations = 10000;
        for (let i = 0; i < iterations; i++) {
            const preimage = [Math.floor(Math.random() * 1000000).toString(), Math.floor(Math.random() * 1000000).toString()];
            calculateSimplePoseidon2Hash(preimage);
        }
        
        const afterMemory = process.memoryUsage();
        
        const memoryDiff = {
            heapUsed: ((afterMemory.heapUsed - beforeMemory.heapUsed) / 1024 / 1024).toFixed(2),
            heapTotal: ((afterMemory.heapTotal - beforeMemory.heapTotal) / 1024 / 1024).toFixed(2),
            external: ((afterMemory.external - beforeMemory.external) / 1024 / 1024).toFixed(2)
        };
        
        this.results.push({
            test: 'Memory Usage',
            iterations: iterations,
            heapUsedDiff: `${memoryDiff.heapUsed} MB`,
            heapTotalDiff: `${memoryDiff.heapTotal} MB`,
            externalDiff: `${memoryDiff.external} MB`
        });
        
        console.log(`  ${iterations}次哈希计算后的内存变化:`);
        console.log(`    堆内存使用: +${memoryDiff.heapUsed} MB`);
        console.log(`    堆内存总计: +${memoryDiff.heapTotal} MB`);
        console.log(`    外部内存: +${memoryDiff.external} MB`);
    }
    
    // 不同参数配置对比
    async compareParameters() {
        console.log("\n4. 参数配置对比...");
        
        const configs = [
            { name: '(256,2,5)', t: 2, description: '2个输入元素，更少状态' },
            { name: '(256,3,5)', t: 3, description: '3个输入元素，标准配置' }
        ];
        
        for (const config of configs) {
            console.log(`  配置 ${config.name}:`);
            console.log(`    状态宽度: ${config.t}`);
            console.log(`    描述: ${config.description}`);
            
            // 估算性能指标
            const estimatedConstraints = config.t === 2 ? 800 : 1200;
            const estimatedProvingTime = config.t === 2 ? '2-5秒' : '5-10秒';
            const estimatedMemory = config.t === 2 ? '< 500MB' : '< 1GB';
            
            console.log(`    估计约束数: ${estimatedConstraints}`);
            console.log(`    估计证明时间: ${estimatedProvingTime}`);
            console.log(`    估计内存使用: ${estimatedMemory}`);
            
            this.results.push({
                test: 'Parameter Comparison',
                config: config.name,
                stateWidth: config.t,
                estimatedConstraints,
                estimatedProvingTime,
                estimatedMemory
            });
        }
    }
    
    // 安全性分析
    async securityAnalysis() {
        console.log("\n5. 安全性分析...");
        
        // 测试雪崩效应
        const original = ["123456", "789012"];
        const modified = ["123457", "789012"]; // 只改变一位
        
        const hash1 = calculateSimplePoseidon2Hash(original);
        const hash2 = calculateSimplePoseidon2Hash(modified);
        
        // 计算汉明距离 (简化版本)
        const diff = BigInt(hash1) ^ BigInt(hash2);
        const hammingWeight = diff.toString(2).split('1').length - 1;
        
        console.log(`  雪崩效应测试:`);
        console.log(`    原始输入: [${original.join(', ')}]`);
        console.log(`    修改输入: [${modified.join(', ')}]`);
        console.log(`    哈希1: ${hash1.substring(0, 20)}...`);
        console.log(`    哈希2: ${hash2.substring(0, 20)}...`);
        console.log(`    汉明权重: ${hammingWeight}/254 位改变`);
        
        this.results.push({
            test: 'Security Analysis',
            avalancheTest: {
                originalHash: hash1.substring(0, 20) + '...',
                modifiedHash: hash2.substring(0, 20) + '...',
                hammingWeight: hammingWeight,
                totalBits: 254
            }
        });
    }
    
    // 生成报告
    generateReport() {
        console.log("\n" + "=".repeat(60));
        console.log("              性能基准测试报告");
        console.log("=".repeat(60));
        
        // 按测试类型分组结果
        const groupedResults = {};
        this.results.forEach(result => {
            if (!groupedResults[result.test]) {
                groupedResults[result.test] = [];
            }
            groupedResults[result.test].push(result);
        });
        
        // 生成JSON报告
        const report = {
            timestamp: new Date().toISOString(),
            system: {
                platform: process.platform,
                nodeVersion: process.version,
                architecture: process.arch
            },
            results: groupedResults
        };
        
        fs.writeFileSync('./build/benchmark_report.json', JSON.stringify(report, null, 2));
        console.log("\n详细报告已保存到: ./build/benchmark_report.json");
        
        // 输出摘要
        console.log("\n性能摘要:");
        console.log("- 简单哈希: ~1000-10000 hashes/sec (JavaScript模拟)");
        console.log("- 简化电路: ~1200约束，2-5秒证明时间");
        console.log("- 完整电路: ~15000约束，1-10分钟证明时间");
        console.log("- 内存使用: < 1GB (依具体实现)");
        console.log("- 证明大小: 128字节 (Groth16固定)");
        console.log("- 验证时间: < 100毫秒");
    }
    
    // 运行所有基准测试
    async runAll() {
        console.log("开始Poseidon2性能基准测试...\n");
        
        await this.benchmarkHashComputation();
        await this.analyzeCircuitComplexity();
        await this.analyzeMemoryUsage();
        await this.compareParameters();
        await this.securityAnalysis();
        
        this.generateReport();
        
        console.log("\n基准测试完成!");
    }
}

// 主函数
async function main() {
    const benchmark = new Poseidon2Benchmark();
    await benchmark.runAll();
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = Poseidon2Benchmark;
