# -*- coding: utf-8 -*-
import arcpy
import os
import csv
import codecs
import Tkinter as tk
import tkMessageBox

def find_mdb_files(directory,exception):

    mdb_files = []
    # Get all .mdb files
    for root, dirnames, filenames in os.walk(directory):
        if any(x in root.lower() for x in exception):  # To detect and skip file/trig folder
            break
        [dirnames.remove(d) for d in dirnames if any(x in os.path.join(root, d).lower() for x in
                                                     exception)]  # To skip file if they contain file/trig in absolute path
        for filename in filenames:
            if filename.endswith('.mdb'):
                mdb_files.append(os.path.join(root, filename))
    return mdb_files

# Function to process .mdb files
def process_mdb_files():
    folder_path = folder_path_entry.get().strip()
    exception = ["merged"]

    if not folder_path or not os.path.isdir(folder_path):
        tkMessageBox.showerror("Error", "Invalid or empty directory! Please enter a valid path.")
        return

    output_csv = os.path.join(folder_path, "parcels_less_than_2.5M_report.csv")
    parcel_files = []
    # Get all .mdb files

    mdb_files = find_mdb_files(folder_path,exception)

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
