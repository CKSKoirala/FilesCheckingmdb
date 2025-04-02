# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class InvalidWardValidator:
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

        output_csv = os.path.join(self.folder_path, "invalid_ward_numbers_report.csv")
        mdb_files = find_mdb_files(self.folder_path)
        valid_wards = set(str(i) for i in range(1, 10))

        if not mdb_files:
            raise ValueError("No MDB files found in the specified folder")

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source File", "Parcel Number", "WARDNO"])

            for mdb in mdb_files:
                try:
                    if self.status_var:
                        self.status_var.set("Processing {}...".format(os.path.basename(mdb)))

                    parcels = get_feature_classes(mdb, ["Parcel"])

                    for fc_name, full_path in parcels:
                        with arcpy.da.SearchCursor(full_path, ["PARCELNO", "WARDNO"]) as cursor:
                            for row in cursor:
                                ward_no = str(row[1]) if row[1] is not None else ""
                                if ward_no not in valid_wards:
                                    writer.writerow([mdb, row[0], row[1]])

                except Exception as e:
                    if self.status_var:
                        self.status_var.set("Error processing {}: {}".format(mdb, str(e)))
                    raise

        if self.status_var:
            self.status_var.set("Invalid ward numbers validation completed")