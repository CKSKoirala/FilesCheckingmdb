# -*- coding: utf-8 -*-
import arcpy
import os
import csv
import codecs
import Tkinter as tk
import tkMessageBox

# Function to process .mdb files
def process_mdb_files():
    folder_path = folder_path_entry.get().strip()

    if not folder_path or not os.path.isdir(folder_path):
        tkMessageBox.showerror("Error", "Invalid or empty directory! Please enter a valid path.")
        return

    output_csv = os.path.join(folder_path, "parcels_less_than_2.5M_report.csv")
    parcel_files = []

    # Get all .mdb files
    mdb_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".mdb")]

    for mdb in mdb_files:
        arcpy.env.workspace = mdb
        feature_datasets = arcpy.ListDatasets() or [""]

        for dataset in feature_datasets:
            arcpy.env.workspace = os.path.join(mdb, dataset) if dataset else mdb
            for fc in arcpy.ListFeatureClasses():
                if fc == "Parcel" and arcpy.Describe(fc).shapeType == "Polygon":
                    parcel_files.append((mdb, dataset, fc))

    if not parcel_files:
        tkMessageBox.showwarning("Warning", "No 'Parcel' feature class found in .mdb files!")
        return

    with codecs.open(output_csv, "w", "utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Source File", "Parcel Number", "Area (sq.m)"])

        for mdb, dataset, fc in parcel_files:
            full_fc_path = os.path.join(mdb, dataset, fc) if dataset else os.path.join(mdb, fc)
            print("Processing: {}".format(full_fc_path))

            try:
                with arcpy.da.SearchCursor(full_fc_path, ["PARCELNO", "Shape_Area"]) as cursor:
                    for row in cursor:
                        parcel_no, area = row
                        if area < 5:
                            csv_writer.writerow([full_fc_path, parcel_no, area])

                print("✔ Area analysis completed for {}".format(fc))

            except arcpy.ExecuteError as e:
                print("❌ Error processing {}: {}".format(fc, e))

    tkMessageBox.showinfo("Success", "📊 Area report saved at: {}".format(output_csv))

# GUI Setup
root = tk.Tk()
root.title("Parcel Area Analysis")
root.geometry("500x200")

tk.Label(root, text="Enter Folder Path Containing .mdb Files:").pack(pady=5)

folder_path_entry = tk.Entry(root, width=60)  # Manual input field
folder_path_entry.pack(pady=5)

tk.Button(root, text="Start Processing", command=process_mdb_files, bg="green", fg="white").pack(pady=20)

root.mainloop()
