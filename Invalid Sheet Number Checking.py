import tkinter as tk
from tkinter import ttk, messagebox
import os
import arcpy
import csv

# Dictionary for scale verification (scale -> corresponding value)
dict_scale = {
    "500": "5554", "600": "5553", "1200": "5555", "1250": "5556",
    "2400": "5557", "2500": "5558", "4800": "5559"
}


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


# Function to check data and generate a report
def check_data_and_generate_report(mdb_folder, selected_scale):
    # Get corresponding value for selected scale
    scale_value = dict_scale.get(selected_scale, None)

    if not scale_value:
        messagebox.showerror("Error", "Invalid scale selected!")
        return

    report_file = os.path.join(mdb_folder, "invalid_sheet_number_report.csv")

    with open(report_file, 'wb') as csvfile:  # Use 'wb' mode for Python 2.7 compatibility
        fieldnames = ['MDB File Path', 'PARCELNO', 'GRIDS1', 'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        exception = ["merged"]

        mdb_files = find_mdb_files(mdb_folder,exception)
        # Iterate through all .mdb files in the folder
        for mdb_path in mdb_files:
            try:
                parcelfile = os.path.join(mdb_path, "Parcel")

                with arcpy.da.SearchCursor(parcelfile, ['PARCELNO', 'GRIDS1']) as cursor:
                    for row in cursor:
                        parcel_no = row[0]
                        grids1 = str(row[1])  # Ensure GRIDS1 is treated as a string

                        # Check if GRIDS1 starts with the correct scale value
                        if not grids1.startswith(scale_value):
                            status = "Invalid GRIDS1 (does not match selected scale)"

                            # Write only invalid data to the report
                            writer.writerow({
                                'MDB File Path': mdb_path,
                                'PARCELNO': parcel_no,
                                'GRIDS1': grids1,
                                'Status': status
                            })
            except Exception as e:
                print("Error processing {}: {}".format(mdb_path, e))

    messagebox.showinfo("Report Generation", "Invalid data report generated successfully.")


# Tkinter GUI
def run_validation():
    mdb_folder = folder_entry.get()
    selected_scale = scale_combobox.get()

    if not os.path.isdir(mdb_folder):
        messagebox.showerror("Error", "Invalid folder path!")
        return

    if selected_scale == "":
        messagebox.showerror("Error", "Please select a scale!")
        return

    check_data_and_generate_report(mdb_folder, selected_scale)


# Tkinter window setup
window = tk.Tk()
window.title("MDB Data Validator")
window.geometry("400x300")

# Folder selection
folder_label = tk.Label(window, text="Enter MDB folder path:")
folder_label.pack(pady=10)

folder_entry = tk.Entry(window, width=40)
folder_entry.pack(pady=5)

# Scale selection dropdown
scale_label = tk.Label(window, text="Select Scale:")
scale_label.pack(pady=10)

scale_combobox = ttk.Combobox(window, values=list(dict_scale.keys()))
scale_combobox.pack(pady=5)

# Validate button
validate_button = tk.Button(window, text="Validate Data", command=run_validation)
validate_button.pack(pady=20)

# Run Tkinter loop
window.mainloop()
