# invalid_parcelnum.py
import csv
import os

import arcpy

from utils import find_mdb_files, get_feature_classes


class InvalidParcelNumValidator(object):
    def __init__(self):
        print("[__init__] Initializing InvalidParcelNumberValidator")
        self.folder_path = ""
        self.status_var = None

    def set_folder_path(self, path):
        print("[set_folder_path] Setting folder path to: {}".format(path))
        self.folder_path = path

    def set_status_var(self, var):
        print("[set_status_var] Setting status_var")
        self.status_var = var

    def run_validation(self):
        print("[invalid_parcel_no] Starting Invalid Parcel Number validation")

        if not self.folder_path:
            raise ValueError("[invalid_parcel_no] Folder path not set")

        output_csv = os.path.join(self.folder_path, "07_invalid_parcel_no_report.csv")
        mdb_files = find_mdb_files(self.folder_path)
        valid_parcelno = set(str(i) for i in range(0, 9999))
        if not mdb_files:
            raise ValueError("[invalid_parcel_no] No MDB files found in the specified folder")

        print("[invalid_parcel_no] Found {} MDB files".format(len(mdb_files)))

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Source File", "Parcel Number"])

            for index, mdb in enumerate(mdb_files, start=1):
                try:
                    base_name = os.path.basename(mdb)
                    if self.status_var:
                        self.status_var.set("Processing ({}/{}) {}".format(index, len(mdb_files), base_name))

                    print("[invalid_parcel_no] Processing ({}/{}) {}".format(index, len(mdb_files), base_name))

                    parcels = get_feature_classes(mdb, ["Parcel"])
                    print("[invalid_parcel_no] Found {} Parcel feature classes in {}".format(len(parcels), base_name))

                    for fc_name, full_path in parcels:
                        with arcpy.da.SearchCursor(full_path, ["PARCELNO"]) as cursor:
                            for row in cursor:
                                parcel_no = str(row[0]) if row[0] is not None else ""
                                if parcel_no not in valid_parcelno:
                                    writer.writerow([mdb, row[0]])

                except Exception as e:
                    error_message = "[invalid_parcel_no] Error processing {}: {}".format(mdb, str(e))
                    if self.status_var:
                        self.status_var.set(error_message)
                    print(error_message)
                    raise

        if self.status_var:
            self.status_var.set("Invalid parcel no validation completed")

        print("[invalid_ward] Invalid parcel no validation completed")
