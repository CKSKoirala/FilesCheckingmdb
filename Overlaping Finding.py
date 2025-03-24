# -*- coding: utf-8 -*-
import arcpy
import os
import csv
import Tkinter as tk
import tkMessageBox
import tkFileDialog


def find_mdb_files(directory, exception):
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


# Function to start processing
def process_mdb_files():
    folder_path = folder_path_entry.get().strip()

    if not folder_path or not os.path.isdir(folder_path):
        tkMessageBox.showerror("Error", "Invalid or empty directory! Please enter a valid path.")
        return
    exception=["merged"]
    mdb_files = find_mdb_files(folder_path,exception)

    if len(mdb_files) < 2:
        tkMessageBox.showwarning("Warning", "Need at least two .mdb files for overlap checking. Found: {}".format(len(mdb_files)))
        return

    output_csv = os.path.join(folder_path, "Overlapping_Report.csv")
    valid_feature_classes = ["Parcel", "Construction", "Segments"]
    parcel_files = []

    for mdb in mdb_files:
        arcpy.env.workspace = mdb
        feature_datasets = arcpy.ListDatasets() or [""]

        for dataset in feature_datasets:
            arcpy.env.workspace = os.path.join(mdb, dataset) if dataset else mdb
            for fc in arcpy.ListFeatureClasses():
                if fc in valid_feature_classes:
                    parcel_files.append((mdb, os.path.join(mdb, dataset, fc) if dataset else os.path.join(mdb, fc)))

    with open(output_csv, "wb") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["File1", "File2", "Overlap Count"])

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

    tkMessageBox.showinfo("Success", "📄 Overlapping report saved at: {}".format(output_csv))

# Function to open folder selection dialog
def browse_folder():
    folder_selected = tkFileDialog.askdirectory(title="Select Folder Containing .mdb Files")
    if folder_selected:
        folder_path_entry.delete(0, tk.END)
        folder_path_entry.insert(0, folder_selected)

# GUI Setup
root = tk.Tk()
root.title("MDB Overlap Checker")
root.geometry("500x250")

tk.Label(root, text="Enter Folder Path Containing .mdb Files:").pack(pady=5)

folder_path_entry = tk.Entry(root, width=60)  # Entry field for manual input
folder_path_entry.pack(pady=5)

tk.Button(root, text="Browse", command=browse_folder, bg="blue", fg="white").pack(pady=5)
tk.Button(root, text="Start Processing", command=process_mdb_files, bg="green", fg="white").pack(pady=20)

root.mainloop()
