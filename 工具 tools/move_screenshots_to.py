import os
import shutil
import re

def is_image_file(filename):
    """检查文件是否为图片格式"""
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    return filename.lower().endswith(image_extensions)

def get_unique_filename(target_dir, original_filename):
    """生成不冲突的目标文件名，模仿 Windows 的 (2)、(3) 规则"""
    base, ext = os.path.splitext(original_filename)
    target_path = os.path.join(target_dir, original_filename)
    counter = 2

    while os.path.exists(target_path):
        # 构造新文件名，例如 "file (2).png"
        new_filename = f"{base} ({counter}){ext}"
        target_path = os.path.join(target_dir, new_filename)
        counter += 1

    return target_path

def move_screenshots(version_dir, target_dir):
    """从单个版本目录的 screenshots 文件夹搬移图片到目标目录"""
    screenshots_dir = os.path.join(version_dir, "screenshots")
    
    # 检查 screenshots 目录是否存在
    if not os.path.isdir(screenshots_dir):
        print(f"跳过 {version_dir}：未找到 screenshots 文件夹")
        return
    
    # 遍历 screenshots 目录中的文件
    for filename in os.listdir(screenshots_dir):
        if not is_image_file(filename):
            print(f"跳过 {filename}：非图片文件")
            continue
        
        source_path = os.path.join(screenshots_dir, filename)
        if not os.path.isfile(source_path):
            continue
        
        # 获取不冲突的目标路径
        target_path = get_unique_filename(target_dir, filename)
        
        try:
            # 搬移文件
            shutil.move(source_path, target_path)
            print(f"已搬移: {source_path} -> {target_path}")
        except Exception as e:
            print(f"搬移失败: {source_path} -> {target_path}, 错误: {e}")

def main():
    """主函数"""
    versions_dir = r"D:\Minecraft\.minecraft\versions"
    target_dir = r"D:\Minecraft\history 历史记录"
    
    # 确保目标目录存在
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"已创建目标目录: {target_dir}")
    
    # 遍历所有版本目录
    for version in os.listdir(versions_dir):
        version_path = os.path.join(versions_dir, version)
        if os.path.isdir(version_path):
            print(f"处理版本目录: {version_path}")
            move_screenshots(version_path, target_dir)
            print(f"完成处理: {version_path}\n")

if __name__ == "__main__":
    main()