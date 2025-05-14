# -*- coding: utf-8 -*-
import os
import arcpy
import csv
import uuid
from utils import find_mdb_files, get_feature_classes


class DuplicateConstAndSegmentsValidator:
    def __init__(self):
        print("[__init__] Initializing Duplicate Const And Segments Validator")
        self.folder_path = ""
        self.status_var = None

    def set_status_var(self, status_var):
        print("[set_status_var] Setting status_var")
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        print("[set_folder_path] Setting folder path to: {}".format(folder_path))
        self.folder_path = folder_path

    def run_validation(self):
        print("[duplicate_segments_and_const] Starting duplicate const and segments validation")

        if not self.folder_path:
            raise ValueError("[duplicate_segments_and_const] Folder path not set")

        output_csv = os.path.join(self.folder_path, "09_duplicate_segments_construction_report.csv")
        mdb_files = find_mdb_files(self.folder_path)

        if not mdb_files:
            raise ValueError("[duplicate_segments_and_const] No MDB files found in the specified folder")

        print("[duplicate_segments_and_const] Found {} MDB files".format(len(mdb_files)))

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source File", "ParFID","Shape_Area", "Shape_Length", "Frequency"])

            total_mdb = len(mdb_files)

            for index, mdb in enumerate(mdb_files, start=1):
                try:
                    base_name = os.path.basename(mdb)
                    if self.status_var:
                        self.status_var.set("Processing ({}/{}) {}".format(index, total_mdb, base_name))

                    print("[duplicate_segments_and_const] Processing ({}/{}) {}...".format(index, total_mdb, base_name))

                    const = get_feature_classes(mdb, ["Construction"])
                    print("[duplicate_segments_and_const] Found {} Constructions feature classes in {}".format(len(const), base_name))

                    seg = get_feature_classes(mdb, ["Segments"])
                    print("[duplicate_segments_and_const] Found {} Segments feature classes in {}".format(len(seg), base_name))

                    for fc_name, full_path in const:
                        print("[duplicate_segments_and_const] Checking feature class: {}".format(fc_name))

                        if arcpy.Describe(full_path).shapeType != "Polygon":
                            print("[duplicate_segments_and_const] Skipping non-polygon feature class: {}".format(fc_name))
                            continue

                        frequency_table = "in_memory/freq_" + uuid.uuid4().hex
                        print("[duplicate_segments_and_const] Running Frequency_analysis on: {}".format(fc_name))

                        arcpy.Frequency_analysis(full_path, frequency_table, ["ParFID","Shape_Area", "Shape_Length"])

                        with arcpy.da.SearchCursor(frequency_table,
                                                   ["ParFID","Shape_Area", "Shape_Length", "FREQUENCY"]) as cursor:
                            for row in cursor:
                                if str(row[2]) != "0" and row[3] > 1:
                                    writer.writerow([full_path, row[0], row[1], row[2], row[3]])

                        if arcpy.Exists(frequency_table):
                            arcpy.Delete_management(frequency_table)
                            print("[duplicate_segments_and_const] Deleted in-memory frequency table")

                    for fc_name, full_path in seg:
                        print("[duplicate_segments_and_const] Checking feature class: {}".format(fc_name))

                        frequency_table = "in_memory/freq_" + uuid.uuid4().hex
                        print("[duplicate_segments_and_const] Running Frequency_analysis on: {}".format(fc_name))

                        arcpy.Frequency_analysis(full_path, frequency_table, ["ParFID", "Shape_Length"])

                        with arcpy.da.SearchCursor(frequency_table,
                                                   ["ParFID", "Shape_Length", "FREQUENCY"]) as cursor:
                            for row in cursor:
                                if str(row[1]) != "0" and row[2] > 1:
                                    writer.writerow([full_path, row[0], "  ", row[1], row[2]])

                        if arcpy.Exists(frequency_table):
                            arcpy.Delete_management(frequency_table)
                            print("[duplicate_segments_and_const] Deleted in-memory frequency table")

                except Exception as e:
                    error_message = "[duplicate_segments_and_const] Error processing {}: {}".format(mdb, str(e))
                    if self.status_var:
                        self.status_var.set(error_message)
                    print(error_message)
                    continue

        if self.status_var:
            self.status_var.set("Duplicate segments_and_const validation completed")

        print("[duplicate_segments_and_const] Duplicate segments_and_const validation completed")
