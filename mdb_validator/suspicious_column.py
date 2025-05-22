# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class SuspiciousColumnValidator:
    def __init__(self):
        print("[__init__] Initializing SuspiciousColumnValidator")
        self.folder_path = ""
        self.status_var = None

    def set_status_var(self, status_var):
        print("[set_status_var] Setting status_var")
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        print("[set_status_var] Setting folder path to: {}".format(folder_path))
        self.folder_path = folder_path

    def run_validation(self):
        print("[SuspiciousColumnValidator] Starting validation process")

        if not self.folder_path:
            raise ValueError("[SuspiciousColumnValidator] Folder path not set")

        output_csv = os.path.join(self.folder_path, "10_suspicious_column_report.csv")
        mdb_files = find_mdb_files(self.folder_path)

        if not mdb_files:
            raise ValueError("[SuspiciousColumnValidator] No MDB files found in the specified folder")

        print("[SuspiciousColumnValidator] Found {} MDB files".format(len(mdb_files)))

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            # Updated header to include status type
            writer.writerow(["Source File", "Parcel Number", "Status", "Value"])

            for index, mdb in enumerate(mdb_files, start=1):
                try:
                    base_name = os.path.basename(mdb)
                    if self.status_var:
                        self.status_var.set("Processing ({}/{}) {}".format(index, len(mdb_files), base_name))

                    print("[SuspiciousColumnValidator] Processing ({}/{}) {}".format(index, len(mdb_files), base_name))

                    parcels = get_feature_classes(mdb, ["Parcel"])
                    print("[SuspiciousColumnValidator] Found {} Parcel feature classes in {}".format(len(parcels), base_name))

                    for fc_name, full_path in parcels:
                        # Check if suspicious column exists
                        field_names = [f.name for f in arcpy.ListFields(full_path)]
                        if "suspicious" not in field_names:
                            writer.writerow([mdb, "N/A", "Column missing", "suspicious column not found"])
                            continue

                        # If column exists, check for yes/YES values
                        with arcpy.da.SearchCursor(full_path, ["PARCELNO", "suspicious"]) as cursor:
                            for row in cursor:
                                parcel_no = row[0]
                                suspicious_val = str(row[1]).strip().upper() if row[1] is not None else ""
                                if suspicious_val in ["YES", "Y"]:
                                    writer.writerow([mdb, parcel_no, "Flagged as suspicious", row[1]])

                except Exception as e:
                    error_message = "[SuspiciousColumnValidator] Error processing {}: {}".format(mdb, str(e))
                    if self.status_var:
                        self.status_var.set(error_message)
                    print(error_message)
                    # Continue with next file instead of raising exception
                    writer.writerow([mdb, "ERROR", "Processing error", str(e)])
                    continue

        if self.status_var:
            self.status_var.set("Suspicious column validation completed")

        print("[SuspiciousColumnValidator] Suspicious column validation completed")