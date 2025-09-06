# Mini Tool Makefile
# 简化常用开发操作

.PHONY: help install test test-unit test-integration coverage lint format type-check clean build docs run-example

# 默认目标
help:
	@echo "Mini Tool - 可用命令:"
	@echo ""
	@echo "  install         安装开发依赖"
	@echo "  test            运行所有测试"
	@echo "  test-unit       运行单元测试"
	@echo "  test-integration 运行集成测试"
	@echo "  coverage        运行测试并生成覆盖率报告"
	@echo "  lint            代码检查"
	@echo "  format          格式化代码"
	@echo "  type-check      类型检查"
	@echo "  clean           清理临时文件"
	@echo "  build           构建包"
	@echo "  run-example     运行演示程序"
	@echo "  ci-check        CI 全面检查"

# 安装开发依赖
install:
	pip install -e ".[dev]"

# 运行所有测试
test:
	pytest -v

# 运行单元测试
test-unit:
	pytest -v -m unit

# 运行集成测试
test-integration:
	pytest -v -m integration

# 运行测试并生成覆盖率报告
coverage:
	pytest --cov=core --cov-report=html --cov-report=term-missing --cov-report=xml

# 代码检查
lint:
	flake8 core example test
	@echo "✅ Linting passed"

# 格式化代码
format:
	black core example test
	isort core example test
	@echo "✅ Code formatted"

# 类型检查
type-check:
	mypy core example
	@echo "✅ Type checking passed"

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml .pytest_cache/ .mypy_cache/
	@echo "✅ Cleanup completed"

# 构建包
build:
	python -m build

# 运行演示程序
run-example:
	python example/ecdhe_demo.py

# CI 全面检查 (本地模拟 CI)
ci-check: format lint type-check coverage
	@echo "🎉 所有检查通过！代码可以提交"

# 快速检查 (提交前)
quick-check: lint test-unit
	@echo "✅ 快速检查通过"
