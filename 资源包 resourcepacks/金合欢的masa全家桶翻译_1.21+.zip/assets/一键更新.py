import os

def process_files_and_folders():
    """处理文件和文件夹配对，替换zh_cn.json文件"""
    
    # 预定义的文件夹列表
    folders = [
        "itemscroller", "litematica", "litematica-printer", "malilib", "minihud",
        "servux", "syncmatica", "tweakeroo", "vkm"
    ]
    
    current_dir = os.getcwd()
    json_files = [f for f in os.listdir(current_dir) if f.endswith('.json')]
    
    print(f"找到 {len(json_files)} 个JSON文件")
    processed_count = 0
    
    for folder in folders:
        # 查找匹配的JSON文件
        matching_files = [f for f in json_files if f.startswith(folder + '-')]
        
        if not matching_files:
            print(f"未找到匹配文件: {folder}")
            continue
            
        json_file = matching_files[0]
        lang_dir = os.path.join(folder, "lang")
        target_path = os.path.join(lang_dir, "zh_cn.json")
        
        if not os.path.exists(lang_dir):
            print(f"目录不存在: {lang_dir}")
            continue
        
        # 删除原有的zh_cn.json（直接删除，不进回收站）
        if os.path.exists(target_path):
            os.remove(target_path)
            print(f"已删除: {target_path}")
        
        # 移动并重命名文件
        os.rename(json_file, target_path)
        print(f"已移动: {json_file} -> {target_path}")
        processed_count += 1
    
    print(f"\n处理完成！共处理 {processed_count} 个文件")

if __name__ == "__main__":
    process_files_and_folders()