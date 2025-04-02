# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class SmallAreasValidator:
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

        output_csv = os.path.join(self.folder_path, "small_areas_report.csv")
        mdb_files = find_mdb_files(self.folder_path)

        if not mdb_files:
            raise ValueError("No MDB files found in the specified folder")

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source File", "Feature Class", "Parcel Number", "ParFID", "Area (sq.m)"])

            for mdb in mdb_files:
                try:
                    if self.status_var:
                        self.status_var.set("Processing {}...".format(os.path.basename(mdb)))

                    # Get Parcel and Construction feature classes
                    features = get_feature_classes(mdb, ["Parcel", "Construction"])

                    for fc_name, full_path in features:
                        if arcpy.Describe(full_path).shapeType != "Polygon":
                            continue

                        fields = [f.name for f in arcpy.ListFields(full_path)]
                        if "Shape_Area" not in fields:
                            continue

                        if fc_name == "Parcel":
                            field_list = ["PARCELNO", "Shape_Area"]
                            min_area = 5
                        else:  # Construction
                            field_list = ["ParFID", "Shape_Area"]
                            min_area = 0.5

                        with arcpy.da.SearchCursor(full_path, field_list) as cursor:
                            for row in cursor:
                                if row[1] < min_area:
                                    if fc_name == "Parcel":
                                        writer.writerow([full_path, fc_name, row[0], "", row[1]])
                                    else:
                                        writer.writerow([full_path, fc_name, "", row[0], row[1]])

                except Exception as e:
                    if self.status_var:
                        self.status_var.set("Error processing {}: {}".format(mdb, str(e)))
                    raise

        if self.status_var:
            self.status_var.set("Small areas validation completed")