import json

def compare_json_keys(file_a, file_b, output_a_minus_b, output_b_minus_a):
    """
    比较两个 JSON 文件，找出各自独有的 key（及其 value），并保存为两个 JSON 文件。

    :param file_a: 第一个 JSON 文件路径
    :param file_b: 第二个 JSON 文件路径
    :param output_a_minus_b: A 比 B 多出的 key-value 保存文件路径
    :param output_b_minus_a: B 比 A 多出的 key-value 保存文件路径
    """
    try:
        # 读取两个 JSON 文件
        with open(file_a, 'r', encoding='utf-8') as f:
            data_a = json.load(f)
        with open(file_b, 'r', encoding='utf-8') as f:
            data_b = json.load(f)

        # 确保数据是字典类型
        if not isinstance(data_a, dict):
            raise ValueError(f"{file_a} 的内容不是 JSON 对象（字典）")
        if not isinstance(data_b, dict):
            raise ValueError(f"{file_b} 的内容不是 JSON 对象（字典）")

        # 获取 key 集合
        keys_a = set(data_a.keys())
        keys_b = set(data_b.keys())

        # 找出 A 有而 B 没有的 key
        only_in_a = keys_a - keys_b
        # 找出 B 有而 A 没有的 key
        only_in_b = keys_b - keys_a

        # 提取对应的 key-value
        a_minus_b = {key: data_a[key] for key in only_in_a}
        b_minus_a = {key: data_b[key] for key in only_in_b}

        # 保存到文件
        with open(output_a_minus_b, 'w', encoding='utf-8') as f:
            json.dump(a_minus_b, f, ensure_ascii=False, indent=2)
        
        with open(output_b_minus_a, 'w', encoding='utf-8') as f:
            json.dump(b_minus_a, f, ensure_ascii=False, indent=2)

        print(f"比较完成！")
        print(f"A 比 B 多出 {len(only_in_a)} 个 key，已保存至: {output_a_minus_b}")
        print(f"B 比 A 多出 {len(only_in_b)} 个 key，已保存至: {output_b_minus_a}")

    except FileNotFoundError as e:
        print(f"文件未找到: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON 解码错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

# 使用示例
if __name__ == "__main__":
    A_FILE = "A.json"
    B_FILE = "B.json"
    OUTPUT_A_MINUS_B = "A_minus_B.json"
    OUTPUT_B_MINUS_A = "B_minus_A.json"

    compare_json_keys(A_FILE, B_FILE, OUTPUT_A_MINUS_B, OUTPUT_B_MINUS_A)