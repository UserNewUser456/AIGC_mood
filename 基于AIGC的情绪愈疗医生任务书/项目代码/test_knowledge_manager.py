"""
知识库管理工具 - 快速测试脚本
演示如何使用知识库管理工具的各个功能
"""

from knowledge_manager import KnowledgeManager
import json

def test_basic_usage():
    """测试基本功能"""
    print("="*60)
    print("知识库管理工具 - 快速测试")
    print("="*60)

    # 1. 创建管理器实例
    print("\n[1] 创建知识库管理器...")
    manager = KnowledgeManager()

    # 2. 尝试加载已有向量库
    print("\n[2] 加载已有向量库...")
    manager.load_vector_db()

    # 3. 导入测试文本
    print("\n[3] 导入测试文本...")
    test_texts = [
        {
            "text": """
            焦虑症是一种常见的精神障碍，表现为过度的担忧和紧张。
            常见症状包括心悸、失眠、注意力不集中等。
            治疗方法包括认知行为疗法、药物治疗和放松训练。
            """,
            "title": "焦虑症简介",
            "source": "心理学教材"
        },
        {
            "text": """
            抑郁症是一种心境障碍，特征是持续的情绪低落和兴趣丧失。
            症状包括悲伤、疲劳、食欲改变、睡眠障碍等。
            常用治疗方法有抗抑郁药物、心理治疗和生活方式调整。
            """,
            "title": "抑郁症概述",
            "source": "心理健康指南"
        },
        {
            "text": """
            正念冥想是一种心理训练方法，有助于减轻压力和焦虑。
            通过专注于当下，观察自己的思绪和感受而不做判断。
            练习正念可以改善情绪调节能力，提升心理健康水平。
            """,
            "title": "正念冥想指南",
            "source": "自我疗愈手册"
        }
    ]

    for i, item in enumerate(test_texts, 1):
        print(f"\n  导入文本 {i}: {item['title']}")
        result = manager.import_text(
            text=item['text'],
            title=item['title'],
            source=item['source'],
            analyze=True  # 启用文本分析
        )
        if result['success']:
            print(f"  ✓ 成功: {result['message']}")
            # 显示分析结果
            if 'data' in result and 'analysis' in result['data']:
                analysis = result['data']['analysis']
                print(f"  关键词: {', '.join(analysis.get('keywords', []))}")
                print(f"  摘要: {analysis.get('summary', 'N/A')}")
        else:
            print(f"  ✗ 失败: {result.get('error', 'Unknown error')}")

    # 4. 搜索测试
    print("\n[4] 测试知识搜索...")
    test_queries = [
        "焦虑症状",
        "如何缓解抑郁",
        "心理治疗方法",
        "正念的好处"
    ]

    for query in test_queries:
        print(f"\n  查询: '{query}'")
        result = manager.search_knowledge(query, top_k=2)

        if result['success']:
            results = result['data']['results']
            print(f"  找到 {len(results)} 条相关内容:")
            for i, item in enumerate(results, 1):
                print(f"\n    [{i}] 相似度: {item['score']:.3f}")
                print(f"    标题: {item['metadata'].get('title', 'N/A')}")
                print(f"    内容: {item['text'][:100]}...")
        else:
            print(f"  ✗ 搜索失败: {result.get('error', 'Unknown error')}")

    # 5. 查看统计信息
    print("\n[5] 知识库统计信息...")
    result = manager.get_stats()
    if result['success']:
        data = result['data']
        print(f"  总文档数: {data['total_documents']}")
        print(f"  导入次数: {data['total_imports']}")
        if data['last_import']:
            print(f"  最后导入: {data['last_import']['title']}")

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


def test_file_import():
    """测试文件导入功能"""
    print("\n" + "="*60)
    print("文件导入测试")
    print("="*60)

    manager = KnowledgeManager()
    manager.load_vector_db()

    # 创建测试文件
    import os
    test_dir = "./test_data"
    os.makedirs(test_dir, exist_ok=True)

    test_file = os.path.join(test_dir, "test_article.txt")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""
        心理健康的维护与促进

        心理健康是整体健康的重要组成部分。
        保持心理健康的方法包括：

        1. 建立良好的社交关系
        2. 保持规律的作息时间
        3. 进行适度的体育锻炼
        4. 学习压力管理技巧
        5. 寻求专业帮助（如有需要）

        心理健康问题常见但不应被忽视。
        早期识别和干预可以有效预防问题恶化。
        """)

    print(f"\n[1] 导入测试文件: {test_file}")
    result = manager.import_file(test_file, analyze=True)

    if result['success']:
        print(f"  ✓ 成功: {result['message']}")
        if 'data' in result and 'analysis' in result['data']:
            analysis = result['data']['analysis']
            print(f"  关键词: {', '.join(analysis.get('keywords', []))}")
    else:
        print(f"  ✗ 失败: {result.get('error', 'Unknown error')}")

    # 清理测试文件
    # os.remove(test_file)
    # os.rmdir(test_dir)

    print("\n测试完成！")


def test_batch_import():
    """测试批量导入功能"""
    print("\n" + "="*60)
    print("批量导入测试")
    print("="*60)

    manager = KnowledgeManager()
    manager.load_vector_db()

    # 创建测试目录
    import os
    test_dir = "./test_books"
    os.makedirs(test_dir, exist_ok=True)

    # 创建多个测试文件
    test_files = [
        ("book1.txt", "情绪管理技巧\n情绪管理是心理健康的重要方面..."),
        ("book2.txt", "认知行为疗法\n认知行为疗法是一种有效的心理治疗方法..."),
        ("book3.txt", "压力应对策略\n面对压力时，我们可以采用多种应对策略...")
    ]

    print("\n[1] 创建测试文件...")
    for filename, content in test_files:
        filepath = os.path.join(test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  创建: {filename}")

    # 批量导入
    print(f"\n[2] 批量导入目录: {test_dir}")
    result = manager.import_directory(test_dir, analyze=True)

    if result['success']:
        data = result['data']
        print(f"  ✓ 成功导入: {data['success_count']} 个文件")
        print(f"  ✓ 失败: {data['fail_count']} 个文件")
        if data['errors']:
            print(f"  错误列表:")
            for error in data['errors']:
                print(f"    - {error}")
    else:
        print(f"  ✗ 失败: {result.get('error', 'Unknown error')}")

    # 清理测试文件
    # import shutil
    # shutil.rmtree(test_dir)

    print("\n测试完成！")


if __name__ == '__main__':
    print("\n选择测试模式:")
    print("1. 基本功能测试")
    print("2. 文件导入测试")
    print("3. 批量导入测试")
    print("4. 全部测试")

    choice = input("\n请输入选项 (1-4): ").strip()

    if choice == '1':
        test_basic_usage()
    elif choice == '2':
        test_file_import()
    elif choice == '3':
        test_batch_import()
    elif choice == '4':
        test_basic_usage()
        test_file_import()
        test_batch_import()
    else:
        print("无效选项，运行基本功能测试...")
        test_basic_usage()
