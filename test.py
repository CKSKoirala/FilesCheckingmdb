# -*- coding: utf-8 -*-
import arcpy
import os
import csv
import codecs
import Tkinter as tk
import tkFileDialog

# Function to get the folder location using Tkinter
def select_folder():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    folder_path = tkFileDialog.askdirectory()  # Open folder selection dialog
    return folder_path

# Function to process .mdb files and generate report
def process_mdb_files(mdb_directory, output_csv):
    # List to store only parcel feature classes
    parcel_files = []

    # Get all .mdb files
    mdb_files = [os.path.join(mdb_directory, f) for f in os.listdir(mdb_directory) if f.endswith(".mdb")]

    # Iterate through each .mdb file
    for mdb in mdb_files:
        arcpy.env.workspace = mdb
        feature_datasets = arcpy.ListDatasets() or [""]  # If no dataset, use an empty string

        for dataset in feature_datasets:
            arcpy.env.workspace = os.path.join(mdb, dataset) if dataset else mdb
            for fc in arcpy.ListFeatureClasses():
                # Only add the 'Parcel' feature class
                if fc == "Parcel" and arcpy.Describe(fc).shapeType == "Polygon":  # Ensure it's a Polygon feature class
                    parcel_files.append((mdb, dataset, fc))  # Store full path info

    # Ensure there are parcel files
    if not parcel_files:
        print("❌ No 'Parcel' feature class found!")
        return

    # Open the CSV file using codecs for UTF-8 encoding in Python 2.7
    with codecs.open(output_csv, "w", "utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Source File", "Parcel Number", "Frequency"])

        # Process each parcel feature class
        for mdb, dataset, fc in parcel_files:
            full_fc_path = os.path.join(mdb, dataset, fc) if dataset else os.path.join(mdb, fc)
            print("Processing: {}".format(full_fc_path))

            # Define output table for Frequency tool (stored in-memory)
            frequency_table = "in_memory/frequency_table"

            # Run Frequency tool on PARCELNO field (instead of ParcelNumber)
            try:
                arcpy.Frequency_analysis(full_fc_path, frequency_table, ["PARCELNO"])

                # Read the frequency results
                with arcpy.da.SearchCursor(frequency_table, ["PARCELNO", "FREQUENCY"]) as cursor:
                    for row in cursor:
                        parcel_no, frequency = row
                        if frequency > 1:  # Only save duplicates
                            csv_writer.writerow([full_fc_path, parcel_no, frequency])

                print("✔ Frequency analysis completed for {}".format(fc))

            except arcpy.ExecuteError as e:
                print("❌ Error processing {}: {}".format(fc, e))

            # Delete temporary in-memory table
            if arcpy.Exists(frequency_table):
                arcpy.Delete_management(frequency_table)

    print("\n📊 Duplicate Parcel Report saved at: {}".format(output_csv))

# Main code execution
folder = select_folder()  # Let the user select the folder
if folder:
    # Generate the output CSV file path in the same folder
    output_csv = os.path.join(folder, "duplicate_parcels_report.csv")
    process_mdb_files(folder, output_csv)  # Call the function to process the .mdb files and generate the report
else:
    print("❌ No folder selected. Exiting...")
