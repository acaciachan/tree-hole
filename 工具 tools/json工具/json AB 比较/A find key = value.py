import json

def extract_key_value_equal(file_a, output_file):
    """
    提取 A.json 中 key 和 value 相等的条目，保存为新 JSON 文件。

    :param file_a: 输入的 JSON 文件路径
    :param output_file: 输出文件路径
    """
    try:
        # 读取 JSON 文件
        with open(file_a, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查是否为字典
        if not isinstance(data, dict):
            raise ValueError(f"{file_a} 的内容不是 JSON 对象（字典）")

        # 找出 key 和 str(value) 相等的项
        same_items = {}
        for key, value in data.items():
            # 将 value 转为字符串进行比较（避免类型不同导致不匹配）
            if str(key) == str(value):
                same_items[key] = value  # 保留原始 value 类型

        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(same_items, f, ensure_ascii=False, indent=2)

        print(f"已完成：找到 {len(same_items)} 个 key 与 value 相等的项")
        print(f"结果已保存至: {output_file}")

    except FileNotFoundError:
        print(f"错误：找不到文件 {file_a}")
    except json.JSONDecodeError as e:
        print(f"JSON 解码错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

# 使用示例
if __name__ == "__main__":
    A_FILE = "A.json"
    OUTPUT_FILE = "A_same.json"
    extract_key_value_equal(A_FILE, OUTPUT_FILE)