CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O3 -g
SIMD_FLAGS = -msse2 -mavx2 -march=native
INCLUDES = -Iinclude

# 基础目标
all: build/libsm3.a build/test_sm3

# 优化目标
opt: build/libsm3_opt.a build/test_sm3_opt

build/obj:
	mkdir -p build/obj

build/obj/sm3.o: src/sm3.c include/sm3.h | build/obj
	$(CC) $(CFLAGS) $(INCLUDES) -c src/sm3.c -o build/obj/sm3.o

build/libsm3.a: build/obj/sm3.o
	mkdir -p build
	ar rcs build/libsm3.a build/obj/sm3.o

build/test_sm3: test/test_sm3.c build/libsm3.a
	mkdir -p build
	$(CC) $(CFLAGS) $(INCLUDES) test/test_sm3.c -Lbuild -lsm3 -o build/test_sm3

# 优化版本编译规则
build/obj/sm3_opt.o: src/sm3_opt.c include/sm3_opt.h include/sm3.h | build/obj
	$(CC) $(CFLAGS) $(SIMD_FLAGS) $(INCLUDES) -c src/sm3_opt.c -o build/obj/sm3_opt.o

build/obj/sm3_multiway.o: src/sm3_multiway.c include/sm3_opt.h | build/obj
	$(CC) $(CFLAGS) $(SIMD_FLAGS) $(INCLUDES) -c src/sm3_multiway.c -o build/obj/sm3_multiway.o

build/obj/sm3_benchmark.o: src/sm3_benchmark.c include/sm3_opt.h | build/obj
	$(CC) $(CFLAGS) $(SIMD_FLAGS) $(INCLUDES) -c src/sm3_benchmark.c -o build/obj/sm3_benchmark.o

build/libsm3_opt.a: build/obj/sm3.o build/obj/sm3_opt.o build/obj/sm3_multiway.o build/obj/sm3_benchmark.o
	mkdir -p build
	ar rcs build/libsm3_opt.a build/obj/sm3.o build/obj/sm3_opt.o build/obj/sm3_multiway.o build/obj/sm3_benchmark.o

build/test_sm3_opt: test/test_sm3_opt.c build/libsm3_opt.a
	mkdir -p build
	$(CC) $(CFLAGS) $(SIMD_FLAGS) $(INCLUDES) test/test_sm3_opt.c -Lbuild -lsm3_opt -o build/test_sm3_opt

test: build/test_sm3
	./build/test_sm3

# 优化版本测试
test-opt: build/test_sm3_opt
	./build/test_sm3_opt --all

benchmark: build/test_sm3_opt
	./build/test_sm3_opt --bench

simd-info: build/test_sm3_opt
	./build/test_sm3_opt | head -10

clean:
	rm -rf build

.PHONY: all opt test test-opt benchmark simd-info clean