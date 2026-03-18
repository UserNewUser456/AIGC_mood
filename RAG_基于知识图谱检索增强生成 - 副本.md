# RAG_检索增强生成

<center>Copyright © xuanlian Technologies, Co., Ltd.
. All Rights Reserved</center>



## 1.文档介绍

​		本案例介绍RAG_检索增强生成技术，包括基础RAG和基于知识图谱的RAG。



## 2.产品开发环境

案例研发环境如下表

| **类型** | **工具与环境**                   |
| -------- | -------------------------------- |
| 开发工具 | 开发工具：PyCharm                |
| 技术运用 | 程序框架：python 3.10及以上      |
| 相关组件 | langchain和neo4j图数据库、olloma |



## 3.RAG介绍



传统的语言模型，比如 GPT-3.5，虽然在生成文本方面表现出色，但它们有一个显著的局限性：它们依赖于预训练的参数，无法动态访问外部知识。这意味着这些模型在处理实时信息、领域特定知识或罕见实体时表现不佳。举个例子，在问答任务中，模型可能会生成不准确或过时的答案，因为它无法访问最新的数据。就像你问一个朋友“今天天气怎么样？”，但他只能告诉你去年的天气情况，显然这样的信息对你来说毫无用处。这种局限性在需要精确答案的场景中尤为明显。例如，在医疗领域，医生可能需要最新的研究数据来做出诊断，而传统的语言模型无法提供这些信息。

RAG（Retrieval Augmented Generation）检索增强生成，即大模型LLM在回答问题或生成文本时，会先从大量的文档中检索出相关信息，然后基于这些检索出的信息进行回答或生成文本，从而可以提高回答的质量，而不是任由LLM来发挥。RAG技术使得开发者没有必要为每个特定的任务重新训练整个大模型，只需要外挂上相关知识库就可以，即可为模型提供额外的信息输入，提高回答的准确性。 

目的是解决大模型幻觉问题。



## 4 基础RAG

### 4.1 工具准备

安装必要的库。

```python
pip install langchain langchain-openai langchain-community
```



安装本地嵌入模型

先下载模型本地部署工具：olloma，下载地址：https://ollama.com/  点击download按钮下载后安装。

下载嵌入模型，在命令行执行：ollama pull nomic-embed-text

然后使用命令行ollama  list是否安装成功

准备一个大模型api的密钥，可以是deepseek或者openai的key

### 4.2 创建知识库

我们使用一个公司介绍的示例文本，用代码将文本内容保存为txt，并用langchain的TextLoader进行加载

```python
def load_and_process_data():
    """加载文档并分割成块"""
    # 使用示例文本内容
    text = """
公司介绍
武汉学链科有限公司，是国家认定的高新技术企业、教育部软件工程专业大学生实习实训基地、武汉市大学生实习实训基地，入选第十四届3551光谷人才计划，提供大数据分析平台、AI实训平台、DevOps实践案例库等产品，并为政企客户提供大数据、人工智能等数字化、智能化技术创新研发服务。
学链科技创新产学合作模式，依托AI实训平台、案例库，提供数智人才实践能力培养解决方案，公司与上海交通大学、华中科技大学、武汉大学、重庆大学等三十多所"双一流"高校开展了密切合作，并获得了多项省部级教学成果，着力打造互联网+教育生态，IT人才供应链。

学链科技以社会化协作的模式，建立涵盖金融、通信、企业管理、物流、制造等多行业的企业项目案例及实践知识库，同时搭建跨区域的软件工程实践平台，实现高校人才培养体系与企业需求的无缝对接，并通过创意工厂把社会化创意、企业研发项目引入高校，帮助大学生在课程知识学习、工程实践的同时，开发适应社会需求的软件产品。
学链科技始终关注用户对于知识传播和学习的需求，不断推出基于知识搜索的各种智能教育产品，与学校、企业、培训机构共同打造垂直领域的知识库和智能平台，按照自适应教学的核心理念，实现个性化的、混合式的教育模式，并为用户提供可不断延伸的终身教育网络。
"知识凝聚价值"是公司的核心价值观。

1)云上学链智慧教育平台
公司在IT教育领域耕耘多年，专注于网络教育系列产品的研发，目前具有自主知识产权的网络教育产品"智慧教育平台"已成功应用于全国像"北京交通大学"、"武汉大学"、"郑州大学"、"东莞理工学院"等十多所知名高等院校，在网络教育平台运营与合作方面积累了丰富的经验。
云上学链智慧教育平台，提供在线课程学习、实践案例学习，以及工程实践管理、实践过程管理等功能。平台提供了一系列功能用于完成实训教学任务所需筹备、布置的工作事宜。教师可以使用资源管理功能实现教学资源的共享，在教学过程跟踪和总结方面，教师可以通过集中管理、分布式统计的功能，更好地把握每位同学的学习进度，以便及时发现问题并敦促学生跟进。

2)创新性工程型人才实践能力培养解决方案
学链科技是创新性工程型人才培养解决方案服务商，经过多年的时间与沉淀，打造了内容详尽的实践项目案例库和层次化工程实践体系，与高校课程体系无缝衔接，紧扣教学计划，帮助高校改进时间和教学环节，沉淀教改成果，提升人才培养质量。通过完整、全面的实践案例和学习资源，让老师轻松成为项目经理，掌控项目实践，开展混合式教学。学生通过工程实践训练，较大地提高工程意识、实践能力、创新能力。

3)案例库平台
我们为案例实践打造了"DevOps工程实践案例库平台"（亦称"案例库平台"），该平台是公司结合多年的软件外包项目开发经验以及高校项目实践经验开发的集中式软件项目实践服务平台，为高校提供一体化的项目案例库管理、知识体系管理、项目实践过程管理，方便高校搭建软件工程实践中心及软件工程产学研基地，为大学生提供软件工程实践的普遍服务。

公司架构
研发一部，部门经理王文鑫，研发产品：云上学链智慧教育平台，创新性工程型人才实践能力培养解决方案
研发二部，部门经理无尾熊，研发产品：案例库平台
"""

    # 将文本保存到文件
    with open("rag_docs.txt", "w", encoding="utf-8") as f:
        f.write(text.strip())

    # 加载并分割文档
    loader = TextLoader("rag_docs.txt", encoding='utf-8')
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # 较小的块大小以提高精确度
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )

    return text_splitter.split_documents(documents)
```

