# Test API
import requests
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 测试RAG API
print("=== 测试RAG知识图谱API (5001) ===")
try:
    r = requests.get("http://49.235.105.137:5001/health", timeout=10)
    print(f"健康检查: {r.json()}")
except Exception as e:
    print(f"错误: {e}")

print("\n=== 测试文档知识API (5002) ===")
try:
    r = requests.get("http://49.235.105.137:5002/health", timeout=10)
    print(f"健康检查: {r.json()}")
except Exception as e:
    print(f"错误: {e}")

print("\n=== 测试管理员API (5005) ===")
try:
    r = requests.get("http://49.235.105.137:5005/health", timeout=10)
    print(f"健康检查: {r.json()}")
except Exception as e:
    print(f"错误: {e}")
