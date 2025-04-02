# -*- coding: utf-8 -*-
import arcpy
import os
import re
import csv
import Tkinter as tk
import tkMessageBox
from tkFileDialog import askdirectory

# Define these dictionaries at the top of your script (global scope)
dic_case_sen = {
    "Ta": "11",
    "Tha": "12",
    "Da": "13",
    "Dha": "14",
    "tta": "16",
    "ttha": "17",
    "dda": "18",
    "ddha": "19",
    "dhha": "19",
    "sha": "30",
    "SHA": "31",
    "sa": "32"
}

dic_case_insen = {
    "": "00",
    "ka": "01",
    "k": "01",
    "kha": "02",
    "kh": "02",
    "ga": "03",
    "gha": "04",
    "nga": "05",
    "ng": "05",
    "ch": "06",
    "cha": "06",
    "chha": "07",
    "ja": "08",
    "jha": "09",
    "yna": "10",
    "yan": "10",
    "ana": "15",
    "na": "20",
    "pa": "21",
    "pha": "22",
    "fa": "22",
    "ba": "23",
    "bha": "24",
    "ma": "25",
    "ya": "26",
    "ra": "27",
    "la": "28",
    "wa": "29",
    "ha": "33",
    "ksha": "34",
    "kshya": "34",
    "tra": "35",
    "gya": "36"
}


def extract_ward_code_from_filename(filename):
    """Improved ward number extraction that handles both old and new filename formats"""
    # First try the original complex pattern
    clean_name = filename.replace(" ", "").replace(".mdb", "")
    original_pattern = r"^...[A-Za-z][A-Za-z\s_-]+(\d+)([\s_(-]*[A-Za-z]*[\(\s_-]*)(\d*)"
    match = re.search(original_pattern, clean_name)

    if match:
        # Process using your existing logic
        bad_chars = ['_', '-', '(', ")", " "]
        new_string_name = ''.join(i for i in match.group(2) if not i in bad_chars)

        if new_string_name in dic_case_sen:
            dic_code = dic_case_sen[new_string_name]
        elif new_string_name.lower() in dic_case_insen:
            dic_code = dic_case_insen[new_string_name.lower()]
        else:
            dic_code = "00"  # Default code if no match

        ward_code = int(match.group(1))
        if ward_code <= 99:
            return ward_code

    # Fallback for simple cases like darakh_9.mdb
    simple_match = re.search(r"(\d+)", clean_name)
    if simple_match:
        ward_num = int(simple_match.group(1))
        if 1 <= ward_num <= 99:
            return ward_num

    return None

def find_mdb_files(folder):
    """Recursively find all .mdb files in a directory."""
    mdb_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.mdb'):
                mdb_files.append(os.path.join(root, file))
    return mdb_files


def check_and_report(input_folder):
    """Check ward number mismatches and save ONLY mismatches to CSV."""
    try:
        mdb_list = find_mdb_files(input_folder)
        if not mdb_list:
            tkMessageBox.showerror("Error", "No .mdb files found in selected folder!")
            return

        output_csv = os.path.join(input_folder, 'ward_mismatches_report.csv')

        with open(output_csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Source_File', 'Parcel_Number',
                'Actual_Ward_No', 'Input_Ward_No', 'Error'
            ])

            for mdb_path in mdb_list:
                filename = os.path.basename(mdb_path)
                input_wardno = extract_ward_code_from_filename(filename)

                if input_wardno is None:
                    continue  # Skip files without ward numbers

                parcel_fc = os.path.join(mdb_path, 'Parcel')
                if not arcpy.Exists(parcel_fc):
                    continue  # Skip missing parcel feature classes

                with arcpy.da.SearchCursor(parcel_fc, ['PARCELNO', 'WARDNO']) as cursor:
                    for row in cursor:
                        parcelno = row[0]
                        error_msg = ''
                        actual_wardno = None

                        try:
                            # Handle empty/None values
                            if row[1] in [None, ""]:
                                error_msg = 'Empty WARDNO'
                            else:
                                # Convert to integer (handles "5.0" by truncating decimals)
                                try:
                                    actual_wardno = int(float(row[1]))
                                except ValueError:
                                    error_msg = 'Non-numeric WARDNO: {}'.format(row[1])

                            # Only write mismatches
                            if actual_wardno != input_wardno:
                                writer.writerow([
                                    filename,
                                    parcelno,
                                    actual_wardno if actual_wardno is not None else 'N/A',
                                    input_wardno,
                                    error_msg if error_msg else 'Mismatch detected'
                                ])

                        except Exception as e:
                            writer.writerow([
                                filename,
                                parcelno,
                                'ERROR',
                                input_wardno,
                                str(e)
                            ])

        tkMessageBox.showinfo("Success", "Mismatches report saved to:\n{}".format(output_csv))


    except Exception as e:
        tkMessageBox.showerror("Error", str(e))

def browse_folder():
    """Open folder selection dialog."""
    folder = askdirectory(title="Select Folder Containing MDB Files")
    if folder:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, folder)


def run_script():
    """Execute the main script with the selected folder."""
    input_folder = entry_path.get()
    if not input_folder:
        tkMessageBox.showerror("Error", "Please select a folder first!")
        return
    check_and_report(input_folder)


# Create Tkinter GUI
root = tk.Tk()
root.title("Ward Number Checker")

# Folder Selection
tk.Label(root, text="Select Folder:").grid(row=0, column=0, padx=5, pady=5)
entry_path = tk.Entry(root, width=50)
entry_path.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=browse_folder).grid(row=0, column=2, padx=5, pady=5)

# Run Button
tk.Button(root, text="Run Report", command=run_script).grid(row=1, column=1, pady=10)

root.mainloop()