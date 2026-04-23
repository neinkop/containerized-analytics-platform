print("Starting script...")
import pandas as pd # type: ignore
import pyarrow.parquet as pq # type: ignore
print("Starting Lib import")

# Pfade anpassen
path = "../data_ab_1/"

print(f"Suche nach Parquet-Dateien im Ordner: {path}")

import os

# Output-Ordner
output_dir = os.path.join(path, "csv")
os.makedirs(output_dir, exist_ok=True)

# Alle Dateien im Ordner durchgehen
for file in os.listdir(path):
    if file.endswith("12.parquet"):
        input_file = os.path.join(path, file)
        output_file = os.path.join(output_dir, file.replace(".parquet", ".csv"))

        print(f"\nVerarbeite: {input_file}")

        parquet_file = pq.ParquetFile(input_file)

        first = True
        row_count = 0

        for batch in parquet_file.iter_batches(batch_size=100_000):
            df = batch.to_pandas()
            row_count += len(df)

            print(f"  Batch verarbeitet... {row_count} Zeilen")

            df.to_csv(
                output_file,
                mode='w' if first else 'a',
                index=False,
                header=first
            )

            first = False

        print(f"Fertig: {output_file} ({row_count} Zeilen)")