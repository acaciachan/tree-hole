import os
import json
import pandas as pd
from collections import defaultdict

output_count = True  # 是否显示成组生成数量范围
output_zero_total_weight = False  # 是否显示没有任何刻生成生物的生物类别和生物群系

categories = ["monster", "creature", "ambient", "water_ambient",
              "water_creature", "underground_water_creature", "axolotls", "misc"]

data = {category: defaultdict(dict) for category in categories}

folder_path = "./structure"
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            spawn_overrides = json_data.get("spawn_overrides", {})
            
            # 从type字段提取结构（去掉命名空间）
            structure_name = filename.split('.')[0]
            
            for category in categories:
                total_weight = 0
                spawn_info = spawn_overrides.get(category, {})
                for spawner in spawn_info.get("spawns", []):
                    # 提取生成信息
                    spawner_type = spawner["type"].split(":")[-1]
                    weight = spawner["weight"]
                    min_count = spawner["minCount"]
                    max_count = spawner["maxCount"]
                    
                    # 格式化显示（保持与群系版相同逻辑）
                    count_str = f"{min_count}-{max_count}" if min_count != max_count else str(min_count)
                    
                    # 权重对齐格式
                    if weight < 10 :
                        weight_value = f"  {weight}"
                    elif 10 <= weight < 100 :
                        weight_value = f" {weight}"
                    else :
                        weight_value = f"{weight}"
                    
                    # 根据标志组合显示值
                    if output_count :
                        display_value = f"{weight_value} {count_str}"
                    else :
                        display_value = f"{weight_value}"
                    
                    data[category][structure_name][spawner_type] = display_value
                    total_weight += weight
                
                # 总权重保持纯数字（仅在有权重时添加）
                if output_zero_total_weight or total_weight > 0:
                    data[category][structure_name]["总权重"] = total_weight

with pd.ExcelWriter("structure.xlsx") as writer:
    for category in categories:
        df = pd.DataFrame(data[category]).T
        
        # 清理空数据（保留至少有一个数据的行）
        df = df.dropna(how='all', axis=0)
        if df.empty:
            continue
        
        # 重置索引并重命名
        df = df.reset_index().rename(columns={"index": "结构"})
        
        # 调整列顺序：结构 -> 总权重 -> 其他生物
        cols = ["结构", "总权重"] + [c for c in df.columns if c not in ("结构", "总权重")]
        df = df[cols]
        
        # 写入Excel并设置格式
        df.to_excel(writer, sheet_name=category, index=False)
        worksheet = writer.sheets[category]

        for col_num, col_name in enumerate(df.columns):
            if col_name == "结构" or col_name == "总权重" :
                worksheet.set_column(col_num, col_num, 20)  # 加宽结构列
            else:
                worksheet.set_column(col_num, col_num, 10)

        worksheet.freeze_panes(1, 2)  # 冻结首行和前两列（保持与群系版一致）

print("Excel文件已生成：structure.xlsx")
