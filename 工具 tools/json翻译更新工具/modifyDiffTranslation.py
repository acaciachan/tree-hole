import json
from collections import OrderedDict

# 可配置的文件路径变量
OLD_EN_US_FILE = 'en_us.json'
NEW_EN_US_FILE = 'en_us (2).json'
OLD_ZH_CN_FILE = 'zh_cn.json'
NEW_ZH_CN_FILE = 'zh_cn (2).json'
DIFF_FILE = 'diff.json'

def load_ordered_json(file_path):
    """加载JSON文件并保留键的顺序"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f, object_pairs_hook=OrderedDict)
    except FileNotFoundError:
        return OrderedDict()

def save_ordered_json(data, file_path):
    """保存有序字典到JSON文件，保持格式"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))

def process_level(new_en_data, old_zh_data, additions, deletions, modifications, current_path=''):
    """递归处理每个层级"""
    new_zh = OrderedDict()
    
    for key in new_en_data:
        en_value = new_en_data[key]
        full_path = f"{current_path}.{key}" if current_path else key

        # 处理被删除的键
        if full_path in deletions:
            continue

        # 处理嵌套对象
        if isinstance(en_value, dict):
            old_sub = old_zh_data.get(key, OrderedDict())
            new_sub = process_level(en_value, old_sub, additions, deletions, modifications, full_path)
            new_zh[key] = new_sub
            continue;

        # 处理叶子节点
        if full_path in additions:
            new_zh[key] = additions[full_path]
        elif full_path in modifications:
            new_zh[key] = modifications[full_path]['new']
        else:
            new_zh[key] = old_zh_data.get(key, f"MISSING: {full_path}")
            
    return new_zh

def main():
    # 加载输入文件
    new_en = load_ordered_json(NEW_EN_US_FILE)
    old_zh = load_ordered_json(OLD_ZH_CN_FILE)
    
    # 加载差异文件
    with open(DIFF_FILE, 'r', encoding='utf-8') as f:
        diff = json.load(f)
    
    # 生成新的中文文件
    new_zh = process_level(
        new_en_data=new_en,
        old_zh_data=old_zh,
        additions=diff.get('additions', {}),
        deletions=diff.get('deletions', []),
        modifications=diff.get('modifications', {})
    )
    
    # 保存结果
    save_ordered_json(new_zh, NEW_ZH_CN_FILE)
    print(f"成功生成新版中文文件：{NEW_ZH_CN_FILE}")

if __name__ == '__main__':
    main()
