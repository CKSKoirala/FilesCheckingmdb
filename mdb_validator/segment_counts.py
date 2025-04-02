# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class SegmentCountsValidator:
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

        output_csv = os.path.join(self.folder_path, "segment_counts_report.csv")
        mdb_files = find_mdb_files(self.folder_path)

        if not mdb_files:
            raise ValueError("No MDB files found in the specified folder")

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source File", "Feature Class", "Segments Count"])

            for mdb in mdb_files:
                try:
                    if self.status_var:
                        self.status_var.set("Processing {}...".format(os.path.basename(mdb)))

                    segments = get_feature_classes(mdb, ["Segments"])

                    for fc_name, full_path in segments:
                        if arcpy.Describe(full_path).shapeType == "Polyline":
                            count = int(arcpy.GetCount_management(full_path)[0])
                            writer.writerow([full_path, fc_name, count])

                except Exception as e:
                    if self.status_var:
                        self.status_var.set("Error processing {}: {}".format(mdb, str(e)))
                    raise

        if self.status_var:
            self.status_var.set("Segment counts validation completed")