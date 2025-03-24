# -*- coding: utf-8 -*-
import arcpy
import os
import csv
import codecs
import Tkinter as tk
import tkMessageBox


def find_mdb_files(directory, exception):
    mdb_files = []
    # Get all .mdb files
    for root, dirnames, filenames in os.walk(directory):
        if any(x in root.lower() for x in exception):  # Skip directories in exception list
            continue  # Use continue instead of break

        dirnames[:] = [d for d in dirnames if not any(x in os.path.join(root, d).lower() for x in exception)]  # Exclude subdirectories

        for filename in filenames:
            if filename.endswith('.mdb') and not any(x in os.path.join(root, filename).lower() for x in exception):  # Ensure files are excluded
                mdb_files.append(os.path.join(root, filename))

    return mdb_files


# Function to process .mdb files
def process_mdb_files():
    folder_path = folder_path_entry.get().strip()

    if not folder_path or not os.path.isdir(folder_path):
        tkMessageBox.showerror("Error", "Invalid or empty directory! Please enter a valid path.")
        return

    output_csv = os.path.join(folder_path, "Invalid_WARDNO_Report.csv")
    parcel_files = []
    valid_ward_numbers = {str(i) for i in range(1, 10)}  # Set of valid values 1-9
    exception = ["merged"]
    # Get all .mdb files
    mdb_files = find_mdb_files(folder_path,exception)

    for mdb in mdb_files:
        arcpy.env.workspace = mdb
        feature_datasets = arcpy.ListDatasets() or [""]

        for dataset in feature_datasets:
            arcpy.env.workspace = os.path.join(mdb, dataset) if dataset else mdb
            for fc in arcpy.ListFeatureClasses():
                if fc == "Parcel":  # Check only 'Parcel' feature class
                    parcel_files.append((mdb, dataset, fc))

    if not parcel_files:
        tkMessageBox.showwarning("Warning", "No 'Parcel' feature class found in .mdb files!")
        return

    with codecs.open(output_csv, "w", "utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Source File", "Parcel Number", "WARDNO"])  # CSV Header

        for mdb, dataset, fc in parcel_files:
            full_fc_path = os.path.join(mdb, dataset, fc) if dataset else os.path.join(mdb, fc)
            print("Processing: {}".format(full_fc_path))

            try:
                with arcpy.da.SearchCursor(full_fc_path, ["PARCELNO", "WARDNO"]) as cursor:
                    for row in cursor:
                        parcel_no, ward_no = row
                        if ward_no is None or str(ward_no) not in valid_ward_numbers:  # Invalid WARDNO
                            csv_writer.writerow([full_fc_path, parcel_no, ward_no])

                print("✔ WARDNO validation completed for {}".format(fc))

            except arcpy.ExecuteError as e:
                print("❌ Error processing {}: {}".format(fc, e))

    tkMessageBox.showinfo("Success", "📊 Invalid WARDNO report saved at: {}".format(output_csv))

# GUI Setup
root = tk.Tk()
root.title("WARDNO Validation")
root.geometry("500x200")

tk.Label(root, text="Enter Folder Path Containing .mdb Files:").pack(pady=5)

folder_path_entry = tk.Entry(root, width=60)  # Manual input field
folder_path_entry.pack(pady=5)

tk.Button(root, text="Start Validation", command=process_mdb_files, bg="green", fg="white").pack(pady=20)

root.mainloop()
