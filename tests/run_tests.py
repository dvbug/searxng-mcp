"""
本地测试运行指南和测试脚本
"""

# pytest.ini 配置已经在 pyproject.toml 中定义
# 本文件提供额外的测试运行说明

import subprocess
import sys
from pathlib import Path


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("运行所有测试")
    print("=" * 70)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=short"],
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode


def run_tests_with_coverage():
    """运行所有测试并生成覆盖率报告"""
    print("=" * 70)
    print("运行测试并生成覆盖率报告")
    print("=" * 70)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-v",
            "--cov=mcp_server",
            "--cov-report=html",
            "--cov-report=term-missing",
        ],
        cwd=Path(__file__).parent.parent,
    )
    print("\n覆盖率报告已生成到 htmlcov/index.html")
    return result.returncode


def run_specific_test_file(test_file):
    """运行特定测试文件"""
    print(f"=" * 70)
    print(f"运行测试文件: {test_file}")
    print("=" * 70)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", f"tests/{test_file}"],
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode


def run_specific_test_class(test_file, test_class):
    """运行特定测试类"""
    print(f"=" * 70)
    print(f"运行测试: {test_file}::{test_class}")
    print("=" * 70)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", f"tests/{test_file}::{test_class}"],
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode


def run_tests_matching_keyword(keyword):
    """运行匹配关键词的测试"""
    print(f"=" * 70)
    print(f"运行包含关键词的测试: {keyword}")
    print("=" * 70)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "-k", keyword],
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="测试运行脚本")
    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有测试",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="运行测试并生成覆盖率报告",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="运行特定测试文件（例如：test_main.py）",
    )
    parser.add_argument(
        "--class",
        type=str,
        dest="test_class",
        help="运行特定测试类（需要配合 --file）",
    )
    parser.add_argument(
        "--keyword",
        "-k",
        type=str,
        help="运行匹配关键词的测试",
    )

    args = parser.parse_args()

    if args.all:
        sys.exit(run_all_tests())
    elif args.coverage:
        sys.exit(run_tests_with_coverage())
    elif args.file:
        if args.test_class:
            sys.exit(run_specific_test_class(args.file, args.test_class))
        else:
            sys.exit(run_specific_test_file(args.file))
    elif args.keyword:
        sys.exit(run_tests_matching_keyword(args.keyword))
    else:
        # 默认运行所有测试
        sys.exit(run_all_tests())
