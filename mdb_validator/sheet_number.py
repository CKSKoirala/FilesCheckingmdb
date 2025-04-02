# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files


class SheetNumberValidator:
    def __init__(self):
        self.folder_path = ""
        self.gridsheet = ""
        self.status_var = None

    def set_status_var(self, status_var):
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        self.folder_path = folder_path

    def set_gridsheet(self, gridsheet):
        self.gridsheet = gridsheet

    def run_validation(self):
        if not self.folder_path:
            raise ValueError("Folder path not set")
        if not self.gridsheet:
            raise ValueError("Gridsheet not set")

        gridsheet_path = os.path.join("D:\\check_clean\\FilesCheckingmdb\\templates", self.gridsheet)
        if not arcpy.Exists(gridsheet_path):
            raise ValueError("Gridsheet not found at: {}".format(gridsheet_path))

        output_dir = os.path.join(self.folder_path, "SheetNumberReports")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        mdb_files = find_mdb_files(self.folder_path)

        for mdb in mdb_files:
            parcel_path = os.path.join(mdb, "Parcel")
            if not arcpy.Exists(parcel_path):
                continue

            try:
                if self.status_var:
                    self.status_var.set("Processing {}...".format(os.path.basename(mdb)))

                # Create intersection
                intersect_shp = os.path.join(output_dir, "Intersect.shp")
                if arcpy.Exists(intersect_shp):
                    arcpy.Delete_management(intersect_shp)

                arcpy.Intersect_analysis([gridsheet_path, parcel_path], intersect_shp, "ALL")

                # Check for PageNumber field
                fields = [f.name for f in arcpy.ListFields(intersect_shp)]
                if "PageNumber" not in fields:
                    if self.status_var:
                        self.status_var.set("PageNumber field missing in {}".format(intersect_shp))
                    continue

                # Create mismatch report
                mismatch_csv = os.path.join(output_dir, "Mismatch_{}.csv".format(os.path.basename(mdb)))
                with open(mismatch_csv, 'wb') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Source", "WARDNO", "FID_Parcel", "PARCELNO", "PageNumber", "GRIDS1"])

                    with arcpy.da.SearchCursor(intersect_shp,
                                               ["PageNumber", "GRIDS1", "WARDNO", "FID_Parcel", "PARCELNO"]) as cursor:
                        for row in cursor:
                            if str(row[0]) != str(row[1]):
                                writer.writerow([parcel_path, row[2], row[3], row[4], row[0], row[1]])

            except Exception as e:
                if self.status_var:
                    self.status_var.set("Error processing {}: {}".format(mdb, str(e)))
                raise

        if self.status_var:
            self.status_var.set("Sheet number validation completed")