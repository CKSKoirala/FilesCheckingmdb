import arcpy
import os
import csv
import tkinter as tk
import tkFileDialog  # Use this for file dialog in Python 2.7


def find_mdb_files(directory, exception):
    mdb_files = []
    # Get mdb_validator .mdb files
    for root, dirnames, filenames in os.walk(directory):
        if any(x in root.lower() for x in exception):  # Skip directories in exception list
            continue  # Use continue instead of break

        dirnames[:] = [d for d in dirnames if
                       not any(x in os.path.join(root, d).lower() for x in exception)]  # Exclude subdirectories

        for filename in filenames:
            if filename.endswith('.mdb') and not any(
                    x in os.path.join(root, filename).lower() for x in exception):  # Ensure files are excluded
                mdb_files.append(os.path.join(root, filename))

    return mdb_files


class App(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master
        self.master.title("Parcel Sheet Number Checker")
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

        # Central Meridian Option
        self.Sheet = tk.Label(self, text="Choose Central Meridian", width=30)
        self.Sheet.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        options = [
            "Gridsheet_81.shp",
            "Gridsheet_84.shp",
            "Gridsheet_87.shp"
        ]

        self.variable = tk.StringVar(self)
        self.variable.set(options[1])  # Default value
        self.optionmenu = tk.OptionMenu(self, self.variable, *options)
        self.optionmenu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Process Button
        self.process_button = tk.Button(self, text="Process", command=self.process_mdb_files, width=30, bg="green",
                                        fg="white")
        self.process_button.grid(row=5, column=1, padx=5, pady=10, sticky="w")

        # Instructions Label
        self.instruction_label = tk.Label(self, text="Instruction:", font=("Arial", 10, "bold italic"), fg="blue")
        self.instruction_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        # Instructions Text
        instructions = (
            "1. Select the folder containing MDB files with a 'Parcel' feature class.\n"
            "2. The script will check for Parcel with wrong sheet number."
        )
        self.instruction_text = tk.Label(self, text=instructions, justify="left", font=("Arial", 9), fg="black")
        self.instruction_text.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="w")

    def select_folder(self):
        """Opens a folder selection dialog and updates the entry field"""
        folder_path = tkFileDialog.askdirectory()  # Corrected for Python 2.7
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
        exception = ["merged"]
        mdb_files = find_mdb_files(folder_path, exception)
        option_choosed = self.variable.get()
        shapefile = "D:\\Python\\Trig sheet test\\Templets\\" + option_choosed
        Folder_Location = "d:\\"

        # Ensure correct output folder path (with drive letter C)
        DataCleanTemp = Folder_Location + "\\DataCleanTemp"
        if (os.path.exists(DataCleanTemp)):  # delete folder if exits, otherwise it causes error
            arcpy.Delete_management(DataCleanTemp, "Folder")
        arcpy.CreateFolder_management(Folder_Location, "DataCleanTemp")
        DataCleanTemp = Folder_Location + "\\DataCleanTemp"

        intersect_shp = os.path.join(DataCleanTemp, "Intersect_Grid_Parcel.shp")

        for mdb in mdb_files:
            arcpy.env.workspace = mdb

            mdb_path = mdb  # Ensure the mdb_path variable is defined before use
            feature_class = os.path.join(mdb_path, "Parcel")

            # Perform intersection
            if arcpy.Exists(shapefile) and arcpy.Exists(feature_class):
                if arcpy.Exists(intersect_shp):
                    arcpy.Delete_management(intersect_shp)  # Delete existing shapefile if it exists
                arcpy.Intersect_analysis([shapefile, feature_class], intersect_shp, "ALL")
            else:
                print("One or more input datasets do not exist. Please check the file paths.")

            # Output CSV file for intersection report
            csv_output = os.path.join(os.path.dirname(mdb), "Intersection_Report.csv")

            # Get available fields in the intersection output
            intersection_fields = [f.name for f in arcpy.ListFields(intersect_shp)]
            print("Fields in intersection shapefile:", intersection_fields)

            # Ensure 'PageNumber' exists in the shapefile
            shape_fields = [f.name for f in arcpy.ListFields(shapefile)]
            if "PageNumber" not in shape_fields:
                raise ValueError("PageNumber field not found in the shapefile.")

            # Fields to include in the report
            fields = ["PageNumber"]  # Only PageNumber field from the shapefile

            # Ensure 'PageNumber' exists in the intersection output
            if "PageNumber" not in intersection_fields:
                raise ValueError("PageNumber field not found in the intersection result.")

            # Write CSV file with unique PageNumber values
            page_numbers_written = set()  # Set to store already written PageNumbers

            with open(csv_output, "wb") as csvfile:  # "wb" mode for Python 2
                writer = csv.writer(csvfile)
                writer.writerow(fields)  # Write header

                with arcpy.da.SearchCursor(intersect_shp, fields) as cursor:
                    for row in cursor:
                        page_number = row[0]  # Get the PageNumber value from the row
                        if page_number not in page_numbers_written:
                            writer.writerow([page_number])  # Write only if not already written
                            page_numbers_written.add(page_number)  # Mark this PageNumber as written

            print("Intersection completed. Shapefile saved at: {}".format(intersect_shp))
            print("CSV report saved at: {}".format(csv_output))

            # Now, for mismatch report generation
            # Define input shapefile (intersection result)
            input_shp = intersect_shp  # Use the intersection result

            # Fields to check
            fields = ["PageNumber", "GRIDS1", "WARDNO", "FID_Parcel", "PARCELNO"]

            # Output CSV file for mismatch report
            mismatch_csv_output = os.path.join(output_dir, "Mismatch_Report.csv")

            # Open the shapefile and find mismatches
            mismatch_records = []
            with arcpy.da.SearchCursor(input_shp, fields) as cursor:
                for row in cursor:
                    page_number, grids1, wardno, fid_parcel, parcelno = row
                    if str(page_number) != str(grids1):  # Compare as strings to handle data type variations
                        mismatch_records.append([input_shp, wardno, fid_parcel, parcelno, page_number, grids1])

            # Write to CSV
            with open(mismatch_csv_output, "wb") as csvfile:  # "wb" mode for Python 2
                writer = csv.writer(csvfile)
                writer.writerow(["Source", "WARDNO", "FID_Parcel", "PARCELNO", "PageNumber", "GRIDS1"])
                writer.writerows(mismatch_records)

            print("Mismatch report generated at: {}".format(mismatch_csv_output))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
