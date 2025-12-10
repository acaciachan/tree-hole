import os
import json
import pandas as pd
from collections import defaultdict

output_count = True  # 是否显示成组生成数量范围
output_zero_total_weight = False  # 是否显示没有任何刻生成生物的生物类别和生物群系

categories = ["monster", "creature", "ambient", "water_ambient",
              "water_creature", "underground_water_creature", "axolotls", "misc"]

# 关键改动：改为 list 存储，支持重复生物
data = {category: defaultdict(lambda: defaultdict(list)) for category in categories}

folder_path = "./structure"
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            spawn_overrides = json_data.get("spawn_overrides", {})
            structure_name = filename.split('.')[0]

            for category in categories:
                total_weight = 0
                spawn_info = spawn_overrides.get(category, {})
                for spawner in spawn_info.get("spawns", []):
                    spawner_type = spawner["type"].split(":")[-1]
                    weight = spawner["weight"]
                    min_count = spawner["minCount"]
                    max_count = spawner["maxCount"]

                    count_str = f"{min_count}-{max_count}" if min_count != max_count else str(min_count)
                    if weight < 10:
                        weight_value = f"  {weight}"
                    elif 10 <= weight < 100:
                        weight_value = f" {weight}"
                    else:
                        weight_value = f"{weight}"

                    if output_count:
                        display_value = f"{weight_value} {count_str}"
                    else:
                        display_value = f"{weight_value}"

                    # ✅ 关键：追加到列表（不再覆盖）
                    data[category][structure_name][spawner_type].append(display_value)
                    total_weight += weight

                # ✅ 合并同一生物的多个条目
                for spawner_type in list(data[category][structure_name].keys()):
                    entries = data[category][structure_name][spawner_type]
                    data[category][structure_name][spawner_type] = "; ".join(entries)

                # 总权重保持数字（按所有条目累加）
                if output_zero_total_weight or total_weight > 0:
                    data[category][structure_name]["总权重"] = total_weight

# 写入 Excel
with pd.ExcelWriter("structure.xlsx") as writer:
    for category in categories:
        df = pd.DataFrame(data[category]).T
        df = df.dropna(how='all', axis=0)
        if df.empty:
            continue
        df = df.reset_index().rename(columns={"index": "结构"})
        cols = ["结构", "总权重"] + [c for c in df.columns if c not in ("结构", "总权重")]
        df = df[cols]
        df.to_excel(writer, sheet_name=category, index=False)

        worksheet = writer.sheets[category]
        for col_num, col_name in enumerate(df.columns):
            if col_name == "结构" or col_name == "总权重":
                worksheet.set_column(col_num, col_num, 20)
            else:
                worksheet.set_column(col_num, col_num, 15)  # 稍宽，适配分号内容
        worksheet.freeze_panes(1, 2)

print("Excel文件已生成：structure.xlsx")