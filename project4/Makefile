CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -g
INCLUDES = -Iinclude
SRCDIR = src
TESTDIR = test
BUILDDIR = build
OBJDIR = $(BUILDDIR)/obj

# 源文件
SOURCES = $(SRCDIR)/sm3.c
OBJECTS = $(OBJDIR)/sm3.o

# 测试文件
TEST_SOURCES = $(TESTDIR)/test_sm3.c
BENCHMARK_SOURCES = $(TESTDIR)/benchmark.c

# 目标文件
TARGETS = $(BUILDDIR)/test_sm3 $(BUILDDIR)/benchmark $(BUILDDIR)/example

# 库文件
LIBSM3 = $(BUILDDIR)/libsm3.a

.PHONY: all clean test benchmark lib help example

# 默认目标
all: $(TARGETS) $(LIBSM3)

# 创建目录
$(OBJDIR):
	mkdir -p $(OBJDIR)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

# 编译源文件
$(OBJDIR)/sm3.o: $(SRCDIR)/sm3.c include/sm3.h | $(OBJDIR)
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# 创建静态库
$(LIBSM3): $(OBJECTS) | $(BUILDDIR)
	ar rcs $@ $(OBJECTS)
	ranlib $@

# 编译测试程序
$(BUILDDIR)/test_sm3: $(TEST_SOURCES) $(LIBSM3) | $(BUILDDIR)
	$(CC) $(CFLAGS) $(INCLUDES) $< -L$(BUILDDIR) -lsm3 -o $@

# 编译性能测试程序
$(BUILDDIR)/benchmark: $(BENCHMARK_SOURCES) $(LIBSM3) | $(BUILDDIR)
	$(CC) $(CFLAGS) $(INCLUDES) $< -L$(BUILDDIR) -lsm3 -o $@

# 编译示例程序
$(BUILDDIR)/example: example.c $(LIBSM3) | $(BUILDDIR)
	$(CC) $(CFLAGS) $(INCLUDES) $< -L$(BUILDDIR) -lsm3 -o $@

# 运行测试
test: $(BUILDDIR)/test_sm3
	@echo "运行SM3测试..."
	./$(BUILDDIR)/test_sm3

# 运行性能测试
benchmark: $(BUILDDIR)/benchmark
	@echo "运行SM3性能测试..."
	./$(BUILDDIR)/benchmark

# 运行示例程序
example: $(BUILDDIR)/example
	@echo "运行SM3示例程序..."
	./$(BUILDDIR)/example

# 编译库
lib: $(LIBSM3)

# 安装库和头文件（可选）
install: $(LIBSM3)
	@echo "安装库和头文件..."
	sudo cp $(LIBSM3) /usr/local/lib/
	sudo cp include/sm3.h /usr/local/include/
	sudo ldconfig

# 清理编译文件
clean:
	rm -rf $(BUILDDIR)

# 显示帮助信息
help:
	@echo "SM3哈希算法 Makefile"
	@echo ""
	@echo "可用目标:"
	@echo "  all        - 编译所有目标（默认）"
	@echo "  lib        - 编译静态库"
	@echo "  test       - 编译并运行测试程序"
	@echo "  benchmark  - 编译并运行性能测试"
	@echo "  example    - 编译并运行示例程序"
	@echo "  install    - 安装库和头文件到系统目录"
	@echo "  clean      - 清理编译文件"
	@echo "  help       - 显示此帮助信息"
	@echo ""
	@echo "编译选项:"
	@echo "  DEBUG=1    - 启用调试模式"
	@echo "  OPTIMIZE=0 - 禁用优化"
	@echo ""
	@echo "示例:"
	@echo "  make all"
	@echo "  make test"
	@echo "  make DEBUG=1 test"
	@echo "  make clean"

# 调试模式
ifdef DEBUG
CFLAGS += -DDEBUG -O0
endif

# 优化选项
ifdef OPTIMIZE
ifeq ($(OPTIMIZE),0)
CFLAGS = $(filter-out -O2,$(CFLAGS)) -O0
endif
endif

# 依赖关系
$(OBJECTS): include/sm3.h
