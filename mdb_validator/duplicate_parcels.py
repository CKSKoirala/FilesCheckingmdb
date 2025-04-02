# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class DuplicateParcelsValidator:
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

        output_csv = os.path.join(self.folder_path, "duplicate_parcels_report.csv")
        mdb_files = find_mdb_files(self.folder_path)

        if not mdb_files:
            raise ValueError("No MDB files found in the specified folder")

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source File", "Parcel Number", "Frequency"])

            for mdb in mdb_files:
                try:
                    if self.status_var:
                        self.status_var.set("Processing {}...".format(os.path.basename(mdb)))

                    # Get all Parcel feature classes in this MDB
                    parcels = get_feature_classes(mdb, ["Parcel"])

                    for fc_name, full_path in parcels:
                        if arcpy.Describe(full_path).shapeType != "Polygon":
                            continue

                        frequency_table = "in_memory/frequency_table"
                        arcpy.Frequency_analysis(full_path, frequency_table, ["PARCELNO"])

                        with arcpy.da.SearchCursor(frequency_table, ["PARCELNO", "FREQUENCY"]) as cursor:
                            for row in cursor:
                                if row[0] != 0 and row[1] > 1:  # Skip parcel number 0
                                    writer.writerow([full_path, row[0], row[1]])

                        if arcpy.Exists(frequency_table):
                            arcpy.Delete_management(frequency_table)

                except Exception as e:
                    if self.status_var:
                        self.status_var.set("Error processing {}: {}".format(mdb, str(e)))
                    raise

        if self.status_var:
            self.status_var.set("Duplicate parcels validation completed")