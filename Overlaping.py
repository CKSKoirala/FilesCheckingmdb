# -*- coding: utf-8 -*-
import arcpy
import os
import csv
import Tkinter as tk
import tkFileDialog

# Tkinter GUI to select a folder
root = tk.Tk()
root.withdraw()  # Hide main window

folder_path = tkFileDialog.askdirectory(title="Select Folder Containing .mdb Files")

if not folder_path:
    print("⚠️ No folder selected. Exiting...")
    exit()

# Find all .mdb files in the selected folder
mdb_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".mdb")]

if len(mdb_files) < 2:
    print("⚠️ Need at least two .mdb files for overlap checking. Found:", len(mdb_files))
    exit()

# Automatically save the CSV in the selected folder
output_csv = os.path.join(folder_path, "Overlapping_Report.csv")

valid_feature_classes = ["Parcel", "Construction", "Segments"]
parcel_files = []

# Extract feature classes
for mdb in mdb_files:
    arcpy.env.workspace = mdb
    feature_datasets = arcpy.ListDatasets() or [""]

    for dataset in feature_datasets:
        arcpy.env.workspace = os.path.join(mdb, dataset) if dataset else mdb
        for fc in arcpy.ListFeatureClasses():
            if fc in valid_feature_classes:
                parcel_files.append((mdb, os.path.join(mdb, dataset, fc) if dataset else os.path.join(mdb, fc)))

# Create CSV file for report
with open(output_csv, "wb") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["File1", "File2", "Overlap Count"])

    # Compare each file with every other file (only different sources)
    for i in range(len(parcel_files)):
        for j in range(i + 1, len(parcel_files)):
            mdb1, fc1 = parcel_files[i]
            mdb2, fc2 = parcel_files[j]

            if mdb1 == mdb2:
                continue  # Skip comparisons within the same MDB file

            print("🔍 Checking overlap between: {} & {}".format(fc1, fc2))
            intersect_output = "in_memory/intersect_output_{}_{}".format(i, j)

            try:
                arcpy.Intersect_analysis([fc1, fc2], intersect_output)
                count = int(arcpy.GetCount_management(intersect_output)[0])

                if count > 0:
                    csv_writer.writerow([fc1, fc2, count])
                    print("✅ Overlap found: {} parcels".format(count))

            except arcpy.ExecuteError as e:
                print("❌ Error processing {} & {}: {}".format(fc1, fc2, e))

            if arcpy.Exists(intersect_output):
                arcpy.Delete_management(intersect_output)

print("\n📄 Overlapping report saved at: {}".format(output_csv))
