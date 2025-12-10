import os
import json
import pandas as pd
from collections import defaultdict

output_count = True  # 是否显示成组生成数量范围
output_zero_total_weight = True  # 是否显示没有任何刻生成生物的生物类别和生物群系

categories = ["monster", "creature", "ambient", "water_ambient",
              "water_creature", "underground_water_creature", "axolotls", "misc"]

# 改为：每个 category → biome → spawner_type → list of display strings
data = {category: defaultdict(lambda: defaultdict(list)) for category in categories}

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
                spawner_entries = spawners.get(category, [])
                # 遍历每个 spawner 实例（可能同 type 多次出现）
                for spawner in spawner_entries:
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

                    # 关键改动：追加到列表而非覆盖
                    data[category][biome_name][spawner_type].append(display_value)
                    total_weight += weight

                # 合并同一 spawner_type 的多个条目，用 "; " 连接
                for spawner_type in list(data[category][biome_name].keys()):
                    entries = data[category][biome_name][spawner_type]
                    data[category][biome_name][spawner_type] = "; ".join(entries)

                # 总权重保持纯数字（仍按所有条目累加）
                if output_zero_total_weight or total_weight > 0:
                    data[category][biome_name]["总权重"] = total_weight

# 构建 DataFrame：每个 category 一张表
with pd.ExcelWriter("biome.xlsx") as writer:
    for category in categories:
        raw_dict = data[category]
        if not raw_dict:
            continue
        df = pd.DataFrame(raw_dict).T
        df = df.dropna(how='all', axis=0)
        if df.empty:
            continue
        df = df.reset_index().rename(columns={"index": "群系"})
        # 确保“群系”和“总权重”在前两列；其余按字母 or 出现顺序排（pandas 默认是按 key 插入顺序，Python 3.7+ 有序）
        cols = ["群系", "总权重"] + [c for c in df.columns if c not in ("群系", "总权重")]
        df = df[cols]
        df.to_excel(writer, sheet_name=category, index=False)

        worksheet = writer.sheets[category]
        for col_num, col_name in enumerate(df.columns):
            if col_name == "群系" or col_name == "总权重":
                worksheet.set_column(col_num, col_num, 20)
            else:
                worksheet.set_column(col_num, col_num, 15)  # 稍宽，适应分号拼接
        worksheet.freeze_panes(1, 2)

print("Excel文件已生成：biome.xlsx")