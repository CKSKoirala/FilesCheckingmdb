# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class OverlapsValidator:
    def __init__(self):
        self.folder_path = ""
        self.status_var = None

    def set_status_var(self, status_var):
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        self.folder_path = folder_path

    def run_validation(self):
        if not self.folder_path:
            raise ValueError("Folder path not set")

        mdb_files = find_mdb_files(self.folder_path)

        if len(mdb_files) < 2:
            raise ValueError("Need at least 2 MDB files for overlap checking")

        output_csv = os.path.join(self.folder_path, "overlap_report.csv")
        valid_fcs = ["Parcel", "Construction", "Segments"]
        feature_files = []

        # Collect all feature classes
        for mdb in mdb_files:
            try:
                features = get_feature_classes(mdb, valid_fcs)
                feature_files.extend([full_path for fc_name, full_path in features])
            except Exception as e:
                if self.status_var:
                    self.status_var.set("Error processing {}: {}".format(mdb, str(e)))
                raise

        if len(feature_files) < 2:
            raise ValueError("Not enough feature classes found for overlap checking")

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["File1", "File2", "Overlap Count"])

            # Compare each feature class with every other
            for i in range(len(feature_files)):
                for j in range(i + 1, len(feature_files)):
                    fc1 = feature_files[i]
                    fc2 = feature_files[j]

                    # Skip if both from same MDB
                    if os.path.dirname(fc1) == os.path.dirname(fc2):
                        continue

                    intersect_output = "in_memory/intersect_output"

                    try:
                        if self.status_var:
                            self.status_var.set("Checking {} vs {}".format(
                                os.path.basename(fc1), os.path.basename(fc2)))

                        arcpy.Intersect_analysis([fc1, fc2], intersect_output)
                        count = int(arcpy.GetCount_management(intersect_output)[0])

                        if count > 0:
                            writer.writerow([fc1, fc2, count])

                    except Exception as e:
                        if self.status_var:
                            self.status_var.set("Error checking {} vs {}: {}".format(
                                fc1, fc2, str(e)))
                        raise

                    finally:
                        if arcpy.Exists(intersect_output):
                            arcpy.Delete_management(intersect_output)

        if self.status_var:
            self.status_var.set("Overlap validation completed")