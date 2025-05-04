# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files, get_feature_classes


class SmallAreasValidator:
    def __init__(self):
        print("[__init__] Initializing SmallAreasValidator")
        self.folder_path = ""
        self.status_var = None

    def set_status_var(self, status_var):
        print("[set_status_var] Setting status_var")
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        print("[set_folder_path] Setting folder path to: {}".format(folder_path))
        self.folder_path = folder_path

    def run_validation(self):
        print("[small_areas] Starting small areas validation")
        if not self.folder_path:
            raise ValueError("[small_areas] Folder path not set")

        output_csv = os.path.join(self.folder_path, "small_areas_report.csv")
        mdb_files = find_mdb_files(self.folder_path)
        print("[small_areas] Found {} MDB files".format(len(mdb_files)))

        if not mdb_files:
            raise ValueError("[small_areas] No MDB files found in the specified folder")

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source File", "Feature Class", "Parcel Number", "ParFID", "Area (sq.m)"])

            for mdb in mdb_files:
                try:
                    mdb_name = os.path.basename(mdb)
                    if self.status_var:
                        self.status_var.set("Processing {}...".format(mdb_name))
                    print("[small_areas] Processing {}".format(mdb_name))

                    features = get_feature_classes(mdb, ["Parcel", "Construction"])
                    print("[small_areas] Found {} relevant feature classes in {}".format(len(features), mdb_name))

                    for fc_name, full_path in features:
                        shape_type = arcpy.Describe(full_path).shapeType
                        if shape_type != "Polygon":
                            print("[small_areas] Skipping non-polygon feature class: {}".format(fc_name))
                            continue

                        fields = [f.name for f in arcpy.ListFields(full_path)]
                        if "Shape_Area" not in fields:
                            print("[small_areas] Shape_Area field missing in: {}".format(fc_name))
                            continue

                        if fc_name == "Parcel":
                            field_list = ["PARCELNO", "Shape_Area"]
                            min_area = 5
                        else:  # Construction
                            field_list = ["ParFID", "Shape_Area"]
                            min_area = 0.5

                        small_count = 0
                        with arcpy.da.SearchCursor(full_path, field_list) as cursor:
                            for row in cursor:
                                if row[1] < min_area:
                                    small_count += 1
                                    if fc_name == "Parcel":
                                        writer.writerow([full_path, fc_name, row[0], "", row[1]])
                                    else:
                                        writer.writerow([full_path, fc_name, "", row[0], row[1]])
                        print("[small_areas] {} small features in {} ({})".format(small_count, fc_name, mdb_name))

                except Exception as e:
                    error_msg = "[small_areas] Error processing {}: {}".format(mdb, str(e))
                    print(error_msg)
                    if self.status_var:
                        self.status_var.set(error_msg)
                    raise

        if self.status_var:
            self.status_var.set("Small areas validation completed")
        print("[small_areas] Small areas validation completed")
