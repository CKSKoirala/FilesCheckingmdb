# -*- coding: utf-8 -*-
import arcpy
import os
import csv
import codecs
import Tkinter as tk
import tkMessageBox


# Function to process .mdb files and count features in Segments feature class
def process_segments_mdb_files():
    folder_path = folder_path_entry.get().strip()
    exception = ["merged"]

    if not folder_path or not os.path.isdir(folder_path):
        tkMessageBox.showerror("Error", "Invalid or empty directory! Please enter a valid path.")
        return

    output_csv = os.path.join(folder_path, "segments_feature_count_report.csv")

    mdb_files = find_mdb_files(folder_path, exception)

    with codecs.open(output_csv, "w", "utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Source File", "Feature Class", "Segments Count"])

        for mdb in mdb_files:
            arcpy.env.workspace = mdb
            feature_datasets = arcpy.ListDatasets() or [""]

            for dataset in feature_datasets:
                arcpy.env.workspace = os.path.join(mdb, dataset) if dataset else mdb
                for fc in arcpy.ListFeatureClasses():
                    full_fc_path = os.path.join(mdb, dataset, fc) if dataset else os.path.join(mdb, fc)
                    print("Processing: {}".format(full_fc_path))

                    # Process Segments feature class (Line feature)
                    try:
                        # Check if the feature class is a line (Polyline)
                        if fc == "Segments" and arcpy.Describe(fc).shapeType == "Polyline":
                            # Get the count of features in the Segments feature class
                            segment_count = int(arcpy.management.GetCount(full_fc_path)[0])
                            csv_writer.writerow([full_fc_path, fc, segment_count])
                            print("✔ Feature count for Segments completed for {}".format(full_fc_path))

                    except arcpy.ExecuteError as e:
                        print("❌ Error processing {}: {}".format(fc, e))

    tkMessageBox.showinfo("Success", "📊 Segments feature count report saved at: {}".format(output_csv))


# Function to find .mdb files
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


# GUI Setup
root = tk.Tk()
root.title("Segments Feature Count")
root.geometry("400x200")

# Instruction Label
instruction_label = tk.Label(root,
                             text="This tool counts features in the Segments feature class of each .mdb file.",
                             bg="yellow",  # Set background color to yellow
                             font=("Times New Roman", 8, "bold"))  # Set font to Times New Roman
instruction_label.pack(pady=10)


instruction_label.pack(pady=10)

tk.Label(root, text="Enter Folder Path Containing .mdb Files:").pack(pady=5)

folder_path_entry = tk.Entry(root, width=60)
folder_path_entry.pack(pady=5)

tk.Button(root, text="Start Processing", command=process_segments_mdb_files, bg="green", fg="white").pack(pady=20)

root.mainloop()
