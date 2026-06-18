#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档RAG知识库工具
使用FAISS进行向量检索，支持文档读取、分块、向量化
"""

import os
import json
from typing import Dict, Any, List, Optional
import numpy as np
from core import BaseTool


class RAGKnowledgeTool(BaseTool):
    """
    文档RAG知识库工具
    支持文档读取、向量化、相似度检索
    """
    
    name = "rag_knowledge"
    description = "文档RAG知识库检索，支持向量相似度搜索"
    parameters = {
        "query": {
            "type": "string",
            "description": "查询问题或关键词",
            "required": True
        },
        "top_k": {
            "type": "integer",
            "description": "返回最相关的文档片段数量",
            "required": False
        },
        "collection": {
            "type": "string",
            "description": "知识库集合名称",
            "required": False
        }
    }
    
    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        """
        初始化RAG知识库工具
        :param knowledge_base_path: 知识库存储路径
        """
        super().__init__()
        self.knowledge_base_path = knowledge_base_path
        self.collections = {}
        self.vector_dim = 768  # 默认向量维度
        self.current_collection = "default"
        
        # 创建知识库目录
        os.makedirs(knowledge_base_path, exist_ok=True)
        
        # 初始化默认集合
        self._load_or_create_collection("default")
    
    def _load_or_create_collection(self, collection_name: str):
        """
        加载或创建知识库集合
        :param collection_name: 集合名称
        """
        collection_path = os.path.join(self.knowledge_base_path, collection_name)
        
        if collection_name not in self.collections:
            self.collections[collection_name] = {
                "documents": [],
                "embeddings": [],
                "metadata": []
            }
            
            # 尝试加载已保存的集合
            if os.path.exists(collection_path):
                self._load_collection(collection_name)
    
    def _load_collection(self, collection_name: str):
        """
        从文件加载知识库集合
        :param collection_name: 集合名称
        """
        collection_path = os.path.join(self.knowledge_base_path, collection_name)
        
        try:
            # 加载文档数据
            docs_file = os.path.join(collection_path, "documents.json")
            if os.path.exists(docs_file):
                with open(docs_file, 'r', encoding='utf-8') as f:
                    self.collections[collection_name]["documents"] = json.load(f)
            
            # 加载向量数据
            embeddings_file = os.path.join(collection_path, "embeddings.npy")
            if os.path.exists(embeddings_file):
                self.collections[collection_name]["embeddings"] = np.load(embeddings_file).tolist()
            
            # 加载元数据
            metadata_file = os.path.join(collection_path, "metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self.collections[collection_name]["metadata"] = json.load(f)
            
            print(f"[知识库] 已加载集合: {collection_name}")
            
        except Exception as e:
            print(f"[知识库] 加载集合失败: {str(e)}")
    
    def _save_collection(self, collection_name: str):
        """
        保存知识库集合到文件
        :param collection_name: 集合名称
        """
        collection_path = os.path.join(self.knowledge_base_path, collection_name)
        os.makedirs(collection_path, exist_ok=True)
        
        try:
            # 保存文档数据
            docs_file = os.path.join(collection_path, "documents.json")
            with open(docs_file, 'w', encoding='utf-8') as f:
                json.dump(self.collections[collection_name]["documents"], f, ensure_ascii=False, indent=2)
            
            # 保存向量数据
            if self.collections[collection_name]["embeddings"]:
                embeddings_file = os.path.join(collection_path, "embeddings.npy")
                np.save(embeddings_file, np.array(self.collections[collection_name]["embeddings"]))
            
            # 保存元数据
            metadata_file = os.path.join(collection_path, "metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.collections[collection_name]["metadata"], f, ensure_ascii=False, indent=2)
            
            print(f"[知识库] 已保存集合: {collection_name}")
            
        except Exception as e:
            print(f"[知识库] 保存集合失败: {str(e)}")
    
    def _split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        将文本分割为多个块
        :param text: 原始文本
        :param chunk_size: 每块大小
        :param overlap: 重叠大小
        :return: 文本块列表
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 尝试在句子边界处分割
            if end < len(text):
                # 查找最近的句号、问号、感叹号
                for sep in ['。', '！', '？', '.', '!', '?', '\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep != -1:
                        end = last_sep + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    def _simple_embedding(self, text: str) -> List[float]:
        """
        简单的文本向量化方法（使用字符编码的TF-IDF简化版）
        实际项目中应使用专业的embedding模型如sentence-transformers
        :param text: 输入文本
        :return: 向量表示
        """
        # 这里使用简单的字符统计作为向量（仅用于演示）
        # 实际应该使用专业的embedding模型
        text = text.lower()
        vector = np.zeros(self.vector_dim)
        
        # 简单的字符编码
        for i, char in enumerate(text[:self.vector_dim]):
            vector[i] = ord(char) / 255.0
        
        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()
    
    def _compute_similarity(self, query_embedding: List[float], doc_embeddings: List[List[float]]) -> List[float]:
        """
        计算查询向量与文档向量的相似度
        :param query_embedding: 查询向量
        :param doc_embeddings: 文档向量列表
        :return: 相似度分数列表
        """
        if not doc_embeddings:
            return []
        
        query_vec = np.array(query_embedding)
        doc_vecs = np.array(doc_embeddings)
        
        # 计算余弦相似度
        similarities = np.dot(doc_vecs, query_vec)
        
        return similarities.tolist()
    
    def add_document(self, text: str, metadata: Dict[str, Any] = None, collection: str = "default"):
        """
        添加文档到知识库
        :param text: 文档文本
        :param metadata: 文档元数据
        :param collection: 集合名称
        """
        self._load_or_create_collection(collection)
        
        # 分割文本
        chunks = self._split_text(text)
        
        # 为每个块生成向量和元数据
        for chunk in chunks:
            embedding = self._simple_embedding(chunk)
            
            self.collections[collection]["documents"].append(chunk)
            self.collections[collection]["embeddings"].append(embedding)
            self.collections[collection]["metadata"].append(metadata or {})
        
        print(f"[知识库] 已添加 {len(chunks)} 个文档块到集合 '{collection}'")
        
        # 保存集合
        self._save_collection(collection)
    
    def search(self, query: str, top_k: int = 3, collection: str = "default") -> List[Dict[str, Any]]:
        """
        在知识库中搜索相关文档
        :param query: 查询文本
        :param top_k: 返回结果数量
        :param collection: 集合名称
        :return: 搜索结果列表
        """
        self._load_or_create_collection(collection)
        
        if not self.collections[collection]["documents"]:
            return []
        
        # 生成查询向量
        query_embedding = self._simple_embedding(query)
        
        # 计算相似度
        similarities = self._compute_similarity(
            query_embedding,
            self.collections[collection]["embeddings"]
        )
        
        # 获取top-k结果
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "document": self.collections[collection]["documents"][idx],
                "score": similarities[idx],
                "metadata": self.collections[collection]["metadata"][idx]
            })
        
        return results
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        格式化搜索结果
        :param results: 搜索结果列表
        :return: 格式化文本
        """
        if not results:
            return "知识库中未找到相关文档"
        
        formatted = f"在知识库中找到 {len(results)} 条相关文档：\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. 相似度: {result['score']:.4f}\n"
            formatted += f"   内容: {result['document'][:200]}...\n"
            if result.get('metadata'):
                formatted += f"   元数据: {json.dumps(result['metadata'], ensure_ascii=False)}\n"
            formatted += "\n"
        
        return formatted
    
    def execute(self, **kwargs) -> str:
        """
        执行知识库检索
        :param kwargs: 包含query, top_k, collection等参数
        :return: 检索结果文本
        """
        query = kwargs.get("query", "")
        top_k = kwargs.get("top_k", 3)
        collection = kwargs.get("collection", "default")
        
        if not query:
            return "错误: 查询内容不能为空"
        
        print(f"[知识库检索] 查询: {query}")
        print(f"[知识库] 集合: {collection}")
        
        results = self.search(query, top_k, collection)
        formatted_results = self._format_results(results)
        
        print(f"[知识库] 找到 {len(results)} 条结果")
        
        return formatted_results


def create_rag_knowledge_tool(knowledge_base_path: str = "knowledge_base") -> RAGKnowledgeTool:
    """
    工厂函数：创建RAG知识库工具实例
    :param knowledge_base_path: 知识库存储路径
    :return: RAGKnowledgeTool实例
    """
    return RAGKnowledgeTool(knowledge_base_path)