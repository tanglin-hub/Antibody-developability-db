import pandas as pd
import json
import os

# ✅ 正确路径（不要加多余的引号）
df = pd.read_excel('C:/Users/34475/Desktop/数据.xlsx')

# 检查列名是否一致
expected_columns = {'Category', 'Name', 'Value'}
if not expected_columns.issubset(df.columns):
    raise ValueError(f"Excel 中应包含列: {expected_columns}")

# 分组生成 JSON
result = []
for category, group in df.groupby('Category'):
    children = group.apply(lambda row: {'name': row['Name'], 'value': row['Value']}, axis=1).tolist()
    result.append({'category': category, 'children': children})

# 输出文件
output_path = 'C:/Users/34475/Desktop/output.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("✅ 转换完成！结果保存在:", os.path.abspath(output_path))
