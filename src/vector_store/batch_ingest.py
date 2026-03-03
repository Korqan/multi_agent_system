import os
from pathlib import Path
# 引入我们刚才写的单文件处理函数
from ingest_single import ingest_single_document 

def batch_ingest_from_directory(root_dir):
    """
    遍历指定根目录。
    假设目录结构为:
    /data_root/
        ├── 安全行业/
        │   ├── 规范1.pdf
        │   └── 手册2.docx
        ├── 危化行业/
        │   └── 管理办法.pdf
    """
    root_path = Path(root_dir)
    if not root_path.exists() or not root_path.is_dir():
        print(f"[!] 错误: 根目录 {root_dir} 不存在或不是一个文件夹。")
        return

    print(f">>> 开始扫描根目录: {root_dir}")
    
    success_count = 0
    fail_count = 0

    # 递归查找所有的 pdf 和 docx 文件
    for file_path in root_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.docx']:
            # 核心逻辑：获取该文件所在的直接父文件夹名称，作为“行业名称”
            chinese_industry_name = file_path.parent.name
            
            try:
                # 调用我们在 2_ingest_single.py 中定义的核心函数
                result = ingest_single_document(str(file_path), chinese_industry_name)
                if result:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                print(f"[!] 处理文件时发生崩溃 {file_path}: {e}")
                fail_count += 1

    print("-" * 30)
    print(f">>> 批量导入任务完成！成功: {success_count} 个文件, 失败/跳过: {fail_count} 个文件。")

if __name__ == "__main__":
    # 请将此处替换为你存放所有行业文件夹的绝对或相对路径
    # 例如：ROOT_DATA_FOLDER = "/Users/yourname/Documents/行业资料库"
    ROOT_DATA_FOLDER = "./my_industry_data" 
    
    batch_ingest_from_directory(ROOT_DATA_FOLDER)