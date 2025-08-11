import json
import os
from collections import OrderedDict

def sort_json_keys(input_file, output_file, indent=4):
    """
    将 JSON 文件的所有键按照字典顺序排序并保存到新文件
    
    :param input_file: 输入的 JSON 文件路径
    :param output_file: 输出的 JSON 文件路径
    :param indent: 缩进空格数，None 表示不格式化
    """
    try:
        # 读取原始 JSON 文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f, object_pairs_hook=OrderedDict)
        
        # 递归排序所有键
        sorted_data = sort_dict(data)
        
        # 写入排序后的 JSON 文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, ensure_ascii=False, indent=indent, sort_keys=True)
        
        print(f"成功生成排序后的 JSON 文件: {output_file}")
    
    except Exception as e:
        print(f"处理 JSON 文件时出错: {e}")

def sort_dict(d):
    """
    递归排序字典的所有键
    
    :param d: 要排序的字典或列表
    :return: 排序后的 OrderedDict 或原数据（如果不是字典）
    """
    if isinstance(d, dict):
        # 创建有序字典并按键排序
        sorted_dict = OrderedDict()
        for key in sorted(d.keys()):
            sorted_dict[key] = sort_dict(d[key])
        return sorted_dict
    elif isinstance(d, list):
        # 处理列表中的每个元素
        return [sort_dict(item) for item in d]
    else:
        # 其他类型直接返回
        return d

def main():
    # 获取当前工作目录
    current_dir = os.getcwd()
    
    # 设置默认文件名
    input_filename = "A.json"
    output_filename = "sorted_A.json"
    
    # 构建完整路径
    input_path = os.path.join(current_dir, input_filename)
    output_path = os.path.join(current_dir, output_filename)
    
    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        print(f"错误: 输入文件 {input_path} 不存在")
        return
    
    # 调用排序函数
    sort_json_keys(input_path, output_path, indent=4)

if __name__ == '__main__':
    main()