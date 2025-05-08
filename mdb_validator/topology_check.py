# -*- coding: utf-8 -*-
import os
import string

import arcpy
import csv
import shutil
from datetime import datetime


class ParcelOverlapValidator(object):
    def __init__(self):
        self.folder_path = ""
        self.status_var = None
        self.parcel_layer_name = "Parcel"  # Default layer name
        self.output_folder = ""
        self.report_prefix = "Parcel_Overlap_Report"
        self.cluster_tolerance = "0.001 Meters"
        self.keep_topology = False  # Default to delete topology
        print("[__init__] Initialized ParcelOverlapValidator")

    def set_parameters(self, folder_path, parcel_layer_name="Parcel", output_folder=None):
        self.folder_path = folder_path
        self.parcel_layer_name = parcel_layer_name
        self.output_folder = output_folder if output_folder else os.path.join(folder_path, "Overlap_Reports")
        print("[set_parameters] Parameters set: folder_path = {}, parcel_layer_name = {}, output_folder = {}".format(
            folder_path, parcel_layer_name, self.output_folder))

    def set_status_var(self, status_var):
        self.status_var = status_var
        print("[set_status_var] Status variable set.")

    def set_folder_path(self, folder_path):
        """For compatibility with existing framework"""
        self.set_parameters(folder_path)
        print("[set_folder_path] Folder path set: {}".format(folder_path))

    def _update_status(self, message):
        if self.status_var:
            self.status_var.set(message)
        print(message)

    def _find_mdb_files(self):
        mdb_files = []
        for root, dirs, files in os.walk(self.folder_path):
            for f in files:
                if f.lower().endswith('.mdb'):
                    mdb_files.append(os.path.join(root, f))
        print("[_find_mdb_files] Found {} MDB files".format(len(mdb_files)))
        return mdb_files

    def _get_feature_classes(self, mdb_path):
        try:
            arcpy.env.workspace = mdb_path
            return arcpy.ListFeatureClasses()
        except:
            print("[_get_feature_classes] Error getting feature classes from: {}".format(mdb_path))
            return []

    def _prepare_feature_dataset(self, mdb_path):
        """Prepare feature dataset and ensure parcel layer is in it"""
        try:
            # Create Cadastre dataset if it doesn't exist
            cadastre_dataset = os.path.join(mdb_path, "Cadastre")
            if arcpy.Exists(cadastre_dataset):
                arcpy.Delete_management(cadastre_dataset)

            spatial_ref = arcpy.Describe(os.path.join(mdb_path, self.parcel_layer_name)).spatialReference
            arcpy.CreateFeatureDataset_management(mdb_path, "Cadastre", spatial_ref)

            # Define the destination parcel feature class
            parcel_in_dataset = os.path.join(cadastre_dataset, "Parcel1")

            # If the feature class already exists, delete it first
            if arcpy.Exists(parcel_in_dataset):
                self._update_status("Parcel layer already exists, deleting it first...")
                arcpy.Delete_management(parcel_in_dataset)

            # Use CopyFeatures_management instead of FeatureClassToFeatureClass_conversion
            arcpy.CopyFeatures_management(os.path.join(mdb_path, "Parcel"), parcel_in_dataset)

            print("[_prepare_feature_dataset] Feature dataset prepared for MDB: {}".format(mdb_path))
            return cadastre_dataset

        except Exception as e:
            self._update_status("Error preparing feature dataset: {}".format(str(e)))
            print("[_prepare_feature_dataset] Error: {}".format(str(e)))
            return None

    def _create_topology(self, mdb_path):
        """Create topology and find overlap errors"""
        try:
            # Prepare feature dataset
            cadastre_dataset = self._prepare_feature_dataset(mdb_path)
            if not cadastre_dataset:
                return None

            parcel_fc = os.path.join(cadastre_dataset, "Parcel1")

            # Create topology
            topology_name = "Parcel_Topology"
            topology = os.path.join(cadastre_dataset, topology_name)

            if arcpy.Exists(topology):
                arcpy.Delete_management(topology)

            # Ensure a valid cluster tolerance
            cluster_tolerance = self.cluster_tolerance if isinstance(self.cluster_tolerance, (int, float)) else 0.001

            # Create topology with a valid tolerance
            arcpy.CreateTopology_management(cadastre_dataset, topology_name, cluster_tolerance)
            arcpy.AddFeatureClassToTopology_management(topology, parcel_fc)
            arcpy.AddRuleToTopology_management(topology, "Must Not Overlap (Area)", parcel_fc)
            arcpy.AddRuleToTopology_management(topology, "Must Not Have Gaps (Area)", parcel_fc)

            # Validate topology
            arcpy.ValidateTopology_management(topology)

            # Export errors
            error_fc = os.path.join(cadastre_dataset, "temp_overlap_errors")
            arcpy.ExportTopologyErrors_management(topology, cadastre_dataset, "temp_overlap_errors")

            print("[_create_topology] Topology created and errors exported for MDB: {}".format(mdb_path))
            return error_fc + "_poly"  # ArcGIS appends _poly to the output

        except arcpy.ExecuteError:
            self._update_status("Topology Error: {}".format(arcpy.GetMessages(2)))
            print("[_create_topology] Topology Error: {}".format(arcpy.GetMessages(2)))
            return None
        except Exception as e:
            self._update_status("Topology Creation Error: {}".format(str(e)))
            print("[_create_topology] Error: {}".format(str(e)))
            return None

    def _generate_outputs(self, mdb_path, error_fc):
        """Generate both CSV report and SHP file from topology errors"""
        try:
            # Create output directory for this MDB
            file_path = mdb_path
            base_name = os.path.splitext(os.path.basename(mdb_path))[0]
            # Clean the base_name to remove invalid characters
            valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
            clean_base_name = ''.join(c for c in base_name if c in valid_chars)
            clean_base_name = clean_base_name.replace(' ', '_')  # Replace spaces with underscores

            mdb_output_folder = os.path.join(self.output_folder, base_name)

            # Clean up existing output folder if it exists
            if os.path.exists(mdb_output_folder):
                self._update_status(" Cleaning up existing output folder...")
                for root, dirs, files in os.walk(mdb_output_folder, topdown=False):
                    for name in files:
                        try:
                            os.remove(os.path.join(root, name))
                        except Exception as e:
                            self._update_status("    Failed to delete file {}: {}".format(name, str(e)))
                            print("[_generate_outputs] Failed to delete file {}: {}".format(name, str(e)))
                    for name in dirs:
                        try:
                            os.rmdir(os.path.join(root, name))
                        except Exception as e:
                            self._update_status("    Failed to delete directory {}: {}".format(name, str(e)))
                            print("[_generate_outputs] Failed to delete directory {}: {}".format(name, str(e)))
                try:
                    os.rmdir(mdb_output_folder)
                except Exception as e:
                    self._update_status("  Failed to delete output folder: {}".format(str(e)))
                    print("[_generate_outputs] Failed to delete output folder: {}".format(str(e)))
                    return None, None, 0

            # Create fresh output folder
            if not os.path.exists(mdb_output_folder):
                os.makedirs(mdb_output_folder)

            csv_path = os.path.join(mdb_output_folder,
                                    "{}_Overlaps.csv".format(clean_base_name))
            shp_path = os.path.join(mdb_output_folder,
                                    "{}_Overlaps.shp".format(clean_base_name))

            # Get original parcel attributes
            parcel_data = {}
            parcel1 = os.path.join(file_path, "Cadastre", "Parcel1")
            fields = [f.name for f in arcpy.ListFields(parcel1)
                      if f.type not in ['Geometry', 'OID'] and not f.name.startswith(('Shape_', 'OBJECTID'))]

            with arcpy.da.SearchCursor(parcel1, ["OID@"] + fields) as cursor:
                for row in cursor:
                    parcel_data[row[0]] = row[1:]

            # Export SHP file
            arcpy.CopyFeatures_management(error_fc, shp_path)

            # Prepare to read topology errors for CSV
            error_fields = ["OriginObjectID", "DestinationObjectID", "Shape_Area"]

            with open(csv_path, 'wb') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                header = [
                             "Overlap_ID", "Source_MDB", "Parcel_Layer",
                             "Parcel1_ID", "Parcel2_ID", "Overlap_Area_SQM"
                         ] + ["Parcel1_" + f for f in fields] + ["Parcel2_" + f for f in fields]
                writer.writerow(header)

                # Process errors
                overlap_count = 0
                with arcpy.da.SearchCursor(error_fc, error_fields) as cursor:
                    for origin_oid, dest_oid, overlap_area in cursor:
                        # Skip invalid pairs
                        if origin_oid == dest_oid or origin_oid not in parcel_data or dest_oid not in parcel_data:
                            continue

                        # Get attributes for both parcels
                        attrs1 = parcel_data.get(origin_oid, [None] * len(fields))
                        attrs2 = parcel_data.get(dest_oid, [None] * len(fields))

                        # Write record
                        writer.writerow(
                            [overlap_count + 1, os.path.basename(mdb_path), self.parcel_layer_name,
                             origin_oid, dest_oid, overlap_area] +
                            list(attrs1) +
                            list(attrs2)
                        )
                        overlap_count += 1

            print("[_generate_outputs] Generated outputs for MDB: {}".format(mdb_path))
            # Clean up temporary feature class
            #arcpy.Delete_management(error_fc)

            # Only delete cadastre dataset if keep_topology is False
            if not self.keep_topology:
                cadastre_dataset = os.path.join(mdb_path, "Cadastre")
                if arcpy.Exists(cadastre_dataset):
                    arcpy.Delete_management(cadastre_dataset)
            else:
                self._update_status("  Keeping topology layer as requested")

            return csv_path, shp_path, overlap_count

        except Exception as e:
            self._update_status("Output Generation Error: {}".format(str(e)))
            print("[_generate_outputs] Error: {}".format(str(e)))
            return None, None, 0

    def run_validation(self):
        if not self.folder_path:
            raise ValueError("Folder path not set")

        mdb_files = self._find_mdb_files()
        if not mdb_files:
            raise ValueError("No MDB files found in: {}".format(self.folder_path))

        self._update_status(
            "\nStarting parcel overlap validation using topology on {} MDB files...".format(len(mdb_files)))
        self._update_status("Output folder: {}".format(self.output_folder))
        self._update_status("Looking for layer: '{}'".format(self.parcel_layer_name))

        # Create main output folder if it doesn't exist
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        reports = []
        shapefiles = []
        total_overlaps = 0

        for index, mdb in enumerate(mdb_files, start=1):
            try:
                self._update_status("\nProcessing: {}".format(os.path.basename(mdb)))
                print("[topology_check] Processing ({}/{}) {}".format(index, len(mdb_files), mdb_files))

                # Check if parcel layer exists
                feature_classes = self._get_feature_classes(mdb)
                if self.parcel_layer_name not in feature_classes:
                    self._update_status("  Layer '{}' not found - skipping".format(self.parcel_layer_name))
                    continue

                # Create topology and find errors
                error_fc = self._create_topology(mdb)
                if not error_fc or not arcpy.Exists(error_fc):
                    self._update_status("  No topology errors found")
                    continue

                # Generate outputs
                csv_path, shp_path, overlap_count = self._generate_outputs(mdb, error_fc)
                total_overlaps += overlap_count

                if overlap_count > 0:
                    reports.append(csv_path)
                    shapefiles.append(shp_path)
                    self._update_status("  Found {} overlaps".format(overlap_count))
                    self._update_status("  CSV report: {}".format(os.path.basename(csv_path)))
                    self._update_status("  Shapefile: {}".format(os.path.basename(shp_path)))
                else:
                    self._update_status("  No overlapping parcels found")
                    # Clean up empty outputs
                    for f in [csv_path, shp_path]:
                        if f and os.path.exists(f):
                            os.remove(f)

            except Exception as e:
                self._update_status("  Error processing {}: {}".format(os.path.basename(mdb), str(e)))
                print("Error processing {}: {}".format(os.path.basename(mdb), str(e)))

        # Create summary
        summary_path = os.path.join(self.output_folder, "{}_Summary.txt".format(self.report_prefix))
        with open(summary_path, 'w') as f:
            f.write("Parcel Overlap Validation Summary\n")
            f.write("Processed {} MDB files\n".format(len(mdb_files)))
            f.write("Found {} overlaps\n".format(total_overlaps))
            f.write("Reports generated at:\n")
            for report in reports:
                f.write("{}\n".format(report))

        self._update_status("Validation complete. Summary report: {}".format(summary_path))
        print("[topology_check] Validation complete. Summary report generated.")
