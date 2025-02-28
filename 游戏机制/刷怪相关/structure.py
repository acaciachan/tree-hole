import os
import json
import pandas as pd
from collections import defaultdict

# 定义需要解析的实体类别（根据结构文件中的实际字段调整）
categories = ["monster", "creature", "ambient", "water_ambient",
              "water_creature", "underground_water_creature", "axolotls", "misc"]

# 初始化数据结构：category -> 结构名称 -> 生物 -> 权重
data = {category: defaultdict(dict) for category in categories}

# 遍历结构文件夹
folder_path = "./structure"  # 结构文件存放目录
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r') as f:
            struct_data = json.load(f)
            
            # 获取结构名称（去掉命名空间）
            struct_name = struct_data["type"].split(":")[-1]
            
            # 解析生成数据
            spawn_overrides = struct_data.get("spawn_overrides", {})
            
            for category in categories:
                total_weight = 0
                spawns = spawn_overrides.get(category, {}).get("spawns", [])
                
                for spawn in spawns:
                    # 清理生物名称并记录权重
                    mob_type = spawn["type"].split(":")[-1]
                    weight = spawn["weight"]
                    data[category][struct_name][mob_type] = weight
                    total_weight += weight
                
                # 记录总权重（即使为0）
                data[category][struct_name]["Total Weight"] = total_weight

# 生成Excel文件
with pd.ExcelWriter("structure_spawn_weights.xlsx") as writer:
    for category in categories:
        df = pd.DataFrame(data[category]).T.reset_index()
        df = df.rename(columns={"index": "结构名称"})
        
        # 调整列顺序：结构名称 -> Total Weight -> 其他生物
        cols = ["结构名称", "Total Weight"] + [c for c in df.columns if c not in ("结构名称", "Total Weight")]
        df = df[cols]
        
        # 写入并设置冻结
        df.to_excel(writer, sheet_name=category, index=False)
        worksheet = writer.sheets[category]
        worksheet.freeze_panes(1, 2)  # 冻结首行和前两列

print("结构生成权重文件已生成：structure_spawn_weights.xlsx")
