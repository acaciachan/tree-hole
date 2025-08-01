import os
import shutil
import re

def read_clear_file(clear_file):
    """读取 clear.txt 文件，分离需要清理的条目和例外条目"""
    to_clear = []
    exceptions = []
    
    with open(clear_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:  # 跳过空行
                continue
            if line.startswith('-'):
                exceptions.append(line[1:].strip())
            else:
                to_clear.append(line)
    
    return to_clear, exceptions

def should_clear(rel_path, to_clear, exceptions):
    """判断一个路径是否需要清理"""
    # 将路径统一为正斜杠，便于匹配
    rel_path = rel_path.replace('\\', '/')
    
    # 检查是否匹配例外
    for exc in exceptions:
        exc = exc.replace('\\', '/')
        if re.fullmatch(exc, rel_path):
            return False
    
    # 检查是否匹配需要清理的条目
    for pattern in to_clear:
        pattern = pattern.replace('\\', '/')
        # 将 * 转换为正则表达式的 .*
        regex_pattern = pattern.replace('.', r'\.').replace('*', '.*')
        if re.fullmatch(regex_pattern, rel_path):
            return True
    
    return False

def clean_version_directory(version_dir, to_clear, exceptions):
    """清理单个版本目录下的垃圾文件和文件夹"""
    for root, dirs, files in os.walk(version_dir, topdown=False):
        # 处理文件
        for name in files:
            file_path = os.path.join(root, name)
            rel_path = os.path.relpath(file_path, version_dir)
            if should_clear(rel_path, to_clear, exceptions):
                try:
                    os.remove(file_path)
                    print(f"已删除文件: {file_path}")
                except Exception as e:
                    print(f"删除文件 {file_path} 失败: {e}")
        
        # 处理文件夹
        for name in dirs:
            dir_path = os.path.join(root, name)
            rel_path = os.path.relpath(dir_path, version_dir)
            if should_clear(rel_path, to_clear, exceptions):
                try:
                    shutil.rmtree(dir_path)
                    print(f"已删除文件夹: {dir_path}")
                except Exception as e:
                    print(f"删除文件夹 {dir_path} 失败: {e}")

def main():
    """主函数"""
    versions_dir = r"D:\Minecraft\.minecraft\versions"
    clear_file = "clean_minecraft.txt"
    
    # 读取清理规则
    to_clear, exceptions = read_clear_file(clear_file)
    
    # 遍历所有版本目录
    for version in os.listdir(versions_dir):
        version_path = os.path.join(versions_dir, version)
        if os.path.isdir(version_path):
            print(f"正在清理版本目录: {version_path}")
            clean_version_directory(version_path, to_clear, exceptions)
            print(f"完成清理: {version_path}\n")

if __name__ == "__main__":
    main()