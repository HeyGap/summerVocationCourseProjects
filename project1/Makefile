# SM4 Cryptographic Library Makefile
# Supports multiple optimization levels and cross-platform compilation

# 编译器设置
CC = gcc
CXX = g++

# 目录结构
SRC_DIR = src
INC_DIR = include
TEST_DIR = test
BUILD_DIR = build
OBJ_DIR = $(BUILD_DIR)/obj

# 源文件
BASIC_SRCS = $(SRC_DIR)/sm4_basic.c $(SRC_DIR)/utils.c
TTABLE_SRCS = $(BASIC_SRCS) $(SRC_DIR)/sm4_ttable.c
AESNI_SRCS = $(TTABLE_SRCS) $(SRC_DIR)/sm4_aesni.c
OPT_SRCS = $(SRC_DIR)/sm4_opt.c

# 所有源文件
ALL_SRCS = $(BASIC_SRCS) $(SRC_DIR)/sm4_ttable.c $(SRC_DIR)/sm4_aesni.c \
           $(OPT_SRCS)

# 测试源文件
TEST_SRCS = $(TEST_DIR)/test_sm4.c
BENCHMARK_SRCS = $(TEST_DIR)/benchmark.c

# 示例源文件
EXAMPLE_SRCS = $(EXAMPLE_DIR)/encrypt_file.c

# 目标文件
BASIC_OBJS = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(BASIC_SRCS))
TTABLE_OBJS = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(TTABLE_SRCS))
AESNI_OBJS = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(AESNI_SRCS))
ALL_OBJS = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(ALL_SRCS))

# 基础编译选项
CFLAGS = -Wall -Wextra -Wpedantic -std=c99 -I$(INC_DIR)
LDFLAGS = 

# Debug/Release 配置
ifdef DEBUG
    CFLAGS += -g -O0 -DDEBUG
    BUILD_TYPE = debug
else
    CFLAGS += -O3 -DNDEBUG -flto
    LDFLAGS += -flto
    BUILD_TYPE = release
endif

# 检测系统
UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)
UNAME_M := $(shell uname -m 2>/dev/null || echo x86_64)

# Windows 特殊处理
ifeq ($(OS),Windows_NT)
    EXEC_EXT = .exe
    RM = del /Q /F
    RMDIR = rmdir /Q /S
    MKDIR = mkdir
    # Windows 下检测是否在 MSYS2/MinGW 环境中
    ifdef MSYSTEM
        # MSYS2 环境
        SHELL = bash
    else
        # 原生 Windows
        SHELL = cmd
        PATH_SEP = \\
    endif
else
    EXEC_EXT =
    RM = rm -f
    RMDIR = rm -rf
    MKDIR = mkdir -p
    PATH_SEP = /
endif

# CPU 特性检测和优化选项
DETECTED_FEATURES := $(shell $(CC) -march=native -dM -E - < /dev/null 2>/dev/null | grep -E "__AES__|__VPCLMULQDQ__" | cut -d' ' -f2 | sort -u)

# 设置优化级别标志
HAS_AES := $(findstring __AES__,$(DETECTED_FEATURES))
HAS_VPCLMULQDQ := $(findstring __VPCLMULQDQ__,$(DETECTED_FEATURES))

# 优化级别特定的编译选项
BASIC_CFLAGS = $(CFLAGS) -DSM4_BASIC_ONLY
TTABLE_CFLAGS = $(CFLAGS) -DSM4_ENABLE_TTABLE
AESNI_CFLAGS = $(TTABLE_CFLAGS) -DSM4_ENABLE_AESNI -maes -msse4.1

# 默认目标
.PHONY: all
all: info libs tests

# 显示编译信息
.PHONY: info
info:
	@echo "=== SM4 Library Build Configuration ==="
	@echo "System: $(UNAME_S) $(UNAME_M)"
	@echo "Compiler: $(CC) $(shell $(CC) --version 2>/dev/null | head -1 || echo 'version unknown')"
	@echo "Build Type: $(BUILD_TYPE)"
	@echo "Detected CPU Features: $(if $(DETECTED_FEATURES),$(DETECTED_FEATURES),none)"
	@echo "AES-NI Support: $(if $(HAS_AES),Yes,No)"
	@echo "VPCLMULQDQ Support: $(if $(HAS_VPCLMULQDQ),Yes,No)"
	@echo "==========================================="

