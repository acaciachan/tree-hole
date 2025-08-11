# merge_json.py
import os
import json
import re
from collections import defaultdict

def merge_split_files(directory=".", max_entries=1000):
    # 匹配 【拆分N】开头的文件
    pattern = re.compile(r"【拆分(\d+)】(.+\.json)")

    # 按原文件名分组
    grouped_files = defaultdict(list)

    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            index = int(match.group(1))
            original_name = match.group(2)
            grouped_files[original_name].append((index, filename))

    if not grouped_files:
        print("未找到以 【拆分】 开头的 JSON 文件。")
        return

    for original_base, file_list in grouped_files.items():
        # 按编号排序
        file_list.sort(key=lambda x: x[0])
        print(f"正在合并 {original_base} 的 {len(file_list)} 个拆分文件...")

        merged_data = {}

        for index, fname in file_list:
            filepath = os.path.join(directory, fname)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    print(f"警告：文件 {fname} 不是字典格式，跳过。")
                    continue
                merged_data.update(data)
            except Exception as e:
                print(f"读取失败 {fname}: {e}")

        # 写入合并文件
        output_filename = f"【合并】{original_base}"
        output_path = os.path.join(directory, output_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)

        print(f"合并完成: {output_filename} (共 {len(merged_data)} 条记录)")

if __name__ == "__main__":
    merge_split_files(".")