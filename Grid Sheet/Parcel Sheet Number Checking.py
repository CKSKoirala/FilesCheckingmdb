import arcpy
import os
import csv

# Input shapefile and feature class
shapefile = r"D:\Python\Trig sheet test\Templets\Gridsheet_87.shp"
mdb_path = r"D:\Python\Trig sheet test\Field_data\Khumjung.mdb"
feature_class = os.path.join(mdb_path, "Parcel")

# Output directory for intersection shapefile and reports
output_dir = r"D:\Python\Trig sheet test\Intersection"

# Intersection shapefile path for output
intersect_shp = os.path.join(output_dir, "Intersect_Grid_Parcel.shp")

# Perform intersection
if arcpy.Exists(shapefile) and arcpy.Exists(feature_class):
    if arcpy.Exists(intersect_shp):
        arcpy.Delete_management(intersect_shp)  # Delete existing shapefile if it exists
    arcpy.Intersect_analysis([shapefile, feature_class], intersect_shp, "ALL")
else:
    print("One or more input datasets do not exist. Please check the file paths.")

# Output CSV file for intersection report
csv_output = os.path.join(output_dir, "Intersection_Report.csv")

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
