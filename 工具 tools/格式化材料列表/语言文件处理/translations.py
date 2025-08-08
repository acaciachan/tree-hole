import json
import os
import csv
from collections import defaultdict

def extract_translations(folder_path):
    # 获取所有语言文件
    lang_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    
    # 初始化数据结构
    translations = defaultdict(dict)
    all_keys = set()
    prefixes = ['block.minecraft.', 'item.minecraft.', 'entity.minecraft.']
    
    # 读取所有语言文件
    for lang_file in lang_files:
        lang_code = os.path.splitext(lang_file)[0]
        with open(os.path.join(folder_path, lang_file), 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 提取符合条件的键值对
            for key, value in data.items():
                if any(key.startswith(prefix) for prefix in prefixes):
                    translations[key][lang_code] = value
                    all_keys.add(key)
    
    return translations, sorted(all_keys), lang_files

def create_csv(translations, all_keys, lang_files, output_file):
    # 获取语言代码列表
    lang_codes = [os.path.splitext(f)[0] for f in lang_files]
    
    # 写入CSV文件
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # 写入标题行
        headers = ['Key Type', 'Key'] + lang_codes
        writer.writerow(headers)
        
        # 写入数据行
        for key in sorted(all_keys):
            # 确定键的类型
            if key.startswith('block.minecraft.'):
                key_type = 'block'
                short_key = key[len('block.minecraft.'):]
            elif key.startswith('item.minecraft.'):
                key_type = 'item'
                short_key = key[len('item.minecraft.'):]
            elif key.startswith('entity.minecraft.'):
                key_type = 'entity'
                short_key = key[len('entity.minecraft.'):]
            else:
                key_type = 'other'
                short_key = key
            
            # 收集所有语言的翻译
            row = [key_type, short_key]
            for lang in lang_codes:
                row.append(translations[key].get(lang, ''))
            
            writer.writerow(row)

def main():
    folder_path = '.'  # 当前目录
    output_file = 'translations.csv'
    
    translations, all_keys, lang_files = extract_translations(folder_path)
    create_csv(translations, all_keys, lang_files, output_file)
    print(f"翻译已导出到 {output_file}")

if __name__ == '__main__':
    main()