# 创建目录
$(BUILD_DIR) $(OBJ_DIR):
	@$(MKDIR) $@

# 编译规则 - 基础实现
$(OBJ_DIR)/sm4_basic.o: $(SRC_DIR)/sm4_basic.c | $(OBJ_DIR)
	$(CC) $(BASIC_CFLAGS) -c $< -o $@

$(OBJ_DIR)/utils.o: $(SRC_DIR)/utils.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# 编译规则 - T-table 优化
$(OBJ_DIR)/sm4_ttable.o: $(SRC_DIR)/sm4_ttable.c | $(OBJ_DIR)
	$(CC) $(TTABLE_CFLAGS) -c $< -o $@

# 编译规则 - AES-NI 优化
$(OBJ_DIR)/sm4_aesni.o: $(SRC_DIR)/sm4_aesni.c | $(OBJ_DIR)
ifneq ($(HAS_AES),)
	$(CC) $(AESNI_CFLAGS) -c $< -o $@
else
	$(CC) $(TTABLE_CFLAGS) -DSM4_NO_AESNI -c $< -o $@
endif

# 编译规则 - 优化框架
$(OBJ_DIR)/sm4_opt.o: $(SRC_DIR)/sm4_opt.c | $(OBJ_DIR)
	$(CC) $(AESNI_CFLAGS) -DSM4_ENABLE_ALL -c $< -o $@

# 静态库目标
.PHONY: libs
libs: $(BUILD_DIR)/libsm4_basic.a $(BUILD_DIR)/libsm4_ttable.a \
      $(BUILD_DIR)/libsm4_aesni.a $(BUILD_DIR)/libsm4_full.a

$(BUILD_DIR)/libsm4_basic.a: $(BASIC_OBJS) | $(BUILD_DIR)
	ar rcs $@ $^

$(BUILD_DIR)/libsm4_ttable.a: $(TTABLE_OBJS) | $(BUILD_DIR)
	ar rcs $@ $^

$(BUILD_DIR)/libsm4_aesni.a: $(AESNI_OBJS) | $(BUILD_DIR)
	ar rcs $@ $^

$(BUILD_DIR)/libsm4_full.a: $(ALL_OBJS) | $(BUILD_DIR)
	ar rcs $@ $^

# 测试程序
.PHONY: tests
tests: $(BUILD_DIR)/test_sm4$(EXEC_EXT) \
       $(BUILD_DIR)/benchmark$(EXEC_EXT)

$(BUILD_DIR)/test_sm4$(EXEC_EXT): $(TEST_DIR)/test_sm4.c $(BUILD_DIR)/libsm4_full.a | $(BUILD_DIR)
	$(CC) $(AESNI_CFLAGS) -DSM4_ENABLE_ALL $< -L$(BUILD_DIR) -lsm4_full -o $@ $(LDFLAGS)

$(BUILD_DIR)/benchmark$(EXEC_EXT): $(TEST_DIR)/benchmark.c $(BUILD_DIR)/libsm4_full.a | $(BUILD_DIR)
	$(CC) $(AESNI_CFLAGS) -DSM4_ENABLE_ALL $< -L$(BUILD_DIR) -lsm4_full -o $@ $(LDFLAGS)

$(BUILD_DIR)/encrypt_file$(EXEC_EXT): $(EXAMPLE_DIR)/encrypt_file.c $(BUILD_DIR)/libsm4_full.a | $(BUILD_DIR)
	$(CC) $(AESNI_CFLAGS) -DSM4_ENABLE_ALL $< -L$(BUILD_DIR) -lsm4_full -o $@ $(LDFLAGS)

# 运行测试
.PHONY: test
test: tests
	@echo "Running SM4 tests..."
	@$(BUILD_DIR)/test_sm4$(EXEC_EXT)

