# -*- coding: utf-8 -*-
import os
import arcpy


def find_mdb_files(directory, exception=["merged"]):
    """Find all .mdb files in directory, excluding those in exception folders"""
    mdb_files = []
    for root, dirnames, filenames in os.walk(directory):
        if any(x in root.lower() for x in exception):
            continue
        dirnames[:] = [d for d in dirnames if not any(x in os.path.join(root, d).lower() for x in exception)]
        for filename in filenames:
            if filename.lower().endswith('.mdb') and not any(
                    x in os.path.join(root, filename).lower() for x in exception):
                mdb_files.append(os.path.join(root, filename))
    return mdb_files


def get_feature_classes(mdb_path, fc_names):
    """Get full paths to feature classes in an MDB"""
    arcpy.env.workspace = mdb_path
    feature_classes = []

    datasets = arcpy.ListDatasets() or [""]
    for dataset in datasets:
        arcpy.env.workspace = os.path.join(mdb_path, dataset) if dataset else mdb_path
        for fc in arcpy.ListFeatureClasses():
            if fc in fc_names:
                full_path = os.path.join(mdb_path, dataset, fc) if dataset else os.path.join(mdb_path, fc)
                feature_classes.append((fc, full_path))

    return feature_classes