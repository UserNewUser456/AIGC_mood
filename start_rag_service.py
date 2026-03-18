#!/usr/bin/env python3
"""
启动RAG知识图谱服务的脚本
"""
import subprocess
import sys
import os

def start_rag_service():
    """启动RAG知识图谱服务"""
    try:
        # 切换到项目目录
        os.chdir("d:/shixi/AIGC_mood/AIGC_mood")
        
        # 启动RAG服务
        print("正在启动RAG知识图谱服务...")
        subprocess.run([sys.executable, "my_rag_knowledge_api.py"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"启动服务失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    start_rag_service()