# 运行基准测试
.PHONY: benchmark
benchmark: $(BUILD_DIR)/benchmark$(EXEC_EXT)
	@echo "Running performance benchmarks..."
	@$(BUILD_DIR)/benchmark$(EXEC_EXT)

# 快速测试（仅基础功能）
.PHONY: quick-test
quick-test: $(BUILD_DIR)/test_sm4$(EXEC_EXT)
	@$(BUILD_DIR)/test_sm4$(EXEC_EXT) --quick

# 安装
PREFIX ?= /usr/local
INSTALL_INCLUDE_DIR = $(PREFIX)/include/sm4
INSTALL_LIB_DIR = $(PREFIX)/lib

.PHONY: install
install: libs
	@echo "Installing SM4 library to $(PREFIX)..."
	@$(MKDIR) $(INSTALL_INCLUDE_DIR) $(INSTALL_LIB_DIR) 2>/dev/null || true
	@cp $(INC_DIR)/*.h $(INSTALL_INCLUDE_DIR)/
	@cp $(BUILD_DIR)/libsm4_full.a $(INSTALL_LIB_DIR)/
	@echo "Installation completed."

# 卸载
.PHONY: uninstall
uninstall:
	@echo "Uninstalling SM4 library..."
	@$(RMDIR) $(INSTALL_INCLUDE_DIR) 2>/dev/null || true
	@$(RM) $(INSTALL_LIB_DIR)/libsm4_full.a 2>/dev/null || true
	@echo "Uninstallation completed."

# 清理
.PHONY: clean
clean:
	@echo "Cleaning build files..."
	@$(RMDIR) $(BUILD_DIR) 2>/dev/null || true

# 深度清理
.PHONY: distclean
distclean: clean
	@echo "Deep cleaning..."
	@$(RM) *.o *.a *$(EXEC_EXT) core* 2>/dev/null || true

# 代码格式化 (需要 clang-format)
.PHONY: format
format:
	@echo "Formatting code..."
	@find $(SRC_DIR) $(INC_DIR) $(TEST_DIR) $(EXAMPLE_DIR) -name "*.c" -o -name "*.h" | \
		xargs clang-format -i --style="{BasedOnStyle: LLVM, IndentWidth: 4, TabWidth: 4, UseTab: Never}"

# 代码检查 (需要 cppcheck)
.PHONY: check
check:
	@echo "Running static analysis..."
	@cppcheck --enable=all --std=c99 --platform=native \
		--suppress=missingIncludeSystem \
		--suppress=unusedFunction \
		-I$(INC_DIR) $(SRC_DIR)/ $(TEST_DIR)/ $(EXAMPLE_DIR)/

# 生成文档 (需要 doxygen)
.PHONY: docs
docs:
	@echo "Generating documentation..."
	@doxygen Doxyfile 2>/dev/null || echo "Doxygen not found or Doxyfile missing"

# 显示帮助
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all         - Build libraries and tests"
	@echo "  libs        - Build all library variants"
	@echo "  tests       - Build test programs"
	@echo "  test        - Run all tests"
	@echo "  benchmark   - Run performance benchmarks"
	@echo "  quick-test  - Run basic functionality tests"
	@echo "  install     - Install library and headers"
	@echo "  uninstall   - Remove installed files"
	@echo "  clean       - Remove build files"
	@echo "  distclean   - Remove all generated files"
	@echo "  format      - Format source code (requires clang-format)"
	@echo "  check       - Run static analysis (requires cppcheck)"
	@echo "  docs        - Generate documentation (requires doxygen)"
	@echo "  info        - Show build configuration"
	@echo "  help        - Show this help message"
	@echo ""
	@echo "Build options:"
	@echo "  DEBUG=1     - Enable debug build"
	@echo "  PREFIX=path - Set installation prefix (default: /usr/local)"

# 特殊目标
.PHONY: .SUFFIXES
.SUFFIXES:

# 防止同名文件干扰
.PHONY: all libs tests test benchmark install uninstall clean distclean info help
