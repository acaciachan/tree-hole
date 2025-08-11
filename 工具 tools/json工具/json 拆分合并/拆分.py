# split_json.py
import os
import json
import glob

def split_json_file(input_file, max_entries=1000):
    # 检查是否是【拆分】或【合并】开头，如果是则跳过
    basename = os.path.basename(input_file)
    if basename.startswith("【拆分】") or basename.startswith("【合并】"):
        print(f"跳过文件: {input_file} (已拆分或合并文件)")
        return

    # 读取原始 JSON 文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取文件失败 {input_file}: {e}")
        return

    if not isinstance(data, dict):
        print(f"文件 {input_file} 不是键值字典格式，跳过。")
        return

    items = list(data.items())
    total = len(items)

    # 计算需要多少个文件
    num_files = (total + max_entries - 1) // max_entries  # 向上取整

    base_name = os.path.splitext(basename)[0]
    ext = os.path.splitext(basename)[1]

    print(f"开始拆分 {input_file}，共 {total} 条，拆成 {num_files} 个文件...")

    for i in range(num_files):
        start_idx = i * max_entries
        end_idx = start_idx + max_entries
        chunk = dict(items[start_idx:end_idx])

        # 生成新文件名：【拆分1】原文件名.json
        output_filename = f"【拆分{i+1}】{base_name}{ext}"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        print(f"已生成: {output_filename}")

    print(f"拆分完成：{input_file} -> {num_files} 个文件")

if __name__ == "__main__":
    # 可以修改目录路径
    directory = "."  # 当前目录

    # 查找所有 .json 文件
    json_files = glob.glob(os.path.join(directory, "*.json"))

    for file in json_files:
        split_json_file(file)