import re
import csv

# 读取文件内容
with open('SpawnPlacements.txt', 'r') as file:
    content = file.read()

# 使用正则表达式匹配所需内容
pattern = r'register\(EntityType\.(\w+),\s*SpawnPlacementTypes\.(\w+),\s*Heightmap\.Types\.(\w+),\s*(\w+)::(\w+)\);'
matches = re.findall(pattern, content)

# 创建CSV文件并写入数据
with open('SpawnPlacements.csv', 'w', newline='') as csvfile:
    fieldnames = ['EntityType', 'SpawnPlacementTypes', 'Heightmap.Types', 'SpawnRules类名', 'SpawnRules方法名']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for match in matches:
        writer.writerow({
            'EntityType': match[0],
            'SpawnPlacementTypes': match[1],
            'Heightmap.Types': match[2],
            'SpawnRules类名': match[3],
            'SpawnRules方法名': match[4]
        })

print("数据已成功导出到SpawnPlacements.csv文件中")