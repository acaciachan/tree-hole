import os
import json

def convert_txt_to_json(input_folder, output_folder):
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历input文件夹中的所有文件
    for filename in os.listdir(input_folder):
        # 只处理.txt文件
        if filename.endswith(".txt"):
            # 构建输入文件的完整路径
            input_file = os.path.join(input_folder, filename)
            
            # 构建输出文件的完整路径（将.txt替换为.json）
            output_file = os.path.join(output_folder, filename.replace(".txt", "_CommandKeys.json"))

            # 读取输入文件
            with open(input_file, 'r', encoding='utf-8') as file:
                commands = file.readlines()

            # 过滤掉空行和注释行
            commands = [cmd.strip() for cmd in commands if cmd.strip() and not cmd.strip().startswith('#')]

            # 处理每条指令，并生成对应的setDefault指令
            processed_commands = []
            for cmd in commands:
                # 如果指令以"/carpet"开头，生成对应的setDefault指令
                if cmd.startswith("/carpet"):
                    set_default_cmd = cmd.replace("/carpet", "/carpet setDefault")
                    processed_commands.append(cmd)
                    processed_commands.append(set_default_cmd)
                else:
                    processed_commands.append(cmd)

            # 构建JSON结构
            json_data = {
                "messages": [
                    {
                        "version": 1,
                        "string": cmd,
                        "delayTicks": 1
                    }
                    for cmd in processed_commands
                ]
            }

            # 将JSON数据写入输出文件，保留前面的空格
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, indent=2, ensure_ascii=False)

            print(f"已转换文件: {input_file} -> {output_file}")

# 使用示例
input_folder = 'input'  # 输入文件夹路径
output_folder = 'output'  # 输出文件夹路径
convert_txt_to_json(input_folder, output_folder)
