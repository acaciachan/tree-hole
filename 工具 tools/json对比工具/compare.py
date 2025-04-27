# 此代码由DeepSeek-R1生成，只会选文件夹里的一个文件对比(不要求名字相同，所以建议保证old和new初面都只有一个文件)
# 用法：在old和new分别放要比较的新旧文件，运行compare.py，即可看到生成了compare.json文件：
# addition  :   增加的部分
# deletion  :   删除的部分
# modifications      :   key(左侧键)一样，但是value(右侧值)不一样

output_origin = False # 是否保留原始数据

import os
import json
from pathlib import Path

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

def find_first_json(folder):
    return next((Path(folder)/f for f in os.listdir(folder) if f.endswith('.json')), None)

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
    if output_origin:
        result.update({
            "old_version": old_data,
            "new_version": new_data
        })
    
    return result

def main():
    old_file = find_first_json('old')
    new_file = find_first_json('new')

    if not old_file or not new_file:
        print("Error: 缺少JSON文件")
        return

    with open(old_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    with open(new_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)

    comparison = generate_comparison(old_data, new_data)

    with open('compare.json', 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    stats = comparison.copy()
    stats.pop('old_version', None)
    stats.pop('new_version', None)
    
    print(f"""对比完成！
    新增条目: {len(stats['additions'])}
    删除条目: {len(stats['deletions'])}
    修改条目: {len(stats['modifications'])}
    完整结果已保存至 compare.json""")

if __name__ == '__main__':
    main()
