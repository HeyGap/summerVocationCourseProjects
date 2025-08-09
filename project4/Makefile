CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O3 -g
SIMD_FLAGS = -msse2 -mavx2 -march=native
INCLUDES = -Iinclude

# 基础目标
all: build/libsm3.a build/test_sm3 build/length_extension_attack build/simple_attack_demo build/test_merkle_tree

# 优化目标
opt: build/libsm3_opt.a build/test_sm3_opt

build/merkle_demo: merkle_demo.c build/libsm3_merkle.a
	mkdir -p build
	$(CC) $(CFLAGS) $(INCLUDES) merkle_demo.c -Lbuild -lsm3_merkle -lm -o build/merkle_demo

# Merkle树目标
merkle: build/test_merkle_tree build/merkle_demo

build/obj:
	mkdir -p build/obj

build/obj/sm3.o: src/sm3.c include/sm3.h | build/obj
	$(CC) $(CFLAGS) $(INCLUDES) -c src/sm3.c -o build/obj/sm3.o

build/obj/merkle_tree.o: src/merkle_tree.c include/merkle_tree.h include/sm3.h | build/obj
	$(CC) $(CFLAGS) $(INCLUDES) -c src/merkle_tree.c -o build/obj/merkle_tree.o

build/libsm3_merkle.a: build/obj/sm3.o build/obj/merkle_tree.o
	mkdir -p build
	ar rcs build/libsm3_merkle.a build/obj/sm3.o build/obj/merkle_tree.o

build/test_merkle_tree: test_merkle_tree.c build/libsm3_merkle.a
	mkdir -p build
	$(CC) $(CFLAGS) $(INCLUDES) test_merkle_tree.c -Lbuild -lsm3_merkle -lm -o build/test_merkle_tree

build/libsm3.a: build/obj/sm3.o
	mkdir -p build
	ar rcs build/libsm3.a build/obj/sm3.o

build/test_sm3: test/test_sm3.c build/libsm3.a
	mkdir -p build
	$(CC) $(CFLAGS) $(INCLUDES) test/test_sm3.c -Lbuild -lsm3 -o build/test_sm3

build/length_extension_attack: length_extension_attack.c build/libsm3.a
	mkdir -p build
	$(CC) $(CFLAGS) $(INCLUDES) length_extension_attack.c -Lbuild -lsm3 -o build/length_extension_attack

build/simple_attack_demo: simple_attack_demo.c build/libsm3.a
	mkdir -p build
	$(CC) $(CFLAGS) $(INCLUDES) simple_attack_demo.c -Lbuild -lsm3 -o build/simple_attack_demo

# 优化版本编译规则
build/obj/sm3_opt.o: src/sm3_opt.c include/sm3_opt.h include/sm3.h | build/obj
	$(CC) $(CFLAGS) $(SIMD_FLAGS) $(INCLUDES) -c src/sm3_opt.c -o build/obj/sm3_opt.o

build/obj/sm3_multiway.o: src/sm3_multiway.c include/sm3_opt.h | build/obj
	$(CC) $(CFLAGS) $(SIMD_FLAGS) $(INCLUDES) -c src/sm3_multiway.c -o build/obj/sm3_multiway.o

build/obj/sm3_benchmark.o: src/sm3_benchmark.c include/sm3_opt.h | build/obj
	$(CC) $(CFLAGS) $(SIMD_FLAGS) $(INCLUDES) -c src/sm3_benchmark.c -o build/obj/sm3_benchmark.o

build/obj/sm3_fast.o: src/sm3_fast.c include/sm3_opt.h | build/obj
	$(CC) $(CFLAGS) $(SIMD_FLAGS) $(INCLUDES) -c src/sm3_fast.c -o build/obj/sm3_fast.o

build/libsm3_opt.a: build/obj/sm3.o build/obj/sm3_opt.o build/obj/sm3_multiway.o build/obj/sm3_benchmark.o build/obj/sm3_fast.o
	mkdir -p build
	ar rcs build/libsm3_opt.a build/obj/sm3.o build/obj/sm3_opt.o build/obj/sm3_multiway.o build/obj/sm3_benchmark.o build/obj/sm3_fast.o

build/test_sm3_opt: test/test_sm3_opt.c build/libsm3_opt.a
	mkdir -p build
	$(CC) $(CFLAGS) $(SIMD_FLAGS) $(INCLUDES) test/test_sm3_opt.c -Lbuild -lsm3_opt -o build/test_sm3_opt

build/simple_perf_test: test/simple_perf_test.c build/libsm3_opt.a
	mkdir -p build
	$(CC) $(CFLAGS) $(SIMD_FLAGS) $(INCLUDES) test/simple_perf_test.c -Lbuild -lsm3_opt -o build/simple_perf_test

test: build/test_sm3
	./build/test_sm3

# 长度扩展攻击演示
attack: build/length_extension_attack
	./build/length_extension_attack

# 简化攻击演示
demo: build/simple_attack_demo
	./build/simple_attack_demo

# 优化版本测试
test-opt: build/test_sm3_opt
	./build/test_sm3_opt --all

# 简单性能测试
test-perf: build/simple_perf_test
	./build/simple_perf_test

benchmark: build/test_sm3_opt
	./build/test_sm3_opt --bench

simd-info: build/test_sm3_opt
	./build/test_sm3_opt | head -10

build/verify_merkle: verify_merkle.c build/libsm3_merkle.a
	mkdir -p build
	$(CC) $(CFLAGS) $(INCLUDES) verify_merkle.c -Lbuild -lsm3_merkle -lm -o build/verify_merkle

# Merkle树验证测试
verify-merkle: build/verify_merkle
	./build/verify_merkle

# Merkle树测试
test-merkle: build/test_merkle_tree
	./build/test_merkle_tree

clean:
	rm -rf build

.PHONY: all opt merkle test attack demo test-opt benchmark simd-info test-merkle demo-merkle verify-merkle clean