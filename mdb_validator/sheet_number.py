# -*- coding: utf-8 -*-
import os
import arcpy
import csv
from utils import find_mdb_files
import sys
import subprocess

pathlib_available = True
try:
    from pathlib import Path
except ImportError:
    print("[init] pathlib not found. Trying to install...")
    try:
        subprocess.call(["python", "-m", "pip", "install", "pathlib"])
        from pathlib import Path
    except ImportError:
        pathlib_available = False
        print("[init] Failed to install pathlib. Disabling pathlib support.")

class SheetNumberValidator:
    def __init__(self):
        print("[__init__] Initializing SheetNumberValidator")
        self.folder_path = ""
        self.gridsheet = ""
        self.status_var = None

    def set_status_var(self, status_var):
        print("[set_status_var] Setting status_var")
        self.status_var = status_var

    def set_folder_path(self, folder_path):
        print("[set_folder_path] Setting folder path to: {}".format(folder_path))
        self.folder_path = folder_path

    def set_gridsheet(self, gridsheet):
        print("[set_gridsheet] Setting gridsheet to: {}".format(gridsheet))
        self.gridsheet = gridsheet

    def run_validation(self):
        print("[sheet_number] Starting sheet number validation")

        if not self.folder_path:
            raise ValueError("[sheet_number] Folder path not set")
        if not self.gridsheet:
            raise ValueError("[sheet_number] Gridsheet not set")

        if pathlib_available:
            if getattr(sys, 'frozen', False):
                base_path = Path(sys.executable).parent
            else:
                base_path = Path(__file__).parent
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        gridsheet_path = os.path.join(base_path, "templates", self.gridsheet)
        print("[sheet_number] Using gridsheet at: {}".format(gridsheet_path))

        if not arcpy.Exists(gridsheet_path):
            raise ValueError("[sheet_number] Gridsheet not found at: {}".format(gridsheet_path))

        output_dir = os.path.join(self.folder_path, "SheetNumberReports")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print("[sheet_number] Created output directory: {}".format(output_dir))

        mdb_files = find_mdb_files(self.folder_path)
        print("[sheet_number] Found {} MDB files".format(len(mdb_files)))

        for mdb in mdb_files:
            parcel_path = os.path.join(mdb, "Parcel")
            if not arcpy.Exists(parcel_path):
                print("[sheet_number] Parcel not found in {}".format(mdb))
                continue

            try:
                mdb_name = os.path.basename(mdb)
                if self.status_var:
                    self.status_var.set("Processing {}...".format(mdb_name))
                print("[sheet_number] Processing {}".format(mdb_name))

                intersect_shp = os.path.join(output_dir, "Intersect.shp")
                if arcpy.Exists(intersect_shp):
                    arcpy.Delete_management(intersect_shp)
                    print("[sheet_number] Deleted previous intersect shapefile")

                arcpy.Intersect_analysis([gridsheet_path, parcel_path], intersect_shp, "ALL")
                print("[sheet_number] Created intersection shapefile")

                fields = [f.name for f in arcpy.ListFields(intersect_shp)]
                if "PageNumber" not in fields:
                    msg = "[sheet_number] PageNumber field missing in {}".format(intersect_shp)
                    print(msg)
                    if self.status_var:
                        self.status_var.set(msg)
                    continue

                mismatch_csv = os.path.join(output_dir, "Mismatch_{}.csv".format(mdb_name))
                with open(mismatch_csv, 'wb') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Source", "WARDNO", "FID_Parcel", "PARCELNO", "PageNumber", "GRIDS1"])

                    with arcpy.da.SearchCursor(intersect_shp,
                                               ["PageNumber", "GRIDS1", "WARDNO", "FID_Parcel", "PARCELNO"]) as cursor:
                        mismatch_count = 0
                        for row in cursor:
                            if str(row[0]) != str(row[1]):
                                writer.writerow([parcel_path, row[2], row[3], row[4], row[0], row[1]])
                                mismatch_count += 1
                        print("[sheet_number] Found {} mismatches in {}".format(mismatch_count, mdb_name))

            except Exception as e:
                error_msg = "[sheet_number] Error processing {}: {}".format(mdb, str(e))
                print(error_msg)
                if self.status_var:
                    self.status_var.set(error_msg)
                raise

        if self.status_var:
            self.status_var.set("Sheet number validation completed")
        print("[sheet_number] Sheet number validation completed")
