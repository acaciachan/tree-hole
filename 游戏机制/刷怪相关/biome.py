import os
import json
import pandas as pd
from collections import defaultdict

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
                    # 去除 "minecraft:" 前缀
                    spawner_type = spawner["type"].split(":")[-1]  # 关键修改点
                    weight = spawner["weight"]
                    data[category][biome_name][spawner_type] = weight
                    total_weight += weight
                data[category][biome_name]["Total Weight"] = total_weight

with pd.ExcelWriter("biome_spawner_weights.xlsx") as writer:
    for category in categories:
        df = pd.DataFrame(data[category]).T
        
        # 将索引转换为普通列并命名
        df = df.reset_index().rename(columns={"index": "群系"})
        
        # 调整列顺序：群系 -> Total Weight -> 其他生物
        cols = ["群系", "Total Weight"] + [c for c in df.columns if c not in ("群系", "Total Weight")]
        df = df[cols]
        
        # 写入Excel并冻结首行首列
        df.to_excel(writer, sheet_name=category, index=False)
        worksheet = writer.sheets[category]
        worksheet.freeze_panes(1, 2)  # 冻结首行和前两列

print("Excel文件已生成：biome_spawner_weights.xlsx")
