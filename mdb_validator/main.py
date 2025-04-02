# -*- coding: utf-8 -*-
import os
import Tkinter as tk
import ttk
import tkMessageBox
import tkFileDialog
from duplicate_parcels import DuplicateParcelsValidator
from small_areas import SmallAreasValidator
from invalid_sheet import InvalidSheetValidator
from invalid_ward import InvalidWardValidator
from overlaps import OverlapsValidator
from segment_counts import SegmentCountsValidator
from sheet_number import SheetNumberValidator


class MDBValidatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MDB Validation Tool Suite - Python 2.7")
        self.root.geometry("750x550")

        # Initialize validators list FIRST
        self.validators = [
            ("Duplicate Parcels", DuplicateParcelsValidator()),
            ("Small Areas", SmallAreasValidator()),
            ("Invalid Sheet Numbers", InvalidSheetValidator()),
            ("Invalid Ward Numbers", InvalidWardValidator()),
            ("Feature Overlaps", OverlapsValidator()),
            ("Segment Counts", SegmentCountsValidator()),
            ("Sheet Number Check", SheetNumberValidator())
        ]

        # Configure style
        self.configure_styles()

        # Create main container
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Input Section
        self.create_input_section()

        # Validators Section
        self.create_validators_section()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(root, textvariable=self.status_var,
                                   relief='sunken', anchor='w', bg='lightgray')
        self.status_bar.pack(side='bottom', fill='x')

        # Set status var for all validators
        for name, validator in self.validators:
            validator.set_status_var(self.status_var)

    def configure_styles(self):
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0')
        style.configure('TLabelframe', background='#f0f0f0')
        style.configure('TLabelframe.Label', background='#f0f0f0')
        style.configure('TCheckbutton', background='#f0f0f0')
        style.configure('Accent.TButton', foreground='white', background='#4CAF50')

    def create_input_section(self):
        """Create the common input section"""
        input_frame = ttk.LabelFrame(self.main_frame, text="Input Parameters", padding=10)
        input_frame.pack(fill='x', pady=5)

        # Folder selection
        folder_frame = ttk.Frame(input_frame)
        folder_frame.pack(fill='x', pady=5)
        ttk.Label(folder_frame, text="MDB Folder Path:").pack(side='left')
        self.folder_entry = ttk.Entry(folder_frame, width=60)
        self.folder_entry.pack(side='left', padx=5, expand=True, fill='x')
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side='left')

        # Scale selection (for sheet number validation)
        self.scale_frame = ttk.Frame(input_frame)
        self.scale_frame.pack(fill='x', pady=5)
        ttk.Label(self.scale_frame, text="Scale:").pack(side='left')
        self.scale_combo = ttk.Combobox(self.scale_frame,
                                        values=["500", "600", "1200", "1250", "2400", "2500", "4800"],
                                        width=10, state='readonly')
        self.scale_combo.current(0)
        self.scale_combo.pack(side='left', padx=5)

        # Gridsheet selection (for sheet number check)
        self.gridsheet_frame = ttk.Frame(input_frame)
        self.gridsheet_frame.pack(fill='x', pady=5)
        ttk.Label(self.gridsheet_frame, text="Gridsheet:").pack(side='left')
        self.gridsheet_combo = ttk.Combobox(self.gridsheet_frame,
                                            values=["Gridsheet_81.shp", "Gridsheet_84.shp", "Gridsheet_87.shp"],
                                            width=20, state='readonly')
        self.gridsheet_combo.current(1)  # Default to Gridsheet_84.shp
        self.gridsheet_combo.pack(side='left', padx=5)

        # Default template path
        ttk.Label(input_frame, text="Note: Gridsheets should be in D:\\Python\\Trig sheet test\\Templets").pack(
            anchor='w')

    def create_validators_section(self):
        """Create the validators selection section"""
        validators_frame = ttk.LabelFrame(self.main_frame, text="Select Validations to Run", padding=10)
        validators_frame.pack(fill='both', expand=True, pady=5)

        # Create checkboxes for each validator
        self.validator_vars = []
        check_frame = ttk.Frame(validators_frame)
        check_frame.pack(fill='both', expand=True)

        for i, (name, validator) in enumerate(self.validators):
            var = tk.IntVar(value=1)
            self.validator_vars.append(var)
            cb = ttk.Checkbutton(check_frame, text=name, variable=var)
            cb.grid(row=i // 2, column=i % 2, sticky='w', padx=5, pady=2)

        # Button frame
        btn_frame = ttk.Frame(validators_frame)
        btn_frame.pack(fill='x', pady=10)

        # Select buttons
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Select None", command=self.select_none).pack(side='left', padx=5)

        # Run button
        ttk.Button(btn_frame, text="Run Selected Validations", command=self.run_validations,
                   style='Accent.TButton').pack(side='right', padx=5)

    def browse_folder(self):
        """Open folder dialog and update entry widget"""
        folder_path = tkFileDialog.askdirectory()
        if folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)
            self.status_var.set("Selected folder: {}".format(folder_path))

    def select_all(self):
        """Select all validations"""
        for var in self.validator_vars:
            var.set(1)
        self.status_var.set("Selected all validations")

    def select_none(self):
        """Deselect all validations"""
        for var in self.validator_vars:
            var.set(0)
        self.status_var.set("Deselected all validations")

    def run_validations(self):
        """Run the selected validations"""
        folder_path = self.folder_entry.get().strip()
        if not folder_path:
            tkMessageBox.showerror("Error", "Please select a folder containing MDB files!")
            return

        if not os.path.isdir(folder_path):
            tkMessageBox.showerror("Error", "Invalid folder path!")
            return

        # Update validator parameters
        for i, (name, validator) in enumerate(self.validators):
            if self.validator_vars[i].get() == 1:
                validator.set_folder_path(folder_path)

                # Set scale if validator needs it
                if hasattr(validator, 'set_scale'):
                    validator.set_scale(self.scale_combo.get())

                # Set gridsheet if validator needs it
                if hasattr(validator, 'set_gridsheet'):
                    validator.set_gridsheet(self.gridsheet_combo.get())

        # Run selected validations
        success_count = 0
        for i, (name, validator) in enumerate(self.validators):
            if self.validator_vars[i].get() == 1:
                try:
                    self.status_var.set("Running {}...".format(name))
                    self.root.update()  # Update UI

                    validator.run_validation()
                    success_count += 1

                    self.status_var.set("Completed {}".format(name))
                    self.root.update()  # Update UI

                except Exception as e:
                    self.status_var.set("Error in {}: {}".format(name, str(e)))
                    tkMessageBox.showerror("Error", "Failed to run {}:\n{}".format(name, str(e)))

        self.status_var.set("Completed {} of {} selected validations".format(
            success_count, sum(var.get() for var in self.validator_vars)))
        tkMessageBox.showinfo("Complete", "Validation process finished!")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = MDBValidatorApp(root)
        root.mainloop()
    except Exception as e:
        print str(e)
        tkMessageBox.showerror("Fatal Error", "Application failed to start:\n{}".format(str(e)))