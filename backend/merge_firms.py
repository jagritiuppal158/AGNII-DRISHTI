import csv
import glob
from pathlib import Path

def merge_csvs():
    data_dir = Path("data")
    output_path = data_dir / "national_firms.csv"
    
    # Look for csv files in all DL_FIRE_* subdirectories
    csv_files = glob.glob("data/DL_FIRE_*/*.csv")
    
    out_headers = ["latitude", "longitude", "brightness", "confidence", "satellite", "acq_date", "acq_time"]
    
    source_counts = {"MODIS": 0, "VIIRS": 0}
    
    print(f"Found {len(csv_files)} files to merge.")
    
    with output_path.open("w", newline="") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(out_headers)
        
        for file in csv_files:
            with open(file, "r") as in_f:
                reader = csv.DictReader(in_f)
                for row in reader:
                    lat = row["latitude"]
                    lon = row["longitude"]
                    acq_date = row["acq_date"]
                    acq_time = row["acq_time"]
                    
                    # All files in this dataset have uniform headers!
                    brightness = row["brightness"]
                    acq_date = row["acq_date"]
                    acq_time = row["acq_time"]
                    
                    if row["instrument"] == "MODIS":
                        confidence = row["confidence"]
                        satellite = "MODIS"
                        source_counts["MODIS"] += 1
                    else:
                        conf_letter = row["confidence"].lower()
                        if conf_letter == 'l':
                            confidence = 30
                        elif conf_letter == 'n':
                            confidence = 60
                        elif conf_letter == 'h':
                            confidence = 90
                        else:
                            confidence = 50
                        satellite = "VIIRS"
                        source_counts["VIIRS"] += 1
                        
                    writer.writerow([lat, lon, brightness, confidence, satellite, acq_date, acq_time])
                    
    print(f"\nMerged {sum(source_counts.values())} total rows into {output_path}")
    print(f"Row count per source:")
    for src, count in source_counts.items():
        print(f"  {src}: {count}")

if __name__ == "__main__":
    merge_csvs()
