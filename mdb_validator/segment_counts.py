# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class SegmentCountsValidator:
    def __init__(self):
        print("[__init__] Initializing SegmentCountsValidator")
        self.folder_path = ""
        self.status_var = None

    def set_status_var(self, status_var):
        print("[set_status_var] Setting status_var")
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        print("[set_folder_path] Setting folder path to: {}".format(folder_path))
        self.folder_path = folder_path

    def run_validation(self):
        print("[segments_count] Starting segment counts validation")

        if not self.folder_path:
            raise ValueError("[segments_count] Folder path not set")

        output_csv = os.path.join(self.folder_path, "06_segment_counts_report.csv")
        mdb_files = find_mdb_files(self.folder_path)
        print("[segments_count] Found {} MDB files".format(len(mdb_files)))

        if not mdb_files:
            raise ValueError("[segments_count] No MDB files found in the specified folder")

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source File", "Feature Class", "Segments Count"])

            for index, mdb in enumerate(mdb_files, start=1):
                try:
                    base_name = os.path.basename(mdb)
                    if self.status_var:
                        self.status_var.set("[segments_count] Processing ({}/{}) {}".format(index, len(mdb_files), base_name))

                    print("[segments_count] Processing ({}/{}) {}".format(index, len(mdb_files), base_name))
                    segments = get_feature_classes(mdb, ["Segments"])
                    print("[segments_count] Found {} 'Segments' feature classes".format(len(segments)))

                    for fc_name, full_path in segments:
                        shape_type = arcpy.Describe(full_path).shapeType
                        if shape_type == "Polyline":
                            count = int(arcpy.GetCount_management(full_path)[0])
                            print("[segments_count] {} has {} segments".format(fc_name, count))
                            writer.writerow([full_path, fc_name, count])
                        else:
                            print("[segments_count] Skipping {} (not Polyline)".format(fc_name))

                except Exception as e:
                    error_msg = "[segments_count] Error processing {}: {}".format(mdb, str(e))
                    print(error_msg)
                    if self.status_var:
                        self.status_var.set(error_msg)
                    raise

        if self.status_var:
            self.status_var.set("Segment counts validation completed")
        print("[segments_count] Segment counts validation completed")
