# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class InvalidWardValidator:
    def __init__(self):
        print("[__init__] Initializing InvalidWardValidator")
        self.folder_path = ""
        self.status_var = None

    def set_status_var(self, status_var):
        print("[set_status_var] Setting status_var")
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        print("[set_folder_path] Setting folder path to: {}".format(folder_path))
        self.folder_path = folder_path

    def run_validation(self):
        print("[run_validation] Starting validation process")

        if not self.folder_path:
            raise ValueError("[run_validation] Folder path not set")

        output_csv = os.path.join(self.folder_path, "invalid_ward_numbers_report.csv")
        mdb_files = find_mdb_files(self.folder_path)
        valid_wards = set(str(i) for i in range(1, 10))

        if not mdb_files:
            raise ValueError("[run_validation] No MDB files found in the specified folder")

        print("[run_validation] Found {} MDB files".format(len(mdb_files)))

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source File", "Parcel Number", "WARDNO"])

            for index, mdb in enumerate(mdb_files, start=1):
                try:
                    base_name = os.path.basename(mdb)
                    if self.status_var:
                        self.status_var.set("Processing ({}/{}) {}".format(index, len(mdb_files), base_name))

                    print("[run_validation] Processing ({}/{}) {}".format(index, len(mdb_files), base_name))

                    parcels = get_feature_classes(mdb, ["Parcel"])
                    print("[run_validation] Found {} Parcel feature classes in {}".format(len(parcels), base_name))

                    for fc_name, full_path in parcels:
                        with arcpy.da.SearchCursor(full_path, ["PARCELNO", "WARDNO"]) as cursor:
                            for row in cursor:
                                ward_no = str(row[1]) if row[1] is not None else ""
                                if ward_no not in valid_wards:
                                    writer.writerow([mdb, row[0], row[1]])

                except Exception as e:
                    error_message = "[run_validation] Error processing {}: {}".format(mdb, str(e))
                    if self.status_var:
                        self.status_var.set(error_message)
                    print(error_message)
                    raise

        if self.status_var:
            self.status_var.set("Invalid ward numbers validation completed")

        print("[run_validation] Invalid ward numbers validation completed")
