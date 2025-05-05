# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class OverlapsValidator:
    def __init__(self):
        print("[__init__] Initializing OverlapsValidator")
        self.folder_path = ""
        self.status_var = None

    def set_status_var(self, status_var):
        print("[set_status_var] Setting status_var")
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        print("[set_folder_path] Setting folder path to: {}".format(folder_path))
        self.folder_path = folder_path

    def run_validation(self):
        print("[overlaps] Starting overlap validation")

        if not self.folder_path:
            raise ValueError("[overlaps] Folder path not set")

        mdb_files = find_mdb_files(self.folder_path)
        print("[overlaps] Found {} MDB files".format(len(mdb_files)))

        if len(mdb_files) < 2:
            raise ValueError("[overlaps] Need at least 2 MDB files for overlap checking")

        output_csv = os.path.join(self.folder_path, "08_overlap_report.csv")
        valid_fcs = ["Parcel", "Construction", "Segments"]
        feature_files = []

        for mdb in mdb_files:
            try:
                print("[overlaps] Getting feature classes from {}".format(mdb))
                features = get_feature_classes(mdb, valid_fcs)
                count = len(features)
                print("[overlaps] Found {} valid feature classes".format(count))
                feature_files.extend([full_path for fc_name, full_path in features])
            except Exception as e:
                error_msg = "[overlaps] Error processing {}: {}".format(mdb, str(e))
                print(error_msg)
                if self.status_var:
                    self.status_var.set(error_msg)
                raise

        if len(feature_files) < 2:
            raise ValueError("[overlaps] Not enough feature classes found for overlap checking")

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["File1", "File2", "Overlap Count"])

            for i in range(len(feature_files)):
                for j in range(i + 1, len(feature_files)):
                    fc1 = feature_files[i]
                    fc2 = feature_files[j]

                    if os.path.dirname(fc1) == os.path.dirname(fc2):
                        print("[overlaps] Skipping comparison within same MDB")
                        continue

                    intersect_output = "in_memory/intersect_output"

                    try:
                        print("[overlaps] Checking overlap: {} vs {}".format(fc1, fc2))
                        if self.status_var:
                            self.status_var.set("Checking {} vs {}".format(
                                os.path.basename(fc1), os.path.basename(fc2)))

                        arcpy.Intersect_analysis([fc1, fc2], intersect_output)
                        count = int(arcpy.GetCount_management(intersect_output)[0])
                        print("[overlaps] Overlap count: {}".format(count))

                        if count > 0:
                            writer.writerow([fc1, fc2, count])

                    except Exception as e:
                        error_msg = "[overlaps] Error checking {} vs {}: {}".format(fc1, fc2, str(e))
                        print(error_msg)
                        if self.status_var:
                            self.status_var.set(error_msg)
                        raise

                    finally:
                        if arcpy.Exists(intersect_output):
                            arcpy.Delete_management(intersect_output)
                            print("[overlaps] Deleted in-memory intersect output")

        if self.status_var:
            self.status_var.set("Overlap validation completed")
        print("[overlaps] Overlap validation completed")
