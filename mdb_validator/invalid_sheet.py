# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class InvalidSheetValidator:
    def __init__(self):
        self.folder_path = ""
        self.scale = ""
        self.status_var = None
        self.scale_values = {
            "500": "5554", "600": "5553", "1200": "5555", "1250": "5556",
            "2400": "5557", "2500": "5558", "4800": "5559"
        }

    def set_status_var(self, status_var):
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        self.folder_path = folder_path

    def set_scale(self, scale):
        self.scale = scale

    def run_validation(self):
        if not self.folder_path:
            raise ValueError("Folder path not set")
        if not self.scale:
            raise ValueError("Scale not set")

        scale_value = self.scale_values.get(self.scale)
        if not scale_value:
            raise ValueError("Invalid scale value")

        output_csv = os.path.join(self.folder_path, "invalid_sheet_numbers_report.csv")
        mdb_files = find_mdb_files(self.folder_path)

        if not mdb_files:
            raise ValueError("No MDB files found in the specified folder")

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["MDB File Path", "PARCELNO", "GRIDS1", "Status"])

            for mdb in mdb_files:
                try:
                    if self.status_var:
                        self.status_var.set("Processing {}...".format(os.path.basename(mdb)))

                    parcels = get_feature_classes(mdb, ["Parcel"])

                    for fc_name, full_path in parcels:
                        with arcpy.da.SearchCursor(full_path, ["PARCELNO", "GRIDS1"]) as cursor:
                            for row in cursor:
                                grids1 = str(row[1]) if row[1] is not None else ""
                                if not grids1.startswith(scale_value):
                                    writer.writerow([mdb, row[0], grids1,
                                                     "Invalid GRIDS1 (does not match selected scale)"])

                except Exception as e:
                    if self.status_var:
                        self.status_var.set("Error processing {}: {}".format(mdb, str(e)))
                    raise

        if self.status_var:
            self.status_var.set("Invalid sheet numbers validation completed")