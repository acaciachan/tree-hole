# 此代码由DeepSeek-R1生成，此版本能一次性比较多阻json文件(文件名要相同)
# 用法：在old和new分别放要比较的新旧文件，运行compare.py，即可看到生成了compare.json文件：
# addition  :   增加的部分
# deletion  :   删除的部分
# modifications      :   key(左侧键)一样，但是value(右侧值)不一样

ouput_original = False # 是否保留原始数据

import os
import json
from pathlib import Path
from collections import defaultdict

def flatten_dict(d, parent_key='', sep='.'):
    """处理嵌套字典为带点号的单层结构"""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items

def get_json_files(folder):
    """获取文件夹内所有JSON文件的文件名（无后缀）"""
    return {f.stem: f for f in Path(folder).glob("*.json")}

def generate_comparison(old_data, new_data, output_original=True):
    """生成对比报告，包含统计信息"""
    old_flat = flatten_dict(old_data)
    new_flat = flatten_dict(new_data)
    
    additions = {k: new_flat[k] for k in new_flat if k not in old_flat}
    deletions = {k: old_flat[k] for k in old_flat if k not in new_flat}
    modifications = {
        k: {"old": old_flat[k], "new": new_flat[k]}
        for k in new_flat if k in old_flat and new_flat[k] != old_flat[k]
    }
    
    # 基础结构
    result = {
        "statistics": {
            "additions_count": len(additions),
            "deletions_count": len(deletions),
            "modifications_count": len(modifications),
            "total_changes": len(additions) + len(deletions) + len(modifications)
        },
        "additions": additions,
        "deletions": deletions,
        "modifications": modifications
    }
    
    # 可选保留原始数据
    if output_original:
        result.update({
            "old_version": old_data,
            "new_version": new_data
        })
    
    return result


def main():
    # 获取所有匹配的文件对
    old_files = get_json_files("old")
    new_files = get_json_files("new")
    common_files = set(old_files.keys()) & set(new_files.keys())

    if not common_files:
        print("Error: 未找到同名JSON文件")
        return

    total_stats = defaultdict(int)
    
    for filename in common_files:
        # 读取文件
        with open(old_files[filename], 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        with open(new_files[filename], 'r', encoding='utf-8') as f:
            new_data = json.load(f)

        # 生成对比结果
        comparison = generate_comparison(old_data, new_data)
        
        # 写入文件
        output_file = f"compare_{filename}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)

        # 统计信息
        for category in ['additions', 'deletions', 'modifications']:
            total_stats[category] += len(comparison[category])

        print(f"生成文件: {output_file}")
        print(f"  - 新增: {len(comparison['additions'])} 删除: {len(comparison['deletions'])} 修改: {len(comparison['modifications'])}")

    print(f"\n总计处理 {len(common_files)} 个文件:")
    print(f"总新增条目: {total_stats['additions']}")
    print(f"总删除条目: {total_stats['deletions']}")
    print(f"总修改条目: {total_stats['modifications']}")

if __name__ == '__main__':
    main()
