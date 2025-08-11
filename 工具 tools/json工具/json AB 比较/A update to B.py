import json

def update_json_keep_b_keys_only(file_a, file_b, output_file):
    """
    将 A.json 的值复制给 B.json，但仅限于 B 中已存在的 key。

    :param file_a: 源 JSON 文件路径（从中取值）
    :param file_b: 目标 JSON 文件路径（只更新它已有的 key）
    :param output_file: 输出更新后的 B 文件路径
    """
    try:
        # 读取两个 JSON 文件
        with open(file_a, 'r', encoding='utf-8') as f:
            data_a = json.load(f)
        with open(file_b, 'r', encoding='utf-8') as f:
            data_b = json.load(f)

        # 确保是字典类型
        if not isinstance(data_a, dict):
            raise ValueError(f"{file_a} 不是 JSON 对象（字典）")
        if not isinstance(data_b, dict):
            raise ValueError(f"{file_b} 不是 JSON 对象（字典）")

        # 遍历 B 的所有 key，如果 A 中有对应 key，则更新 B 的值
        updated_count = 0
        for key in data_b:
            if key in data_a:
                old_value = data_b[key]
                new_value = data_a[key]
                if old_value != new_value:
                    data_b[key] = new_value
                    updated_count += 1

        # 保存更新后的 B
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_b, f, ensure_ascii=False, indent=2)

        print(f"合并完成！")
        print(f"共更新了 {updated_count} 个 key 的值（仅限 B 原本存在的 key）")
        print(f"结果已保存至: {output_file}")

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
    OUTPUT_FILE = "B_updated.json"

    update_json_keep_b_keys_only(A_FILE, B_FILE, OUTPUT_FILE)