import json
import pandas as pd
from django.core.management.base import BaseCommand
from blog.models import Antibody
from django.db import transaction
import logging

class Command(BaseCommand):
    help = 'Import antibody data from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')

    def handle(self, *args, **kwargs):
        excel_file = kwargs['excel_file']
        logging.basicConfig(filename='import_antibody.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        try:
             # 清空数据库中的旧数据
            self.stdout.write("Deleting old antibody data...")
            Antibody.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Old data deleted successfully."))
            logging.info("Old data deleted successfully.")
            
            # 读取  antibody_list.antibody_list.antibody_list.antibody_list'CSI-BLI Delta Response (nm)'''ELISA'.an.
            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.strip()
            
            # 遍历 DataFrame 中的每一行，导入抗体数据
            antibody_list = []
            for index, row in df.iterrows():
                try:
                    id_db=row['id_db']
                    date=row['date'] if not pd.isna(row['date']) else None  # 设置为 None 表示空值
                    antibody_name = row['name']
                    if not antibody_name:
                        logging.warning(f"Skipping row {index}: 'name' is missing")
                        continue 
                    reference = row['reference']
                    doi = row['doi']
                    # 解析 sequence 数据（根据列名包含 "sequence" 来识别）
                    sequence = {
                        col.replace(" sequence", ""): row[col]
                        for col in df.columns if "sequence" in col and not pd.isnull(row[col])
                    }



                    # 动态生成 properties
                    properties_columns = [col for col in df.columns if col not in ['name', 'sequence_VH', 'sequence_VL', 'sequence_CH2','sequence_CH3', 'reference', 'doi','number','id_db','http','date','note',]]
                    properties = {col: row[col] for col in properties_columns if not pd.isna(row[col])}
                    property_keys = ", ".join(key.strip() for key in properties.keys())  # 去掉多余空格
                    if not properties:
                        logging.warning(f"Skipping row {index}: No properties found for antibody '{antibody_name}'")
                        continue
            

                    antibody_list.append(
                        Antibody(
                            id_db=id_db,
                            date=date,
                            name=antibody_name,
                            reference=reference,
                            doi=doi,
                            sequence=sequence,
                            properties=properties,
                            property_keys= property_keys,
                        )
                    )
                    logging.info(f"Successfully processed antibody: {antibody_name}")
                
                except Exception as e:
                    logging.error(f"Error processing row {index}: {str(e)}")
            

            # 批量插入数据
            if antibody_list:
                Antibody.objects.bulk_create(antibody_list, ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(f"Imported {len(antibody_list)} antibodies successfully"))
             # 更新 property_keys 字段
            
        except Exception as e:
            logging.critical(f"Critical error: {str(e)}")