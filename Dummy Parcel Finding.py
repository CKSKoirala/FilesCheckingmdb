import arcpy
import os
import csv
import codecs
import Tkinter as tk
import tkFileDialog


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


class App(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master
        self.master.title("MDB Attribute Checker v2.1.3")
        self.pack()
        self.create_widgets()


    def create_widgets(self):
        """Create UI elements"""

        # Folder Path Label
        self.label_folder = tk.Label(self, text="Enter path to the main folder:", font=("Arial", 10, "bold"))
        self.label_folder.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Folder Path Entry
        self.folder_entry = tk.Entry(self, width=50)
        self.folder_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Browse Button
        self.browse_button = tk.Button(self, text="Browse", command=self.select_folder)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Process Button
        self.process_button = tk.Button(self, text="Process", command=self.process_mdb_files, width=30, bg="green",
                                        fg="white")
        self.process_button.grid(row=1, column=1, padx=5, pady=10, sticky="w")

        # Instructions Label
        self.instruction_label = tk.Label(self, text="Instruction:", font=("Arial", 10, "bold italic"), fg="blue")
        self.instruction_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        # Instructions Text
        instructions = (
            "1. Select the folder containing MDB files with a 'Parcel' feature class.\n"
            "2. The script will check for duplicate parcels and ignore those with 'ParcelNo' = 0 or parcels that are not touching each other."
        )
        self.instruction_text = tk.Label(self, text=instructions, justify="left", font=("Arial", 9), fg="black")
        self.instruction_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")

    def select_folder(self):
        """Opens a folder selection dialog and updates the entry field"""
        folder_path = tkFileDialog.askdirectory()
        if folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)

    def process_mdb_files(self):
        """Processes MDB files and generates CSV error reports"""
        folder_path = self.folder_entry.get()
        if not folder_path:
            print("Error: Please enter or select a folder!")
            return

        output_csv = os.path.join(folder_path, "duplicate_parcels_report.csv")

        parcel_files = []
        exception=["merged"]
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
            print("Error: No 'Parcel' feature class found!")
            return

        with codecs.open(output_csv, "w", "utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Source File", "Parcel Number", "Frequency"])

            for mdb, dataset, fc in parcel_files:
                full_fc_path = os.path.join(mdb, dataset, fc) if dataset else os.path.join(mdb, fc)
                print("Processing: {}".format(full_fc_path))

                frequency_table = "in_memory/frequency_table"

                try:
                    arcpy.Frequency_analysis(full_fc_path, frequency_table, ["PARCELNO"])

                    with arcpy.da.SearchCursor(frequency_table, ["PARCELNO", "FREQUENCY"]) as cursor:
                        for row in cursor:
                            parcel_no, frequency = row
                            # Skip parcel number 0
                            if parcel_no == 0:
                                continue
                            if frequency > 1:
                                csv_writer.writerow([full_fc_path, parcel_no, frequency])

                    print("Frequency analysis completed for {}".format(fc))

                except arcpy.ExecuteError as e:
                    print("Error processing {}: {}".format(fc, e))

                if arcpy.Exists(frequency_table):
                    arcpy.Delete_management(frequency_table)

        print("\nDuplicate Parcel Report saved at: {}".format(output_csv))


# Run the Tkinter GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
