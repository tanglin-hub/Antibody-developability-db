import csv
import json
from django.http import HttpResponse
from .models import Antibody

def download_results(query, search_type, antibodies):
    """
    生成 CSV 文件的 HttpResponse。
    
    :param query: 查询的关键词 (Name 或 Property)
    :param search_type: 查询类型 ("name" 或 "property")
    :param antibodies: 查询到的抗体列表
    :return: CSV HttpResponse
    """
    is_property_search = (search_type == "property")  # 是否按抗体性质搜索


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{f"{query}_results.csv"}"'

    writer = csv.writer(response)

    # 获取所有 properties key（仅适用于名称搜索）
    all_property_keys = set()
    for antibody in antibodies:
        all_property_keys.update(antibody.properties.keys())
    # 设置 CSV 头部
    if is_property_search:
        writer.writerow(['ID', 'Name', 'Reference', 'Date', query])  # 只导出查询的属性
    else:
        writer.writerow(['ID', 'Name', 'Reference', 'Date'] + list(all_property_keys))  # 全部属性

    # 遍历抗体数据，写入 CSV
    for antibody in antibodies:
        row = [antibody.id_db, antibody.name, antibody.reference, antibody.date]
        if is_property_search:
            row.append(antibody.properties.get(query, ''))  # 只导出查询的属性
        else:
            row.extend([antibody.properties.get(key, '') for key in all_property_keys])  # 导出所有属性
        
        writer.writerow(row)

    return response