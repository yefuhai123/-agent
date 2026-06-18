"""
配置管理模块
统一管理项目所有配置项，从.env文件加载环境变量
提供类型安全的配置访问接口
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    全局配置类
    封装所有环境变量和配置参数
    """
    
    # DeepSeek API配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL_NAME: str = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    
    # 模型参数配置
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P: float = float(os.getenv("TOP_P", "0.9"))
    
    # 向量存储配置
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "data/vector_store/agent_memory.index")
    KNOWLEDGE_BASE_PATH: str = os.getenv("KNOWLEDGE_BASE_PATH", "data/knowledge_base/")
    
    # Streamlit配置
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # 工具配置
    MAX_WEB_SEARCH_RESULTS: int = 5
    MAX_DOCUMENT_CHUNKS: int = 3
    CODE_EXECUTION_TIMEOUT: int = 30
    
    @property
    def is_api_key_set(self) -> bool:
        """检查API密钥是否已配置"""
        return bool(self.DEEPSEEK_API_KEY and self.DEEPSEEK_API_KEY != "your_deepseek_api_key_here")
    
    def validate_config(self) -> bool:
        """
        验证配置完整性
        返回True表示配置有效，False表示存在缺失
        """
        missing_items = []
        
        if not self.is_api_key_set:
            missing_items.append("DEEPSEEK_API_KEY")
        
        if missing_items:
            print(f"[错误] 缺少必要配置项: {', '.join(missing_items)}")
            print("请在.env文件中配置完整的API密钥")
            return False
        
        return True


settings = Settings()


def get_settings() -> Settings:
    """
    获取全局配置实例
    提供单例模式的配置访问接口
    """
    return settings