在上面的代码中，保存为txt后，需要分割知识库为块，使用 RecursiveCharacterTextSplitter方法进行分割，其中chunk_size的大小是每个块文本的程度，chunk_overlap是滑块文本的长度，这个2个值需要自己工具文本内容大小进行设置。这里文本内容比较小所以设置为500和100，一般文本内容较多时设置为1000和200.最后返回分割好的文本块。分割质量直接影响后续检索效果。

这里加载的时txt类型的知识库，如果是pdf和word，csv等，langchain也提供了对于的读取文件方法。



### 4.3  向量化与存储

我们使用安装好的本地嵌入模型将文本转为向量并存储到内存中。

```python
# 初始化嵌入模型
embedding_model = OllamaEmbeddings(model='nomic-embed-text')

# 创建内存向量存储
texts = [doc.page_content for doc in documents]
text_embeddings = embedding_model.embed_documents(texts)
vector_store = InMemoryVectorStore.from_texts(
    texts=texts,
    embedding=embedding_model,
    metadatas=[{"source": "rag_docs.txt"} for _ in texts]
)

# 创建检索器
retriever = vector_store.as_retriever(search_kwargs={"k": 3})
```

最后创建检索器返回相似度最好的3个结果。

这里案例是采用比较方便的方式使用本地nomic-embed-text和向量检索器。

如果要提高嵌入模型检索效果，则需要使用评分更好的模型。

比如最新25年6月发布的 **Qwen3-Embedding** 模型，但是对本地算力有要求。



### 4.4构建检索上下文

我们使用`retriever.get_relevant_documents(query)`检索相关文档，设置search_kwargs={"k": 3}`指定返回最相关的3个文档块，格式化上下文便于大语言模型理解，其中上下文质量直接影响最终回答准确性

```python
def get_context(retriever, query: str):
    docs = retriever.get_relevant_documents(query)
    context = "## 相关文档内容:\n"
    for i, doc in enumerate(docs):
        context += f"\n### 文档片段 {i+1}:\n{doc.page_content}\n"
    return context

```

我们返回文档的引用片段，用于验证检索查询的来源，以及是否正确。



### 4.5使用大语言模型根据检索结果回答问题

```python
llm = ChatOpenAI(model="deepseek-chat",openai_api_base="https://api.deepseek.com")

# 定义提示模板
template = """
你是一个专业的AI助手，需要根据提供的上下文信息回答问题。
结合以下检索到的信息，用专业且简洁的语言回答用户问题：

{context}

---
问题：{question}
要求：
1. 回答应基于公司提供的产品、服务和架构信息
2. 如果问题涉及具体部门或产品，请详细说明
3. 如果信息不足，请说明哪些方面需要更多数据
4. 请使用中文回答
"""
prompt = ChatPromptTemplate.from_template(template)

