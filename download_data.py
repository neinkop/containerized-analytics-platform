import urllib.request
import pandas as pd
from pathlib import Path

YEAR_TO_FOLDER = {
    2024: "data_ab_1",
    2025: "data_ab_2",
    2026: "data_ab_3",
}

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

year_input = input("Jahr eingeben (2024 / 2025 / 2026): ").strip()
try:
    year = int(year_input)
except ValueError:
    print("Ungültige Eingabe.")
    exit(1)

if year not in YEAR_TO_FOLDER:
    print(f"Kein Ordner für Jahr {year} konfiguriert.")
    exit(1)

output_dir = Path(YEAR_TO_FOLDER[year])
output_dir.mkdir(exist_ok=True)

for month in range(1, 13):
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    url = f"{BASE_URL}/{filename}"
    parquet_path = output_dir / filename
    csv_path = output_dir / filename.replace(".parquet", ".csv")

    if csv_path.exists():
        print(f"[SKIP] {csv_path.name} bereits vorhanden")
        continue

    print(f"[DOWNLOAD] {url}")
    try:
        urllib.request.urlretrieve(url, parquet_path)
    except Exception as e:
        print(f"[ERROR] Download fehlgeschlagen für {filename}: {e}")
        continue

    print(f"[CONVERT] {parquet_path.name} -> {csv_path.name}")
    try:
        df = pd.read_parquet(parquet_path)
        df.to_csv(csv_path, index=False)
        parquet_path.unlink()
        print(f"[DONE] {csv_path.name} ({len(df):,} Zeilen)")
    except Exception as e:
        print(f"[ERROR] Konvertierung fehlgeschlagen für {filename}: {e}")
        continue

    data_list_path = output_dir / "data.list"
    container_path = f"/app/data/{csv_path.name}"
    existing = data_list_path.read_text() if data_list_path.exists() else ""
    if container_path not in existing:
        with open(data_list_path, "a") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write(container_path + "\n")
        print(f"[LIST] {container_path} in data.list eingetragen")
