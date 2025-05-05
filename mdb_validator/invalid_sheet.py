# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class InvalidSheetValidator:
    def __init__(self):
        print("[__init__] Initializing InvalidSheetValidator")
        self.folder_path = ""
        self.scale = ""
        self.status_var = None
        self.scale_values = {
            "500": "5554", "600": "5553", "1200": "5555", "1250": "5556",
            "2400": "5557", "2500": "5558", "4800": "5559"
        }

    def set_status_var(self, status_var):
        print("[set_status_var] Setting status_var")
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        print("[set_folder_path] Setting folder path to: {}".format(folder_path))
        self.folder_path = folder_path

    def set_scale(self, scale):
        print("[set_scale] Setting scale to: {}".format(scale))
        self.scale = scale

    def run_validation(self):
        print("[invalid_sheet] Starting validation process")

        if not self.folder_path:
            raise ValueError("[invalid_sheet] Folder path not set")
        if not self.scale:
            raise ValueError("[invalid_sheet] Scale not set")

        scale_value = self.scale_values.get(self.scale)
        if not scale_value:
            raise ValueError("[invalid_sheet] Invalid scale value: {}".format(self.scale))

        output_csv = os.path.join(self.folder_path, "01_invalid_sheet_numbers_report.csv")
        mdb_files = find_mdb_files(self.folder_path)

        if not mdb_files:
            raise ValueError("[invalid_sheet] No MDB files found in the specified folder")

        print("[invalid_sheet] Found {} MDB files".format(len(mdb_files)))

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["MDB File Path", "PARCELNO", "GRIDS1", "Status"])

            for index, mdb in enumerate(mdb_files, start=1):
                try:
                    base_name = os.path.basename(mdb)
                    if self.status_var:
                        self.status_var.set("Processing ({}/{}) {}".format(index, len(mdb_files), base_name))

                    print("[invalid_sheet] Processing ({}/{}) {}".format(index, len(mdb_files), base_name))

                    parcels = get_feature_classes(mdb, ["Parcel"])
                    print("[invalid_sheet] Found {} Parcel feature classes in {}".format(len(parcels), base_name))

                    for fc_name, full_path in parcels:
                        with arcpy.da.SearchCursor(full_path, ["PARCELNO", "GRIDS1"]) as cursor:
                            for row in cursor:
                                grids1 = str(row[1]) if row[1] is not None else ""
                                if not grids1.startswith(scale_value):
                                    writer.writerow([mdb, row[0], grids1,
                                                     "Invalid GRIDS1 (does not match selected scale)"])

                except Exception as e:
                    error_message = "[invalid_sheet] Error processing {}: {}".format(mdb, str(e))
                    if self.status_var:
                        self.status_var.set(error_message)
                    print(error_message)
                    raise

        if self.status_var:
            self.status_var.set("Invalid sheet numbers validation completed")

        print("[invalid_sheet] Invalid sheet numbers validation completed")