# 构建RAG链
rag_chain = (
        {"context": lambda x: get_context(x["question"]),
         "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)


# ----------------------
# 步骤5: 查询接口
# ----------------------
def ask_question(question):
    """执行查询并返回结果"""
    # 显示检索的上下文
    print("\n" + "=" * 50)
    print("检索上下文:")
    print(get_context(question))
    print("=" * 50 + "\n")

    # 生成回答
    return rag_chain.invoke({"question": question})
```

使用lanchain调用大语言模型，设置系统提示词模板将检索结果加入提示词中，接收用户提问。

```python
if __name__ == "__main__":
    questions = [
        "学链科技的主要产品有哪些？",
        "研发一部的部门经理是谁？该部门负责哪些产品？",
        "学链科技与哪些高校有合作关系？",
        "请详细介绍云上学链智慧教育平台的功能",
        "公司获得了哪些荣誉资质？"
    ]

    for q in questions:
        print(f"\n问题: {q}")
        print(f"答案: {ask_question(q)}")
        print("-" * 80)
```

向模型提问并返回结果。



完整代码如下：

```python
import os
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.vectorstores import InMemoryVectorStore


# 加载环境变量
os.environ["OPENAI_API_KEY"] = ""
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = ""


# ----------------------
# 步骤1: 数据加载和处理
# ----------------------
def load_and_process_data():
    """加载文档并分割成块"""
    # 使用示例文本内容
    text = """
公司介绍
武汉学链科有限公司，是国家认定的高新技术企业、教育部软件工程专业大学生实习实训基地、武汉市大学生实习实训基地，入选第十四届3551光谷人才计划，提供大数据分析平台、AI实训平台、DevOps实践案例库等产品，并为政企客户提供大数据、人工智能等数字化、智能化技术创新研发服务。
学链科技创新产学合作模式，依托AI实训平台、案例库，提供数智人才实践能力培养解决方案，公司与上海交通大学、华中科技大学、武汉大学、重庆大学等三十多所"双一流"高校开展了密切合作，并获得了多项省部级教学成果，着力打造互联网+教育生态，IT人才供应链。

学链科技以社会化协作的模式，建立涵盖金融、通信、企业管理、物流、制造等多行业的企业项目案例及实践知识库，同时搭建跨区域的软件工程实践平台，实现高校人才培养体系与企业需求的无缝对接，并通过创意工厂把社会化创意、企业研发项目引入高校，帮助大学生在课程知识学习、工程实践的同时，开发适应社会需求的软件产品。
学链科技始终关注用户对于知识传播和学习的需求，不断推出基于知识搜索的各种智能教育产品，与学校、企业、培训机构共同打造垂直领域的知识库和智能平台，按照自适应教学的核心理念，实现个性化的、混合式的教育模式，并为用户提供可不断延伸的终身教育网络。
"知识凝聚价值"是公司的核心价值观。

1)云上学链智慧教育平台
公司在IT教育领域耕耘多年，专注于网络教育系列产品的研发，目前具有自主知识产权的网络教育产品"智慧教育平台"已成功应用于全国像"北京交通大学"、"武汉大学"、"郑州大学"、"东莞理工学院"等十多所知名高等院校，在网络教育平台运营与合作方面积累了丰富的经验。
云上学链智慧教育平台，提供在线课程学习、实践案例学习，以及工程实践管理、实践过程管理等功能。平台提供了一系列功能用于完成实训教学任务所需筹备、布置的工作事宜。教师可以使用资源管理功能实现教学资源的共享，在教学过程跟踪和总结方面，教师可以通过集中管理、分布式统计的功能，更好地把握每位同学的学习进度，以便及时发现问题并敦促学生跟进。

2)创新性工程型人才实践能力培养解决方案
学链科技是创新性工程型人才培养解决方案服务商，经过多年的时间与沉淀，打造了内容详尽的实践项目案例库和层次化工程实践体系，与高校课程体系无缝衔接，紧扣教学计划，帮助高校改进时间和教学环节，沉淀教改成果，提升人才培养质量。通过完整、全面的实践案例和学习资源，让老师轻松成为项目经理，掌控项目实践，开展混合式教学。学生通过工程实践训练，较大地提高工程意识、实践能力、创新能力。

3)案例库平台
我们为案例实践打造了"DevOps工程实践案例库平台"（亦称"案例库平台"），该平台是公司结合多年的软件外包项目开发经验以及高校项目实践经验开发的集中式软件项目实践服务平台，为高校提供一体化的项目案例库管理、知识体系管理、项目实践过程管理，方便高校搭建软件工程实践中心及软件工程产学研基地，为大学生提供软件工程实践的普遍服务。

公司架构
研发一部，部门经理王文鑫，研发产品：云上学链智慧教育平台，创新性工程型人才实践能力培养解决方案
研发二部，部门经理无尾熊，研发产品：案例库平台
"""

    # 将文本保存到文件
    with open("rag_docs.txt", "w", encoding="utf-8") as f:
        f.write(text.strip())

    # 加载并分割文档
    loader = TextLoader("rag_docs.txt", encoding='utf-8')
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # 较小的块大小以提高精确度
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )

    return text_splitter.split_documents(documents)


# 加载并处理文档
documents = load_and_process_data()

# ----------------------
# 步骤2: 创建嵌入模型和向量存储
# ----------------------
# 初始化嵌入模型
embedding_model = OllamaEmbeddings(model='nomic-embed-text')

# 创建内存向量存储
texts = [doc.page_content for doc in documents]
text_embeddings = embedding_model.embed_documents(texts)
vector_store = InMemoryVectorStore.from_texts(
    texts=texts,
    embedding=embedding_model,
    metadatas=[{"source": "rag_docs.txt"} for _ in texts]
)

# 创建检索器
retriever = vector_store.as_retriever(search_kwargs={"k": 3})


# ----------------------
# 步骤3: 构建检索上下文
# ----------------------
def get_context(query: str):
    """获取检索到的上下文"""
    # 使用检索器获取相关文档
    results = retriever.get_relevant_documents(query)

    # 构建上下文字符串
    context = "## 相关文档内容:\n"
    for i, doc in enumerate(results):
        context += f"\n### 文档片段 {i + 1}:\n{doc.page_content}\n"
    return context


# ----------------------
# 步骤4: 构建RAG管道
# ----------------------
# 初始化大语言模型
llm = ChatOpenAI(model="deepseek-chat",openai_api_base="https://api.deepseek.com")

# 定义提示模板
template = """
你是一个专业的AI助手，需要根据提供的上下文信息回答问题。
结合以下检索到的信息，用专业且简洁的语言回答用户问题：

{context}

---
问题：{question}
要求：
1. 回答应基于公司提供的产品、服务和架构信息
2. 如果问题涉及具体部门或产品，请详细说明
3. 如果信息不足，请说明哪些方面需要更多数据
4. 请使用中文回答
"""
prompt = ChatPromptTemplate.from_template(template)

# 构建RAG链
rag_chain = (
        {"context": lambda x: get_context(x["question"]),
         "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)


# ----------------------
# 步骤5: 查询接口
# ----------------------
def ask_question(question):
    """执行查询并返回结果"""
    # 显示检索的上下文
    print("\n" + "=" * 50)
    print("检索上下文:")
    print(get_context(question))
    print("=" * 50 + "\n")

    # 生成回答
    return rag_chain.invoke({"question": question})


# ----------------------
# 步骤6: 示例查询
# ----------------------
if __name__ == "__main__":
    questions = [
        "学链科技的主要产品有哪些？",
        "研发一部的部门经理是谁？该部门负责哪些产品？",
        "学链科技与哪些高校有合作关系？",
        "请详细介绍云上学链智慧教育平台的功能",
        "公司获得了哪些荣誉资质？"
    ]

    for q in questions:
        print(f"\n问题: {q}")
        print(f"答案: {ask_question(q)}")
        print("-" * 80)

```



## 5.基于知识图谱的RAG

### 5.1 安装图数据库

下载安装neo4j的数据库，解压到本地文件夹，并配置环境变量。

下载地址：https://neo4j.com/deployment-center/

配置环境变量：新增 变量名NEO4J_HOME  值：C:\Environment\neo4j-community-5.26.0\bin

修改path变量，添加%NEO4J_HOME%\bin;

启动图数据库，在cmd里输入 neo4j console ，输入cmd里的路径http://localhost:7474/

运行neo4j的web管理页面查看是否成功运行。账户密码：neo4j/neo4j

![1750035638894](C:\Users\wwx_i\AppData\Roaming\Typora\typora-user-images\1750035638894.png)

现在是还没有数据的，代码里会初始化知识图谱。

### 5.2设置相关配置

我们需要配置图数据库连接字符串，大模型key，初始neo4j数据库对象

```python
import os
import re
from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

# 加载环境变量
os.environ["OPENAI_API_KEY"] = ""
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "neo4j"
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# 初始化Neo4j图数据库连接
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)
```

其中OPENAI_API_KEY可以说各个平台的大模型key，这里使用的是deepseek的key

LANGCHAIN_API_KEY设置的是langsmith的key，用于监控和调试大模型的调用过程。

NEO4J_USERNAME和NEO4J_PASSWORD，默认是neo4j/neo4j

运行代码，无报错则，数据库连接成功。



### 5.3 初始知识图谱数据。

这里还是使用学链公司的公司介绍，并且抽取出公司、部门，公司业务，公司产品、人员、岗位信息的实体和关系创建知识图谱数据库。代码里会清空现有数据，如果图数据库有数据则注释清空代码。

```python
def load_and_process_data():
    """加载文档并分割成块"""
    # 使用示例文本内容
    text = """
公司介绍
武汉学链科有限公司，是国家认定的高新技术企业、教育部软件工程专业大学生实习实训基地、武汉市大学生实习实训基地，入选第十四届3551光谷人才计划，提供大数据分析平台、AI实训平台、DevOps实践案例库等产品，并为政企客户提供大数据、人工智能等数字化、智能化技术创新研发服务。
学链科技创新产学合作模式，依托AI实训平台、案例库，提供数智人才实践能力培养解决方案，公司与上海交通大学、华中科技大学、武汉大学、重庆大学等三十多所“双一流”高校开展了密切合作，并获得了多项省部级教学成果，着力打造互联网+教育生态，IT人才供应链。

学链科技以社会化协作的模式，建立涵盖金融、通信、企业管理、物流、制造等多行业的企业项目案例及实践知识库，同时搭建跨区域的软件工程实践平台，实现高校人才培养体系与企业需求的无缝对接，并通过创意工厂把社会化创意、企业研发项目引入高校，帮助大学生在课程知识学习、工程实践的同时，开发适应社会需求的软件产品。
学链科技始终关注用户对于知识传播和学习的需求，不断推出基于知识搜索的各种智能教育产品，与学校、企业、培训机构共同打造垂直领域的知识库和智能平台，按照自适应教学的核心理念，实现个性化的、混合式的教育模式，并为用户提供可不断延伸的终身教育网络。
“知识凝聚价值”是公司的核心价值观。

1)云上学链智慧教育平台
公司在IT教育领域耕耘多年，专注于网络教育系列产品的研发，目前具有自主知识产权的网络教育产品“智慧教育平台”已成功应用于全国像“北京交通大学”、“武汉大学”、“郑州大学”、“东莞理工学院”等十多所知名高等院校，在网络教育平台运营与合作方面积累了丰富的经验。
云上学链智慧教育平台，提供在线课程学习、实践案例学习，以及工程实践管理、实践过程管理等功能。平台提供了一系列功能用于完成实训教学任务所需筹备、布置的工作事宜。教师可以使用资源管理功能实现教学资源的共享，在教学过程跟踪和总结方面，教师可以通过集中管理、分布式统计的功能，更好地把握每位同学的学习进度，以便及时发现问题并敦促学生跟进。

2)创新性工程型人才实践能力培养解决方案
学链科技是创新性工程型人才培养解决方案服务商，经过多年的时间与沉淀，打造了内容详尽的实践项目案例库和层次化工程实践体系，与高校课程体系无缝衔接，紧扣教学计划，帮助高校改进时间和教学环节，沉淀教改成果，提升人才培养质量。通过完整、全面的实践案例和学习资源，让老师轻松成为项目经理，掌控项目实践，开展混合式教学。学生通过工程实践训练，较大地提高工程意识、实践能力、创新能力。

3)案例库平台
我们为案例实践打造了“DevOps工程实践案例库平台”（亦称“案例库平台”），该平台是公司结合多年的软件外包项目开发经验以及高校项目实践经验开发的集中式软件项目实践服务平台，为高校提供一体化的项目案例库管理、知识体系管理、项目实践过程管理，方便高校搭建软件工程实践中心及软件工程产学研基地，为大学生提供软件工程实践的普遍服务。

公司架构
研发一部，部门经理王文鑫，研发产品：云上学链智慧教育平台，创新性工程型人才实践能力培养解决方案
研发二部，部门经理无尾熊，研发产品：案例库平台
"""

    # 将文本保存到临时文件
    with open("rag_docs.txt", "w", encoding="utf-8") as f:
        f.write(text.strip())

    # 加载并分割文档
    loader = TextLoader("rag_docs.txt", encoding='utf-8')
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    return text_splitter.split_documents(documents)


# 加载并处理文档
documents = load_and_process_data()


# ----------------------
# 步骤2: 构建知识图谱
# ----------------------
def extract_structured_data(text):
    """从文本中提取结构化数据"""
    # 提取公司基本信息
    company_match = re.search(r'武汉学链科有限公司[^。]+', text)
    company_intro = company_match.group(0) if company_match else ""

    # 提取荣誉
    honors = re.findall(
        r'国家认定的高新技术企业|教育部软件工程专业大学生实习实训基地|武汉市大学生实习实训基地|第十四届3551光谷人才计划',
        text)

    # 提取产品信息 - 修复正则表达式问题
    products = []
    # 使用更简单的正则表达式匹配产品部分
    product_sections = re.findall(r'\d+\)[^\n]+\n.+?(?=\n\d+\)|\n公司架构|\Z)', text, re.DOTALL)

    for section in product_sections:
        # 提取产品名称
        name_match = re.search(r'\d+\)(.+)', section)
        if name_match:
            product_name = name_match.group(1).strip()

            # 提取产品描述
            description_match = re.search(r'\n(.+)', section, re.DOTALL)
            if description_match:
                description = description_match.group(1).strip()
                products.append({
                    "name": product_name,
                    "description": description
                })

    # 提取部门信息 - 简化正则表达式
    departments = []
    dept_pattern = r'([^，]+)，部门经理([^，]+)，研发产品：([^\n]+)'
    dept_matches = re.findall(dept_pattern, text)

    for dept in dept_matches:
        departments.append({
            "name": dept[0].strip(),
            "manager": dept[1].strip(),
            "products": [p.strip() for p in dept[2].split("，")]
        })

    # 提取合作高校
    universities = re.findall(r'上海交通大学|华中科技大学|武汉大学|重庆大学|北京交通大学|郑州大学|东莞理工学院', text)

    return {
        "company_intro": company_intro,
        "honors": list(set(honors)),
        "products": products,
        "departments": departments,
        "universities": list(set(universities))
    }


def create_knowledge_graph():
    """构建知识图谱"""
    # 加载文档内容
    with open("rag_docs.txt", "r", encoding="utf-8") as f:
        text = f.read()

    # 提取结构化数据
    data = extract_structured_data(text)

    # 创建公司节点
    company_query = """
    MERGE (c:Company {name: "武汉学链科有限公司"})
    SET c.introduction = $intro,
        c.alias = "学链科技",
        c.core_value = "知识凝聚价值"
    RETURN id(c) AS companyId
    """
    company_id = graph.query(company_query, params={"intro": data["company_intro"]})[0]["companyId"]

    # 创建荣誉节点并建立关系
    for honor in data["honors"]:
        honor_query = """
        MERGE (h:Honor {name: $name})
        WITH h
        MATCH (c:Company) WHERE id(c) = $companyId
        MERGE (c)-[:HAS_HONOR]->(h)
        """
        graph.query(honor_query, params={"name": honor, "companyId": company_id})

    # 创建产品节点并建立关系
    for product in data["products"]:
        product_query = """
        MERGE (p:Product {name: $name})
        SET p.description = $description
        WITH p
        MATCH (c:Company) WHERE id(c) = $companyId
        MERGE (c)-[:HAS_PRODUCT]->(p)
        """
        graph.query(product_query, params={
            "name": product["name"],
            "description": product["description"],
            "companyId": company_id
        })

    # 创建部门节点并建立关系
    for dept in data["departments"]:
        # 创建部门节点
        dept_query = """
        MERGE (d:Department {name: $name})
        WITH d
        MATCH (c:Company) WHERE id(c) = $companyId
        MERGE (c)-[:HAS_DEPARTMENT]->(d)
        RETURN id(d) AS deptId
        """
        dept_id = graph.query(dept_query, params={
            "name": dept["name"],
            "companyId": company_id
        })[0]["deptId"]

        # 创建经理节点并建立关系
        manager_query = """
        MERGE (p:Person {name: $name})
        SET p.position = "部门经理"
        WITH p
        MATCH (d:Department) WHERE id(d) = $deptId
        MERGE (d)-[:HAS_MANAGER]->(p)
        """
        graph.query(manager_query, params={
            "name": dept["manager"],
            "deptId": dept_id
        })

        # 建立部门与产品的关系
        for product_name in dept["products"]:
            product_rel_query = """
            MATCH (d:Department) WHERE id(d) = $deptId
            MATCH (p:Product {name: $name})
            MERGE (d)-[:DEVELOPS]->(p)
            """
            graph.query(product_rel_query, params={
                "deptId": dept_id,
                "name": product_name
            })

    # 创建高校节点并建立合作关系
    for university in data["universities"]:
        university_query = """
        MERGE (u:University {name: $name})
        WITH u
        MATCH (c:Company) WHERE id(c) = $companyId
        MERGE (c)-[:COOPERATES_WITH]->(u)
        """
        graph.query(university_query, params={
            "name": university,
            "companyId": company_id
        })

    # 将文档分块存储为向量
    Neo4jVector.from_documents(
        documents=documents,
        embedding=OllamaEmbeddings(model='nomic-embed-text'),
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        index_name="rag_docs",
        node_label="Chunk",
        text_node_property="text",
        embedding_node_property="embedding"
    )

    # 将概念链接到文档块
    concepts = [
                   "武汉学链科有限公司", "学链科技",
                   "云上学链智慧教育平台", "创新性工程型人才实践能力培养解决方案", "案例库平台",
                   "研发一部", "研发二部", "王文鑫", "无尾熊"
               ] + data["honors"] + data["universities"]

    for concept in concepts:
        graph.query("""
        MATCH (c:Chunk), (con)
        WHERE con.name = $concept AND c.text CONTAINS $concept
        MERGE (c)-[:MENTIONS]->(con)
        """, params={"concept": concept})


# 构建知识图谱
create_knowledge_graph()
```

如果是自己的知识库文档，需要根据文档中内容，分析出实体和关系，创建图数据库实体和关系。



### 5.4 构建混合检索器

这里为了提高搜索结果的准确度，使用混合检索器，其中包含基础的纯向量相似度检索和基于知识图谱的检索。

嵌入式模型使用的本地部署的OllamaEmbeddings-nomic-embed-text，如果要提高检索速度和精度，则需要更好的嵌入式模型。

```python
class HybridRetriever:
    def __init__(self):
        # 向量检索器
        self.vector_store = Neo4jVector(
            embedding=OllamaEmbeddings(model='nomic-embed-text'),
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            index_name="rag_docs",
            node_label="Chunk",
            text_node_property="text",
            embedding_node_property="embedding"
        )

        # 图数据库连接
        self.graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD
        )

    def vector_retrieval(self, query: str, k: int = 3):
        """纯向量相似度检索"""
        return self.vector_store.similarity_search(query, k=k)

    def graph_retrieval(self, query: str):
        """图关系检索扩展上下文"""
        # 查找相关概念
        concept_query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) CONTAINS toLower($query)
        RETURN c.name AS concept
        LIMIT 5
        """
        concepts = [record['concept'] for record in self.graph.query(concept_query, params={"query": query})]

        if not concepts:
            return []

        # 查找相关文档块
        doc_query = """
        UNWIND $concepts AS concept
        MATCH (con:Concept {name: concept})-[:MENTIONS]-(chunk:Chunk)
        RETURN DISTINCT chunk.text AS text, chunk.embedding AS embedding
        LIMIT 10
        """
        return self.graph.query(doc_query, params={'concepts': concepts})

    def hybrid_search(self, query: str):
        """混合检索策略"""
        # 获取向量检索结果
        vector_results = self.vector_retrieval(query)

        # 获取图检索结果
        graph_results = self.graph_retrieval(query)

        # 合并结果
        context = ""

        # 添加向量结果
        context += "## 相关文档内容:\n"
        for i, doc in enumerate(vector_results):
            context += f"\n### 文档片段 {i + 1}:\n{doc.page_content}\n"

        # 添加图结果
        if graph_results:
            context += "\n## 相关实体信息:\n"
            for i, record in enumerate(graph_results):
                context += f"\n### 实体关联内容 {i + 1}:\n{record['text']}\n"

        return context

```

其中在“graph_retrieval”中使用了cypher查询语法，这个是图数据库的查询语法，类似sql语法，可以直接使用ai生成cypher语句。



### 5.5构建RAG管道

RGA管道是将检索器查询的结果提供给LLM的系统提示词里作为用户提示词的上下文。方便大模型直接根据知识库查询到的相关内容回答问题。

```python
retriever = HybridRetriever()
llm = ChatOpenAI(model="deepseek-chat",openai_api_base="https://api.deepseek.com")


# 定义提示模板
template = """
你是一个专业的AI助手，需要根据提供的上下文信息回答问题。
结合以下检索到的信息，用专业且简洁的语言回答用户问题：

