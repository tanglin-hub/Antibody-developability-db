
import pandas as pd
from django.core.management.base import BaseCommand
from blog.models import Antibody, AntibodyProperty
from django.db import transaction
import logging

class Command(BaseCommand):
    help = 'Import antibody data from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')

    def handle(self, *args, **kwargs):
        excel_file = kwargs['excel_file']
        logging.basicConfig(
            filename='import_antibody.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.stdout.write("Deleting old antibody data...")
        Antibody.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Old data deleted successfully."))
        logging.info("Old data deleted successfully.")
        
        try:
            df = pd.read_excel(excel_file)
            df.columns = df.columns.str.strip()

            skip_columns = ['id_db', 'date', 'name', 'format', 'other_id', 'organism',
                            'paper', 'reference', 'doi', 'note', 'http']
            skip_columns += [col for col in df.columns if 'sequence' in col.lower()]

            success_count = 0
            fail_count = 0
            skipped_rows = 0
            failed_antibodies = []

            self.stdout.write(f"Excel columns: {df.columns.tolist()}")
            self.stdout.write(f"Total rows: {len(df)}")

            for index, row in df.iterrows():
                name = str(row.get('name')).strip()
                if not name or name.lower() == 'nan':
                    self.stdout.write(f"Skipping row {index} due to missing name.")
                    continue
                self.stdout.write(f"Processing row {index}: {name}")

            with transaction.atomic():
                for index, row in df.iterrows():
                    name = row.get('name')
                    if not name:
                        continue  # 跳过没有名字的抗体

                    try:
                        antibody = Antibody.objects.create(
                            id_db=row.get('id_db'),
                            date=row.get('date') if pd.notna(row.get('date')) else None,
                            name=name,
                            format=row.get('format'),
                            other_id=row.get('other_id'),
                            organism=row.get('organism'),
                            paper=row.get('paper'),
                            reference=row.get('reference'),
                            doi=row.get('doi'),
                            sequence={col.replace(" sequence", "").strip(): row[col] for col in df.columns
                                      if "sequence" in col.lower() and pd.notna(row[col])}
                        )

                        valid_property_found = False

                        for col in df.columns:
                            if col.lower().startswith('assay'):
                                continue
                            if col in skip_columns or pd.isna(row[col]):
                                continue

                            idx = df.columns.get_loc(col)
                            assay = None
                            for offset in [1, 2]:
                                if idx + offset < len(df.columns):
                                    next_col = df.columns[idx + offset]
                                    if 'assay' in next_col.lower():
                                        next_val = row[next_col]
                                        if pd.notna(next_val):
                                            assay = str(next_val)
                                            break

                            AntibodyProperty.objects.create(
                                antibody=antibody,
                                property_name=col.strip(),
                                value=str(row[col]),
                                assay=assay
                            )
                            valid_property_found = True

                        if not valid_property_found:
                            skipped_rows += 1
                            logging.warning(f"Skipping row {index}: No valid properties found")
                            self.stdout.write(self.style.WARNING(f"Skipping row {index}: No valid properties found"))
                        else:
                            success_count += 1
                            logging.info(f"Successfully processed antibody: {name}")
                            self.stdout.write(self.style.SUCCESS(f"Successfully imported antibody: {name}"))

                    except Exception as e:
                        fail_count += 1
                        failed_antibodies.append(name or f"Row {index}")
                        logging.error(f"Failed to import antibody at row {index}: {str(e)}")
                        self.stdout.write(self.style.ERROR(f"Failed to import antibody at row {index}: {str(e)}"))

            # 汇总输出
            self.stdout.write(self.style.SUCCESS("\n=== Import Summary ==="))
            self.stdout.write(f"Successfully imported: {success_count}")
            self.stdout.write(f"Skipped rows (no valid properties): {skipped_rows}")
            self.stdout.write(f"Failed imports: {fail_count}")
            if failed_antibodies:
                self.stdout.write("Failed antibody names or rows:")
                for name in failed_antibodies:
                    self.stdout.write(f" - {name}")

            logging.info("=== Import Summary ===")
            logging.info(f"Successfully imported: {success_count}")
            logging.info(f"Skipped rows: {skipped_rows}")
            logging.info(f"Failed imports: {fail_count}")
            for name in failed_antibodies:
                logging.info(f"Failed antibody: {name}")

        except Exception as e:
            logging.error(f"Fatal error: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Fatal error: {str(e)}"))