# -*- coding: utf-8 -*-
import os
import arcpy
import csv
import uuid
from utils import find_mdb_files, get_feature_classes


class DuplicateParcelsValidator:
    def __init__(self):
        print("[__init__] Initializing DuplicateParcelsValidator")
        self.folder_path = ""
        self.status_var = None

    def set_status_var(self, status_var):
        print("[set_status_var] Setting status_var")
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        print("[set_folder_path] Setting folder path to: {}".format(folder_path))
        self.folder_path = folder_path

    def run_validation(self):
        print("[duplicate_parcels] Starting duplicate parcel validation")

        if not self.folder_path:
            raise ValueError("[duplicate_parcels] Folder path not set")

        output_csv = os.path.join(self.folder_path, "04_duplicate_parcels_report.csv")
        mdb_files = find_mdb_files(self.folder_path)

        if not mdb_files:
            raise ValueError("[duplicate_parcels] No MDB files found in the specified folder")

        print("[duplicate_parcels] Found {} MDB files".format(len(mdb_files)))

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source File", "WARDNO", "GRIDS1", "PARCELNO", "Frequency"])

            total_mdb = len(mdb_files)

            for index, mdb in enumerate(mdb_files, start=1):
                try:
                    base_name = os.path.basename(mdb)
                    if self.status_var:
                        self.status_var.set("Processing ({}/{}) {}".format(index, total_mdb, base_name))

                    print("[duplicate_parcels] Processing ({}/{}) {}...".format(index, total_mdb, base_name))

                    parcels = get_feature_classes(mdb, ["Parcel"])
                    print("[duplicate_parcels] Found {} Parcel feature classes in {}".format(len(parcels), base_name))

                    for fc_name, full_path in parcels:
                        print("[duplicate_parcels] Checking feature class: {}".format(fc_name))

                        if arcpy.Describe(full_path).shapeType != "Polygon":
                            print("[duplicate_parcels] Skipping non-polygon feature class: {}".format(fc_name))
                            continue

                        frequency_table = "in_memory/freq_" + uuid.uuid4().hex
                        print("[duplicate_parcels] Running Frequency_analysis on: {}".format(fc_name))

                        arcpy.Frequency_analysis(full_path, frequency_table, ["WARDNO", "GRIDS1", "PARCELNO"])

                        with arcpy.da.SearchCursor(frequency_table,
                                                   ["WARDNO", "GRIDS1", "PARCELNO", "FREQUENCY"]) as cursor:
                            for row in cursor:
                                if str(row[2]) != "0" and row[3] > 1:
                                    writer.writerow([full_path, row[0], row[1], row[2], row[3]])

                        if arcpy.Exists(frequency_table):
                            arcpy.Delete_management(frequency_table)
                            print("[duplicate_parcels] Deleted in-memory frequency table")

                except Exception as e:
                    error_message = "[duplicate_parcels] Error processing {}: {}".format(mdb, str(e))
                    if self.status_var:
                        self.status_var.set(error_message)
                    print(error_message)
                    continue

        if self.status_var:
            self.status_var.set("Duplicate parcels validation completed")

        print("[duplicate_parcels] Duplicate parcels validation completed")