{context}

---
问题：{question}
要求：
1. 回答应基于公司提供的产品、服务和架构信息
2. 如果问题涉及具体部门或产品，请详细说明
3. 如果信息不足，请说明哪些方面需要更多数据
"""
prompt = ChatPromptTemplate.from_template(template)

# 构建RAG链
rag_chain = (
        {"context": lambda x: retriever.hybrid_search(x["question"]),
         "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)


# ----------------------
# 步骤5: 查询接口
# ----------------------
def ask_question(question):
    """执行查询并返回结果"""
    response = rag_chain.invoke({"question": question})

    # 显示检索的上下文（调试用）
    print("\n" + "=" * 50)
    print("检索上下文:")
    print(retriever.hybrid_search(question))
    print("=" * 50 + "\n")

    return response

```

影响大模型根据知识库回复正确率的要素是，检索器查询返回的结果，系统提示词工程设置，大模型基座能力。

最后运行查询方法，进行提问。

```python
if __name__ == "__main__":
    questions = [
        "学链科技的主要产品有哪些？",
        "研发一部的部门经理是谁？该部门负责哪些产品？",
        "学链科技与哪些高校有合作关系？",
        "请详细介绍云上学链智慧教育平台的功能",
        "公司获得了哪些荣誉资质？"
    ]

    for q in questions:
        print(f"\n问题: {q}")
        print(f"答案: {ask_question(q)}")
        print("-" * 80)

```



## 6.RAG结果对比

| RAG类型 | 问题                                         | 回复                                                         |
| ------- | -------------------------------------------- | ------------------------------------------------------------ |
| 基础RAG | 学链科技的主要产品有哪些？                   | 学链科技的主要产品和服务包括以下三类核心解决方案：<br/><br/>1. **教育技术平台**  <br/>   - **云上学链智慧教育平台**：提供在线课程学习、实践案例库、工程实践管理及教学过程跟踪功能，支持高校实训教学全流程（如资源管理、学习进度统计），已应用于北京交通大学、武汉大学等十多所高校。  <br/>   - **AI实训平台**：聚焦人工智能领域实践能力培养，与高校合作开发适配产业需求的实训内容。<br/><br/>2. **行业案例库与工具**  <br/>   - **DevOps实践案例库**：涵盖企业级软件开发运维实践。  <br/>   - **大数据分析平台**：服务于政企客户的数字化研发需求，同时用于教学场景。<br/><br/>3. **产学合作服务**  <br/>   - 提供"数智人才实践能力培养"整体解决方案，通过跨区域软件工程实践平台、创意工厂等，对接高校课程与企业项目需求（如金融、物流等行业案例）。  <br/>   - 联合高校开发垂直领域知识库，支持个性化混合教育模式。 |
| 高级RAG | 学链科技的主要产品有哪些？                   | 学链科技的主要产品包括以下两类核心解决方案及配套平台，分别由不同研发部门负责：  <br/><br/>1. **创新性工程型人才实践能力培养解决方案**  <br/>   - **研发部门**：研发一部（经理：王文鑫）  <br/>   - **核心功能**：  <br/>     - 提供层次化工程实践体系，与高校课程无缝衔接，提升学生工程意识、实践及创新能力。  <br/>     - 包含详尽的实践项目案例库，支持混合式教学，帮助教师转型为“项目经理”。  <br/><br/>2. **案例库平台（DevOps工程实践案例库平台）**  <br/>   - **研发部门**：研发二部（经理：无尾熊）  <br/>   - **核心功能**：  <br/>     - 集中管理软件项目案例、知识体系及实践过程，支持高校搭建软件工程实践中心或产学研基地。  <br/>     - 基于企业级项目经验开发，提供多行业（金融、通信、物流等）真实案例资源。  <br/><br/>**其他关联产品与服务**（补充信息）：  <br/>- **云上学链智慧教育平台**：  <br/>  - 提供在线课程学习、工程实践管理及教学跟踪功能，已应用于多所高校（如武汉大学、北京交通大学）。  <br/>- **AI实训平台**与**大数据分析平台**：  <br/>  - 用于数智人才培养，支持人工智能、大数据等领域的实践教学。 |
| 基础RAG | 研发一部的部门经理是谁？该部门负责哪些产品？ | 根据提供的文档内容，目前无法直接回答"研发一部的部门经理是谁"这一问题，原因如下：<br/><br/>1. 信息不足：<br/>- 现有文档未提及公司内部组织架构<br/>- 未披露具体部门设置及管理人员信息<br/><br/>关于部门负责产品的推测（基于公司整体业务）：<br/>若"研发一部"属于核心研发部门，可能负责以下产品线（需进一步确认）：<br/>1. 大数据分析平台<br/>2. AI实训平台<br/>3. DevOps实践案例库<br/>4. 云上学链智慧教育平台（含在线课程系统、工程实践管理系统等）<br/><br/>建议补充以下信息：<br/>- 公司组织架构图<br/>- 部门分工说明<br/>- 管理人员名录 |
| 高级RAG | 研发一部的部门经理是谁？该部门负责哪些产品？ | 研发一部的部门经理是王文鑫。该部门负责以下产品：  <br/>1. **云上学链智慧教育平台**：提供在线课程学习、实践案例学习及工程实践管理等功能，支持高校实训教学任务的全流程管理（如资源管理、学习进度跟踪等）。  <br/>2. **创新性工程型人才实践能力培养解决方案**：包括层次化工程实践体系、与高校课程衔接的实践项目案例库，旨在提升学生工程意识和创新能力。 |

提供对比可以看到，

问题一：学链科技的主要产品有哪些？ 普通rag可以列出产品相关的信息，但是额外的产品信息无法自动列出。对于问题的扩展和补充不足。



问题二：研发一部的部门经理是谁？ 普通rag无法找到部门负责人，并且出现大模型幻觉，将所有的产品都添加到回答中。

而基于知识图谱的高级rag回复的准确率更高。

在智能体开发过程中，根据知识库的结构和用于来选择是否搭建知识图谱提供大模型支持。

