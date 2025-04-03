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
from topology_check import ParcelOverlapValidator
# Add this to your imports
from ttk import Progressbar


class MDBValidatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MDB Validation Tool Suite - Python 2.7")
        self.root.geometry("850x650")
        self.root.configure(bg='#2c3e50')  # Dark blue background

        # Enhanced color scheme with high contrast for buttons
        self.colors = {
            'primary': '#3498db',  # Blue
            'secondary': '#2ecc71',  # Green
            'accent': '#e74c3c',  # Red
            'background': '#ecf0f1',  # Light gray
            'text': '#2c3e50',  # Dark blue
            'highlight': '#f39c12',  # Orange
            'button_text': '#ffffff',  # White
            'button_bg': '#3498db',  # Blue
            'button_active': '#2980b9',  # Darker blue
            'button_text_highlight': '#000000'  # Black for highlighted buttons
        }

        # Initialize validators list
        self.validators = [
            ("Duplicate Parcels", DuplicateParcelsValidator()),
            ("Small Areas", SmallAreasValidator()),
            ("Invalid Sheet Numbers", InvalidSheetValidator()),
            ("Invalid Ward Numbers", InvalidWardValidator()),
            ("Feature Overlaps", OverlapsValidator()),
            ("Segment Counts", SegmentCountsValidator()),
            ("Sheet Number Check", SheetNumberValidator()),
            ("Parcel Overlaps (Topology)", ParcelOverlapValidator())
        ]

        # Configure styles
        self.configure_styles()

        # Create main container
        self.main_frame = ttk.Frame(root, style='Main.TFrame')
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Header
        self.create_header()

        # Input Section
        self.create_input_section()

        # Validators Section
        self.create_validators_section()

        # Topology Options Section
        self.create_topology_options_section()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(root, textvariable=self.status_var,
                                   relief='sunken', anchor='w',
                                   bg=self.colors['primary'], fg='white',
                                   font=('Helvetica', 10, 'bold'))
        self.status_bar.pack(side='bottom', fill='x')


        # Add progress bar below the status bar
        self.progress = Progressbar(root, orient='horizontal',
                                  length=300, mode='determinate')
        self.progress.pack(side='bottom', fill='x', pady=(0,5))

        # Set status var for all validators
        for name, validator in self.validators:
            validator.set_status_var(self.status_var)

    def configure_styles(self):
        style = ttk.Style()

        # Configure main frame style
        style.configure('Main.TFrame', background=self.colors['background'])

        # Configure label frames
        style.configure('TLabelframe', background=self.colors['background'],
                        bordercolor=self.colors['primary'],
                        relief='solid', borderwidth=2)
        style.configure('TLabelframe.Label', background=self.colors['primary'],
                        foreground='white', font=('Helvetica', 10, 'bold'))

        # Configure labels
        style.configure('TLabel', background=self.colors['background'],
                        foreground=self.colors['text'],
                        font=('Helvetica', 9))

        # Configure checkbuttons
        style.configure('TCheckbutton', background=self.colors['background'],
                        font=('Helvetica', 9))

        # Configure comboboxes
        style.configure('TCombobox', fieldbackground='white',
                        selectbackground=self.colors['primary'])

    def create_header(self):
        """Create application header"""
        header_frame = ttk.Frame(self.main_frame, style='Main.TFrame')
        header_frame.pack(fill='x', pady=(0, 10))

        title = tk.Label(header_frame, text="MDB Validation Tool Suite",
                         font=('Helvetica', 16, 'bold'),
                         bg=self.colors['background'],
                         fg=self.colors['primary'])
        title.pack(side='left')

        version = tk.Label(header_frame, text="Version 2.0",
                           font=('Helvetica', 10),
                           bg=self.colors['background'],
                           fg=self.colors['text'])
        version.pack(side='right')

    def create_input_section(self):
        """Create the common input section"""
        input_frame = ttk.LabelFrame(self.main_frame, text="Input Parameters", padding=10)
        input_frame.pack(fill='x', pady=5)

        # Folder selection
        folder_frame = ttk.Frame(input_frame)
        folder_frame.pack(fill='x', pady=5)

        folder_label = ttk.Label(folder_frame, text="MDB Folder Path:")
        folder_label.pack(side='left')

        self.folder_entry = ttk.Entry(folder_frame, width=60, font=('Helvetica', 9))
        self.folder_entry.pack(side='left', padx=5, expand=True, fill='x')

        # Using standard tk.Button for better visibility
        browse_btn = tk.Button(folder_frame, text="Browse", command=self.browse_folder,
                               bg=self.colors['button_bg'], fg=self.colors['button_text'],
                               activebackground=self.colors['button_active'],
                               activeforeground=self.colors['button_text'],
                               font=('Helvetica', 9, 'bold'),
                               relief='raised', bd=2)
        browse_btn.pack(side='left')

        # Scale selection (for sheet number validation)
        self.scale_frame = ttk.Frame(input_frame)
        self.scale_frame.pack(fill='x', pady=5)

        scale_label = ttk.Label(self.scale_frame, text="Scale:")
        scale_label.pack(side='left')

        self.scale_combo = ttk.Combobox(self.scale_frame,
                                        values=["500", "600", "1200", "1250", "2400", "2500", "4800"],
                                        width=10, state='readonly', font=('Helvetica', 9))
        self.scale_combo.current(0)
        self.scale_combo.pack(side='left', padx=5)

        # Gridsheet selection (for sheet number check)
        self.gridsheet_frame = ttk.Frame(input_frame)
        self.gridsheet_frame.pack(fill='x', pady=5)

        gridsheet_label = ttk.Label(self.gridsheet_frame, text="Gridsheet:")
        gridsheet_label.pack(side='left')

        self.gridsheet_combo = ttk.Combobox(self.gridsheet_frame,
                                            values=["Gridsheet_81.shp", "Gridsheet_84.shp", "Gridsheet_87.shp"],
                                            width=20, state='readonly', font=('Helvetica', 9))
        self.gridsheet_combo.current(1)  # Default to Gridsheet_84.shp
        self.gridsheet_combo.pack(side='left', padx=5)

        # Default template path
        note_label = ttk.Label(input_frame,
                               text="Note: Gridsheets should be in D:\\Python\\Trig sheet test\\Templets",
                               font=('Helvetica', 8, 'italic'))
        note_label.pack(anchor='w')

    def create_topology_options_section(self):
        """Create section for topology-specific options"""
        options_frame = ttk.LabelFrame(self.main_frame, text="Topology Options", padding=10)
        options_frame.pack(fill='x', pady=5)

        # Keep topology layer option
        self.keep_topology_var = tk.IntVar(value=0)  # Default to delete

        keep_topology_cb = ttk.Checkbutton(options_frame,
                                           text="Keep topology layer after validation",
                                           variable=self.keep_topology_var,
                                           style='TCheckbutton')
        keep_topology_cb.pack(anchor='w', pady=2)

        # Cluster tolerance option
        tol_frame = ttk.Frame(options_frame)
        tol_frame.pack(fill='x', pady=5)

        tol_label = ttk.Label(tol_frame, text="Cluster Tolerance:")
        tol_label.pack(side='left')

        self.tolerance_combo = ttk.Combobox(tol_frame,
                                            values=["0.001 Meters", "0.01 Meters", "0.1 Meters", "1 Meter"],
                                            width=15, state='readonly', font=('Helvetica', 9))
        self.tolerance_combo.current(0)  # Default to 0.001 Meters
        self.tolerance_combo.pack(side='left', padx=5)

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
            cb = ttk.Checkbutton(check_frame, text=name, variable=var,
                                 style='TCheckbutton')
            cb.grid(row=i // 2, column=i % 2, sticky='w', padx=5, pady=2)

        # Button frame
        btn_frame = ttk.Frame(validators_frame)
        btn_frame.pack(fill='x', pady=10)

        # Select buttons - using standard tk.Button
        select_all_btn = tk.Button(btn_frame, text="Select All",
                                   command=self.select_all,
                                   bg=self.colors['button_bg'],
                                   fg=self.colors['button_text'],
                                   activebackground=self.colors['button_active'],
                                   activeforeground=self.colors['button_text'],
                                   font=('Helvetica', 9, 'bold'),
                                   relief='raised', bd=2)
        select_all_btn.pack(side='left', padx=5)

        select_none_btn = tk.Button(btn_frame, text="Select None",
                                    command=self.select_none,
                                    bg=self.colors['button_bg'],
                                    fg=self.colors['button_text'],
                                    activebackground=self.colors['button_active'],
                                    activeforeground=self.colors['button_text'],
                                    font=('Helvetica', 9, 'bold'),
                                    relief='raised', bd=2)
        select_none_btn.pack(side='left', padx=5)

        # Run button - using standard tk.Button with accent color
        run_btn = tk.Button(btn_frame, text="RUN VALIDATIONS",
                            command=self.run_validations,
                            bg=self.colors['secondary'],
                            fg=self.colors['button_text'],
                            activebackground='#27ae60',
                            activeforeground=self.colors['button_text'],
                            font=('Helvetica', 10, 'bold'),
                            relief='raised', bd=3)
        run_btn.pack(side='right', padx=5)

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

        # Reset progress bar
        self.progress['value'] = 0
        self.root.update_idletasks()

        # Count how many validations we'll run
        total_validations = sum(var.get() for var in self.validator_vars)
        if total_validations == 0:
            tkMessageBox.showerror("Error", "No validations selected!")
            return

        progress_increment = 100.0 / total_validations

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

                # Set topology options for ParcelOverlapValidator
                if isinstance(validator, ParcelOverlapValidator):
                    validator.cluster_tolerance = self.tolerance_combo.get()
                    validator.keep_topology = bool(self.keep_topology_var.get())

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

        # Complete progress bar
        self.progress['value'] = 100
        self.root.update_idletasks()

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