"""
基于FastAPI和LlamaIndex的RAG服务
实现功能：文档加载、索引构建、自然语言问答
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware  # CORS

# 加载环境变量（如需使用OpenAI等云服务）
load_dotenv()
# ----------------------------
# 配置参数（按需修改）
# ----------------------------
DOC_DIR = "./sample_docs"  # 文档存储目录
EMBED_MODEL = r"/mnt/workspace/llm/BAAI/bge-small-zh-v1.5"  # 本地嵌入模型
LLM_MODEL =  r"/mnt/workspace/llm/Qwen/Qwen1___5-1___8B-Chat"  # 本地LLM模型

# ----------------------------
# FastAPI应用初始化
# ----------------------------
app = FastAPI(
    title="RAG API Service",
    description="基于本地模型的检索增强生成系统",
    version="1.0"
)
# 添加 CORS 配置 👇

# ----------------------------
# LlamaIndex组件初始化
# ----------------------------
class RAGSystem:
    def __init__(self):
        self.index = None
        self.query_engine = None
        self._init_models()
        self._load_data()
    
    def _init_models(self):
        """初始化嵌入模型和LLM"""
        # 使用本地嵌入模型
        self.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)
        
        # 配置本地LLM
        self.llm = HuggingFaceLLM(
            model_name=LLM_MODEL,
            tokenizer_name=LLM_MODEL,
            device_map="auto",  # 自动选择GPU/CPU
            generate_kwargs={"temperature": 0.1, "max_length": 500}#此处统计配置生成长度
          
        )
        
        # 全局设置
        Settings.embed_model = self.embed_model
        Settings.llm = self.llm
    def _load_data(self):
        """加载文档并构建索引"""
        try:
            if not os.path.exists(DOC_DIR):
                os.makedirs(DOC_DIR)
                raise FileNotFoundError(f"请将文档放入{DOC_DIR}目录")
            
            # 读取文档（支持pdf、txt、md等格式）
            documents = SimpleDirectoryReader(DOC_DIR).load_data()
            
            # 构建向量索引
            self.index = VectorStoreIndex.from_documents(documents)
            
            # 创建查询引擎
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=3,  # 检索前3个相关段落
                response_mode="compact"  # 生成紧凑回答
            )
        except Exception as e:
            raise RuntimeError(f"索引初始化失败: {str(e)}")

# 初始化RAG系统
rag_system = RAGSystem()

# ----------------------------
# API数据模型
# ----------------------------
class QueryRequest(BaseModel):
    question: str
    # max_length: Optional[int] = 500#删除，在LLM中统一配置

class QueryResponse(BaseModel):
    question: str
    answer: str
    source_docs: list[str]

# ----------------------------
# API端点
# ----------------------------
# 处理自然语言查询
@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    处理自然语言问答
    参数：
    - question: 用户问题
    - max_length: 生成文本的最大长度
    """
    try:
        if not rag_system.query_engine:
            raise HTTPException(status_code=503, detail="系统未就绪")
        
        # 执行查询
        response = rag_system.query_engine.query(
            request.question,
        )
        
        # 提取来源文档
        source_nodes = response.source_nodes or []
        sources = [node.text[:200]+"..." for node in source_nodes]  # 截取部分内容
        
        return QueryResponse(
            question=request.question,
            answer=response.response,
            source_docs=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 提供健康检查
@app.get("/health")
def check_health():
    """服务健康检查"""
    return {"status": "ready" if rag_system.query_engine else "initializing"}

# ----------------------------
# 启动服务
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)