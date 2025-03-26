# -*- coding: utf-8 -*-
import arcpy
import os
import csv
import codecs
import Tkinter as tk
import tkMessageBox


def find_mdb_files(directory, exception):
    mdb_files = []
    for root, dirnames, filenames in os.walk(directory):
        if any(x in root.lower() for x in exception):
            continue
        dirnames[:] = [d for d in dirnames if not any(x in os.path.join(root, d).lower() for x in exception)]
        for filename in filenames:
            if filename.endswith('.mdb') and not any(x in os.path.join(root, filename).lower() for x in exception):
                mdb_files.append(os.path.join(root, filename))
    return mdb_files


def process_mdb_files():
    folder_path = folder_path_entry.get().strip()
    exception = ["merged"]

    if not folder_path or not os.path.isdir(folder_path):
        tkMessageBox.showerror("Error", "Invalid or empty directory! Please enter a valid path.")
        return

    output_csv = os.path.join(folder_path, "parcels_construction_less_area_report.csv")
    parcel_files = []

    mdb_files = find_mdb_files(folder_path, exception)

    for mdb in mdb_files:
        arcpy.env.workspace = mdb
        feature_datasets = arcpy.ListDatasets() or [""]

        for dataset in feature_datasets:
            arcpy.env.workspace = os.path.join(mdb, dataset) if dataset else mdb
            for fc in arcpy.ListFeatureClasses():
                if fc in ["Parcel", "Construction"] and arcpy.Describe(fc).shapeType == "Polygon":
                    parcel_files.append((mdb, dataset, fc))

    if not parcel_files:
        tkMessageBox.showwarning("Warning", "No 'Parcel' or 'Construction' feature class found in .mdb files!")
        return

    with codecs.open(output_csv, "w", "utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Source File", "Feature Class", "Parcel Number", "ParFID", "Area (sq.m)"])

        for mdb, dataset, fc in parcel_files:
            full_fc_path = os.path.join(mdb, dataset, fc) if dataset else os.path.join(mdb, fc)
            print("Processing: {}".format(full_fc_path))

            try:
                # Get field names
                fields = [f.name for f in arcpy.ListFields(full_fc_path)]
                area_field = "Shape_Area" if "Shape_Area" in fields else None

                if not area_field:
                    print("❌ Skipping {} - 'Shape_Area' field not found!".format(fc))
                    continue

                if fc == "Parcel":
                    field_list = ["PARCELNO", "Shape_Area"]
                elif fc == "Construction":
                    field_list = ["ParFID", "Shape_Area"]

                with arcpy.da.SearchCursor(full_fc_path, field_list) as cursor:
                    for row in cursor:
                        if fc == "Parcel":
                            parcel_no, area = row
                            if area < 5:
                                csv_writer.writerow([full_fc_path, fc, parcel_no, "", area])

                        elif fc == "Construction":
                            parfid, area = row
                            if area < 0.5:
                                csv_writer.writerow([full_fc_path, fc, "", parfid, area])

                print("✔ Area analysis completed for {}".format(fc))

            except arcpy.ExecuteError as e:
                print("❌ Error processing {}: {}".format(fc, e))

    tkMessageBox.showinfo("Success", "📊 Area report saved at: {}".format(output_csv))


# GUI Setup
root = tk.Tk()
root.title("Parcel & Construction Area Analysis")
root.geometry("400x200")

# Instruction Label with Yellow Background
instruction_label = tk.Label(root,
                             text="Feature Class Parcel Area Checked < 5 sq.m\n"
                                  "Feature Class Construction Area Checked < 0.5 sq.m",
                             bg="yellow",  # Set background color to yellow
                             font=("Times New Roman", 9, "bold"))  # Set font to Times New Roman
instruction_label.pack(pady=5)

tk.Label(root, text="Enter Folder Path Containing .mdb Files:").pack(pady=5)

folder_path_entry = tk.Entry(root, width=60)
folder_path_entry.pack(pady=5)

tk.Button(root, text="Start Processing", command=process_mdb_files, bg="green", fg="white").pack(pady=20)

root.mainloop()
