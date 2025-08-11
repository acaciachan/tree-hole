import json

def generate_message_json(template, start_n, end_n, output_file):
    messages = []
    for n in range(start_n, end_n + 1):
        message = {
            "version": 1,
            "string": template.format(n=n),
            "delayTicks": 0
        }
        messages.append(message)
    
    data = {
        "messages": messages
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"文件已成功生成：{output_file}")

# 示例使用
if __name__ == "__main__":
    template = "/player {n} kill"  # 模板字符串
    start_n = 0     # 起始n
    end_n = 1000    # 结束n
    output_file = "messages_output.txt"  # 输出文件名
    
    generate_message_json(template, start_n, end_n, output_file)