# Google Sheets

Google Sheets is a spreadsheet program included as part of the free, web-based Google Docs Editors suite. The `Spreadsheet` class in gcp-pilot provides a high-level interface for interacting with Google Sheets.

## Installation

To use the Google Sheets functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.sheets import Spreadsheet

# Initialize with a sheet ID
spreadsheet = Spreadsheet(sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")

# Initialize with a sheet URL
spreadsheet = Spreadsheet(sheet_id="https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit")

# Initialize with specific project
spreadsheet = Spreadsheet(
    sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    project_id="my-project"
)

# Initialize with service account impersonation
spreadsheet = Spreadsheet(
    sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    impersonate_account="service-account@project-id.iam.gserviceaccount.com"
)
```

### Working with Worksheets

#### Accessing a Worksheet

```python
# Get a worksheet by name
worksheet = spreadsheet.worksheet("Sheet1")

# Now you can use all gspread Worksheet methods
values = worksheet.get_all_values()
cell = worksheet.acell("A1")
row = worksheet.row_values(1)
column = worksheet.col_values(1)
```

### Getting the Spreadsheet URL

```python
# Get the URL of the spreadsheet
url = spreadsheet.url
print(f"Spreadsheet URL: {url}")
```

## Advanced Usage

Since the `Spreadsheet` class is a wrapper around the [gspread](https://gspread.readthedocs.io/) library, you can use all the functionality provided by gspread once you have a worksheet:

```python
worksheet = spreadsheet.worksheet("Sheet1")

# Update a cell
worksheet.update_cell(1, 1, "New Value")

# Update a range
worksheet.update("A1:B2", [["A1", "B1"], ["A2", "B2"]])

# Find a cell
cell = worksheet.find("Value to find")

# Append rows
worksheet.append_rows([["A1", "B1"], ["A2", "B2"]])
```

## Error Handling

The Spreadsheet class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    spreadsheet = Spreadsheet(sheet_id="non-existent-sheet-id")
except exceptions.NotFound:
    print("Spreadsheet not found")

try:
    worksheet = spreadsheet.worksheet("non-existent-worksheet")
except exceptions.NotFound:
    print("Worksheet not found")
```