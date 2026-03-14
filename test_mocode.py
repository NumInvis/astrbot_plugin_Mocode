#!/usr/bin/env python3
"""Mocode 插件深度测试"""

import asyncio
import tempfile
import os
import subprocess
import shutil

async def test_mocode():
    timeout_seconds = 10
    
    # 测试 1: 检查 Docker
    print("=" * 50)
    print("测试 1: 检查 Docker 是否可用")
    print("=" * 50)
    try:
        result = subprocess.run(
            ["docker", "version"], 
            capture_output=True, 
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Docker 可用")
        else:
            print(f"❌ Docker 返回错误: {result.stderr}")
            return
    except Exception as e:
        print(f"❌ Docker 检查失败: {e}")
        return
    
    # 测试 2: 确保镜像
    print("\n" + "=" * 50)
    print("测试 2: 确保 Python 镜像存在")
    print("=" * 50)
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "python:3.12-slim"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout.strip():
            print("✅ Python 镜像已存在")
        else:
            print("⚠️ 需要拉取 Python 镜像...")
            result = subprocess.run(
                ["docker", "pull", "python:3.12-slim"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print("✅ Python 镜像拉取成功")
            else:
                print(f"❌ 镜像拉取失败: {result.stderr}")
                return
    except Exception as e:
        print(f"❌ 镜像检查失败: {e}")
        return
    
    # 测试 3: 执行简单代码
    print("\n" + "=" * 50)
    print("测试 3: 执行简单代码")
    print("=" * 50)
    code = 'print("Hello from Mocode!")'
    result = await run_code_in_docker(code, "", timeout_seconds)
    print(f"代码: {code}")
    print(f"结果: {result}")
    if result.get('error'):
        print(f"❌ 执行失败: {result['error']}")
    else:
        print(f"✅ 执行成功")
        print(f"   stdout: {result.get('stdout', '')}")
        print(f"   stderr: {result.get('stderr', '')}")
    
    # 测试 4: 执行计算
    print("\n" + "=" * 50)
    print("测试 4: 执行计算")
    print("=" * 50)
    code = 'x = sum(range(100)); print(f"Sum: {x}")'
    result = await run_code_in_docker(code, "", timeout_seconds)
    print(f"代码: {code}")
    if result.get('error'):
        print(f"❌ 执行失败: {result['error']}")
    else:
        print(f"✅ 执行成功")
        print(f"   stdout: {result.get('stdout', '')}")
    
    # 测试 5: 测试输入
    print("\n" + "=" * 50)
    print("测试 5: 测试输入")
    print("=" * 50)
    code = 'print(input())'
    input_text = "Hello from input!"
    result = await run_code_in_docker(code, input_text, timeout_seconds)
    print(f"代码: {code}")
    print(f"输入: {input_text}")
    if result.get('error'):
        print(f"❌ 执行失败: {result['error']}")
    else:
        print(f"✅ 执行成功")
        print(f"   stdout: {result.get('stdout', '')}")
    
    # 测试 6: 测试超时
    print("\n" + "=" * 50)
    print("测试 6: 测试超时")
    print("=" * 50)
    code = 'import time; time.sleep(20)'
    result = await run_code_in_docker(code, "", 3)  # 3秒超时
    print(f"代码: {code}")
    if "超时" in result.get('stderr', '') or result.get('error'):
        print(f"✅ 超时正常工作")
    else:
        print(f"⚠️ 超时可能有问题")
    print(f"   stderr: {result.get('stderr', '')}")
    
    # 测试 7: 测试危险代码（文件写入）
    print("\n" + "=" * 50)
    print("测试 7: 测试危险代码（文件写入）")
    print("=" * 50)
    code = 'open("/tmp/test.txt", "w").write("test")'
    result = await run_code_in_docker(code, "", timeout_seconds)
    print(f"代码: {code}")
    if "Read-only file system" in result.get('stderr', '') or result.get('error'):
        print(f"✅ 只读文件系统阻止了写入")
    else:
        print(f"⚠️ 可能有问题")
    print(f"   stderr: {result.get('stderr', '')}")
    
    # 测试 8: 测试网络隔离
    print("\n" + "=" * 50)
    print("测试 8: 测试网络隔离")
    print("=" * 50)
    code = 'import urllib.request; urllib.request.urlopen("http://example.com")'
    result = await run_code_in_docker(code, "", timeout_seconds)
    print(f"代码: {code}")
    if result.get('stderr') or result.get('error'):
        print(f"✅ 网络隔离正常工作（无法访问外部网络）")
    else:
        print(f"⚠️ 网络隔离可能有问题")
    print(f"   stderr: {result.get('stderr', '')}")
    
    print("\n" + "=" * 50)
    print("✅ 所有测试完成！")
    print("=" * 50)

async def run_code_in_docker(code: str, input_text: str, timeout: int):
    """在 Docker 中运行代码"""
    temp_dir = tempfile.mkdtemp(prefix="mocode_")
    
    try:
        # 写入代码文件
        code_file = os.path.join(temp_dir, "main.py")
        with open(code_file, 'w') as f:
            f.write(code)
        
        # 写入输入文件
        input_file = os.path.join(temp_dir, "input.txt")
        with open(input_file, 'w') as f:
            f.write(input_text or "")
        
        # 构建 Docker 命令
        docker_cmd = [
            "docker", "run", "--rm",
            "--read-only",
            "--network", "none",
            "--memory", "8m",
            "--memory-swap", "8m",
            "--cpus", "0.1",
            "--pids-limit", "10",
            "-v", f"{temp_dir}:/code:ro",
            "-w", "/code",
            "python:3.12-slim",
            "python", "-c",
            f"import sys; sys.stdin = open('/code/input.txt'); exec(open('/code/main.py').read())"
        ]
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": None if result.returncode == 0 else f"Exit code: {result.returncode}"
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"执行超时（超过 {timeout} 秒）",
                "error": "Timeout"
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": "",
                "error": str(e)
            }
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

# 运行测试
if __name__ == "__main__":
    asyncio.run(test_mocode())
