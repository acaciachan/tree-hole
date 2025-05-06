import os
import json
import pandas as pd
from collections import defaultdict

output_count = True  # 是否显示成组生成数量范围
output_zero_total_weight = True  # 是否显示没有任何刻生成生物的生物类别和生物群系

categories = ["monster", "creature", "ambient", "water_ambient",
              "water_creature", "underground_water_creature", "axolotls", "misc"]

data = {category: defaultdict(dict) for category in categories}

folder_path = "./biome"
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            spawners = json_data.get("spawners", {})
            biome_name = filename.split('.')[0]
            
            for category in categories:
                total_weight = 0
                for spawner in spawners.get(category, []):
                    # 提取生成信息
                    spawner_type = spawner["type"].split(":")[-1]
                    weight = spawner["weight"]
                    min_count = spawner["minCount"]
                    max_count = spawner["maxCount"]
                    
                    # 格式化数量显示
                    count_str = f"{min_count}-{max_count}" if min_count != max_count else str(min_count)
                    
                    if weight < 10 :
                        weight_value = f"  {weight}"
                    elif 10 <= weight < 100 :
                        weight_value = f" {weight}"
                    else :
                        weight_value = f"{weight}"
                    
                    if output_count :
                        display_value = f"{weight_value} {count_str}"
                    else :
                        display_value = f"{weight_value}"
                    
                    data[category][biome_name][spawner_type] = display_value
                    total_weight += weight
                
                # 总权重保持纯数字
                if output_zero_total_weight or total_weight > 0:
                    data[category][biome_name]["总权重"] = total_weight

with pd.ExcelWriter("biome.xlsx") as writer:
    for category in categories:
        df = pd.DataFrame(data[category]).T
        
        # 处理没有数据的群系
        df = df.dropna(how='all', axis=0)
        if df.empty:
            continue
                
        # 重置索引并重命名
        df = df.reset_index().rename(columns={"index": "群系"})
        
        # 调整列顺序：群系 -> 总权重 -> 其他生物
        cols = ["群系", "总权重"] + [c for c in df.columns if c not in ("群系", "总权重")]
        df = df[cols]
        
        # 写入Excel并设置格式
        df.to_excel(writer, sheet_name=category, index=False)
        worksheet = writer.sheets[category]

        for col_num, col_name in enumerate(df.columns):
            if col_name == "群系" or col_name == "总权重" :
                worksheet.set_column(col_num, col_num, 20)  # 加宽结构名称列
            else:
                worksheet.set_column(col_num, col_num, 10)

        worksheet.freeze_panes(1, 2)  # 冻结首行和前两列

print("Excel文件已生成：biome.xlsx")
