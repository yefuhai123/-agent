#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长期记忆模块 - FAISS向量记忆存储
使用FAISS进行向量检索，支持长期知识的存储和检索
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np


class MemoryEntry:
    """
    记忆条目
    封装一条长期记忆，包含内容、向量和元数据
    """
    
    def __init__(
        self,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        初始化记忆条目
        :param content: 记忆内容
        :param embedding: 向量表示
        :param metadata: 元数据
        :param timestamp: 时间戳
        """
        self.content = content
        self.embedding = embedding or []
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now()
        self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"mem_{int(self.timestamp.timestamp())}_{hash(self.content) % 10000}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """从字典创建记忆条目"""
        timestamp = datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now()
        return cls(
            content=data["content"],
            embedding=data.get("embedding", []),
            metadata=data.get("metadata", {}),
            timestamp=timestamp
        )


class LongTermMemory:
    """
    长期记忆 - FAISS向量存储
    使用FAISS进行向量检索，支持长期知识的存储和检索
    """
    
    def __init__(
        self,
        storage_path: str = "memory_store",
        vector_dim: int = 768,
        index_type: str = "flat"
    ):
        """
        初始化长期记忆
        :param storage_path: 存储路径
        :param vector_dim: 向量维度
        :param index_type: 索引类型 (flat/ivf)
        """
        self.storage_path = storage_path
        self.vector_dim = vector_dim
        self.index_type = index_type
        
        os.makedirs(storage_path, exist_ok=True)
        
        self.memory_entries: List[MemoryEntry] = []
        self.embeddings: np.ndarray = np.empty((0, vector_dim))
        self.index = None
        
        self._init_faiss()
    
    def _init_faiss(self):
        """初始化FAISS索引"""
        try:
            import faiss
            
            if self.index_type == "ivf":
                nlist = 100
                quantizer = faiss.IndexFlatL2(self.vector_dim)
                self.index = faiss.IndexIVFFlat(quantizer, self.vector_dim, nlist, faiss.METRIC_L2)
            else:
                self.index = faiss.IndexFlatL2(self.vector_dim)
            
            print(f"[长期记忆] FAISS索引初始化成功: {self.index_type}")
            
        except ImportError:
            print("[长期记忆] FAISS未安装，使用简单余弦相似度")
            self.index = None
    
    def _simple_embedding(self, text: str) -> List[float]:
        """
        简单的文本向量化方法
        :param text: 输入文本
        :return: 向量表示
        """
        text = text.lower()
        vector = np.zeros(self.vector_dim)
        
        for i, char in enumerate(text[:self.vector_dim]):
            vector[i] = ord(char) / 255.0
        
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()
    
    def _compute_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        :param vec1: 向量1
        :param vec2: 向量2
        :return: 相似度分数
        """
        a = np.array(vec1)
        b = np.array(vec2)
        
        if len(a) == 0 or len(b) == 0:
            return 0.0
        
        if len(a) != len(b):
            min_len = min(len(a), len(b))
            a = a[:min_len]
            b = b[:min_len]
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> MemoryEntry:
        """
        添加记忆条目
        :param content: 记忆内容
        :param metadata: 元数据
        :param embedding: 向量表示（可选）
        :return: 添加的记忆条目
        """
        # 生成向量（如果未提供）
        if embedding is None:
            embedding = self._simple_embedding(content)
        
        # 创建记忆条目
        entry = MemoryEntry(
            content=content,
            embedding=embedding,
            metadata=metadata
        )
        
        self.memory_entries.append(entry)
        
        # 更新FAISS索引
        if self.index is not None:
            embedding_np = np.array([embedding], dtype=np.float32)
            if isinstance(self.index, type('')) or self.index is None:
                pass
            elif hasattr(self.index, 'is_trained') and not self.index.is_trained:
                self.index.train(embedding_np)
                self.index.add(embedding_np)
            else:
                self.index.add(embedding_np)
        
        # 更新内存中的向量数组
        self.embeddings = np.vstack([self.embeddings, embedding])
        
        print(f"[长期记忆] 添加记忆: {entry.id[:20]}...")
        
        return entry
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        搜索相关记忆
        :param query: 查询文本
        :param top_k: 返回数量
        :param similarity_threshold: 相似度阈值
        :return: 搜索结果列表
        """
        # 生成查询向量
        query_embedding = self._simple_embedding(query)
        
        if self.index is not None and len(self.memory_entries) > 0:
            # 使用FAISS搜索
            query_np = np.array([query_embedding], dtype=np.float32)
            
            try:
                distances, indices = self.index.search(query_np, top_k)
                
                results = []
                for i in range(min(top_k, len(indices[0]))):
                    idx = indices[0][i]
                    distance = distances[0][i]
                    
                    if idx >= 0 and idx < len(self.memory_entries):
                        entry = self.memory_entries[idx]
                        # 将距离转换为相似度 (L2距离越小越相似)
                        similarity = 1.0 / (1.0 + distance)
                        
                        if similarity >= similarity_threshold:
                            results.append({
                                "entry": entry,
                                "similarity": similarity,
                                "distance": float(distance)
                            })
                
                return results
            
            except Exception as e:
                print(f"[长期记忆] FAISS搜索失败，使用简单搜索: {str(e)}")
        
        # 使用简单余弦相似度搜索
        results = []
        for entry in self.memory_entries:
            if entry.embedding:
                similarity = self._compute_cosine_similarity(query_embedding, entry.embedding)
                
                if similarity >= similarity_threshold:
                    results.append({
                        "entry": entry,
                        "similarity": similarity,
                        "distance": 1.0 - similarity
                    })
        
        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:top_k]
    
    def get_memory_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        根据ID获取记忆
        :param memory_id: 记忆ID
        :return: 记忆条目
        """
        for entry in self.memory_entries:
            if entry.id == memory_id:
                return entry
        return None
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        :param memory_id: 记忆ID
        :return: 是否删除成功
        """
        for i, entry in enumerate(self.memory_entries):
            if entry.id == memory_id:
                del self.memory_entries[i]
                # 更新向量数组
                self.embeddings = np.delete(self.embeddings, i, axis=0)
                # 重建FAISS索引
                if self.index is not None:
                    self._init_faiss()
                    if len(self.embeddings) > 0:
                        self.index.add(self.embeddings.astype(np.float32))
                print(f"[长期记忆] 删除记忆: {memory_id}")
                return True
        return False
    
    def get_all_memories(self) -> List[MemoryEntry]:
        """获取所有记忆"""
        return self.memory_entries
    
    def get_memory_count(self) -> int:
        """获取记忆数量"""
        return len(self.memory_entries)
    
    def clear(self):
        """清空所有记忆"""
        self.memory_entries = []
        self.embeddings = np.empty((0, self.vector_dim))
        if self.index is not None:
            self._init_faiss()
        print("[长期记忆] 已清空")
    
    def save_to_disk(self):
        """保存记忆到磁盘"""
        # 保存记忆条目
        entries_file = os.path.join(self.storage_path, "entries.json")
        with open(entries_file, 'w', encoding='utf-8') as f:
            json.dump(
                [entry.to_dict() for entry in self.memory_entries],
                f,
                ensure_ascii=False,
                indent=2
            )
        
        # 保存向量数据
        vectors_file = os.path.join(self.storage_path, "embeddings.npy")
        if len(self.embeddings) > 0:
            np.save(vectors_file, self.embeddings)
        
        # 保存FAISS索引
        if self.index is not None:
            index_file = os.path.join(self.storage_path, "index.faiss")
            try:
                import faiss
                faiss.write_index(self.index, index_file)
            except:
                pass
        
        print(f"[长期记忆] 已保存到 {self.storage_path}")
    
    def load_from_disk(self):
        """从磁盘加载记忆"""
        # 加载记忆条目
        entries_file = os.path.join(self.storage_path, "entries.json")
        if os.path.exists(entries_file):
            with open(entries_file, 'r', encoding='utf-8') as f:
                entries_data = json.load(f)
                self.memory_entries = [
                    MemoryEntry.from_dict(data) for data in entries_data
                ]
        
        # 加载向量数据
        vectors_file = os.path.join(self.storage_path, "embeddings.npy")
        if os.path.exists(vectors_file):
            self.embeddings = np.load(vectors_file)
        
        # 加载FAISS索引
        index_file = os.path.join(self.storage_path, "index.faiss")
        if os.path.exists(index_file) and self.index is not None:
            try:
                import faiss
                self.index = faiss.read_index(index_file)
            except:
                pass
        
        print(f"[长期记忆] 已加载 {len(self.memory_entries)} 条记忆")
    
    def get_recent_memories(self, count: int = 10) -> List[MemoryEntry]:
        """
        获取最近的记忆
        :param count: 数量
        :return: 记忆列表
        """
        sorted_entries = sorted(self.memory_entries, key=lambda x: x.timestamp, reverse=True)
        return sorted_entries[:count]
    
    def search_by_keyword(self, keyword: str, top_k: int = 5) -> List[MemoryEntry]:
        """
        按关键词搜索记忆
        :param keyword: 关键词
        :param top_k: 返回数量
        :return: 记忆列表
        """
        keyword_lower = keyword.lower()
        results = []
        
        for entry in self.memory_entries:
            if keyword_lower in entry.content.lower():
                results.append(entry)
        
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:top_k]


def create_long_term_memory(
    storage_path: str = "memory_store",
    vector_dim: int = 768,
    index_type: str = "flat"
) -> LongTermMemory:
    """
    工厂函数：创建长期记忆实例
    :param storage_path: 存储路径
    :param vector_dim: 向量维度
    :param index_type: 索引类型
    :return: LongTermMemory实例
    """
    return LongTermMemory(storage_path, vector_dim, index_type)