# config.py
# 全局行业映射字典
INDUSTRY_MAPPING = {
    "安全": "security",
    "危化": "hazardous",
    "环保": "environmental"
}
VECTOR_DIM = 1024 # 统一的向量维度config

def get_collection_name(industry_name: str) -> str:
    """
    Get the configured collection name for the given industry.
    Raises ValueError if the industry is not found in the mapping.
    """
    collection_name = INDUSTRY_MAPPING.get(industry_name)
    if not collection_name:
        raise ValueError(f"Industry '{industry_name}' is not configured in INDUSTRY_MAPPING.")
    return collection_name
import os
import yaml
import logging
import sys
from typing import Any, Dict


class ConfigLoader:
    """
    配置加载器 (单例模式)
    负责加载 settings.yaml 和 prompts.yaml，并初始化系统目录和日志
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 避免重复初始化
        if self._initialized:
            return

        # 1. 计算项目根目录 (基于当前文件的相对位置)
        # src/config_loader.py -> src -> project_root
        current_file_path = os.path.abspath(__file__)
        self.project_root = os.path.dirname(os.path.dirname(current_file_path))

        # 2. 加载 YAML 配置
        self._config = self._load_yaml("settings.yaml")
        self._prompts = self._load_yaml("prompts.yaml")

        # 3. 路径标准化处理 (将相对路径转换为绝对路径)
        self._normalize_paths()

        # 4. 创建必要的系统目录
        self._ensure_dirs()

        # 5. 初始化日志系统
        self._setup_logging()

        self._initialized = True
        # 此时日志已配置好，可以使用 logger
        logging.getLogger(__name__).info(f"⚙️ 配置加载完成。项目根目录: {self.project_root}")

    def _load_yaml(self, file_name: str) -> Dict[str, Any]:
        """通用 YAML 读取函数"""
        path = os.path.join(self.project_root, "config", file_name)
        if not os.path.exists(path):
            # 如果配置目录没找到，尝试在当前目录找（兼容某些特殊运行环境）
            error_msg = f"配置文件未找到: {path}。请确保 config/ 目录位于项目根目录下。"
            print(f"❌ {error_msg}")
            raise FileNotFoundError(error_msg)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise RuntimeError(f"读取配置文件 {file_name} 失败: {e}")

    def _normalize_paths(self):
        """将配置文件中的相对路径转换为绝对路径"""
        if 'paths' in self._config:
            for key, path in self._config['paths'].items():
                if path and not os.path.isabs(path):
                    self._config['paths'][key] = os.path.join(self.project_root, path)

        if 'vector_db' in self._config and 'persist_directory' in self._config['vector_db']:
            path = self._config['vector_db']['persist_directory']
            if path and not os.path.isabs(path):
                self._config['vector_db']['persist_directory'] = os.path.join(self.project_root, path)

    def _ensure_dirs(self):
        """根据 settings.yaml 中的 paths 配置，自动创建文件夹"""
        paths = self._config.get('paths', {})

        # 1. 创建 Data Root
        data_root = paths.get('data_root')
        if data_root and not os.path.exists(data_root):
            os.makedirs(data_root, exist_ok=True)

        # 2. 创建日志目录 (如果 global_log_file 定义了)
        log_file = paths.get('global_log_file')
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

        # 3. 创建向量库目录
        vec_dir = self._config.get('vector_db', {}).get('persist_directory')
        if vec_dir and not os.path.exists(vec_dir):
            os.makedirs(vec_dir, exist_ok=True)

    def _setup_logging(self):
        """初始化全局日志配置"""
        # 防止重复配置导致日志重复打印
        if logging.getLogger().hasHandlers():
            return

        log_file_path = self._config.get('paths', {}).get('global_log_file', 'system.log')

        # 获取日志级别配置
        # 之前的配置结构里 logging 是个 key，如果 yaml 没配则默认 INFO
        level_str = "INFO"
        # 注意：这里我们假设 settings.yaml 里可能有 logging: level: INFO 结构，或者直接硬编码
        # 为了健壮性，这里写死默认 INFO，也可以从 config 读取

        log_format = '%(asctime)s [%(levelname)s] [%(name)s]: %(message)s'

        handlers = [logging.StreamHandler(sys.stdout)]

        # 只有在路径存在时才添加文件 Handler
        try:
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            handlers.append(file_handler)
        except Exception as e:
            print(f"⚠️ 无法创建日志文件 {log_file_path}: {e}")

        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=handlers
        )

    @property
    def config(self) -> Dict[str, Any]:
        """获取环境配置"""
        return self._config

    @property
    def prompts(self) -> Dict[str, Any]:
        """获取 Prompt 配置"""
        return self._prompts


# 全局单例实例
settings = ConfigLoader()