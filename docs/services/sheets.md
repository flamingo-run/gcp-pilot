# Google Sheets

Google Sheets is a spreadsheet program included as part of the free, web-based Google Docs Editors suite. The `Spreadsheet` class in gcp-pilot provides a high-level interface for interacting with Google Sheets.

## Installation

To use the Google Sheets functionality, you need to install gcp-pilot with the sheets extra:

```bash title="Install Sheets extra"
pip install gcp-pilot[sheets]
```

## Usage

### Initialization

```python title="Initialize Spreadsheet Client"
from gcp_pilot.sheets import Spreadsheet

spreadsheet = Spreadsheet(sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms") # (1)!
spreadsheet = Spreadsheet(sheet_id="https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit") # (2)!
spreadsheet = Spreadsheet( # (3)!
    sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    project_id="my-project"
)
spreadsheet = Spreadsheet( # (4)!
    sheet_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    impersonate_account="service-account@project-id.iam.gserviceaccount.com"
)
```

1.  Initialize with a sheet ID
2.  Initialize with a sheet URL
3.  Initialize with specific project
4.  Initialize with service account impersonation

### Working with Worksheets

#### Accessing a Worksheet

```python title="Access a Worksheet"
worksheet = spreadsheet.worksheet("Sheet1") # (1)!

values = worksheet.get_all_values() # (2)!
cell = worksheet.acell("A1")
row = worksheet.row_values(1)
column = worksheet.col_values(1)
```

1.  Get a worksheet by name
2.  Now you can use all gspread Worksheet methods

### Getting the Spreadsheet URL

```python title="Get Spreadsheet URL"
url = spreadsheet.url # (1)!
print(f"Spreadsheet URL: {url}")
```

1.  Get the URL of the spreadsheet

!!! note "Leveraging gspread"
    The `Spreadsheet` class is a wrapper around the [gspread](https://gspread.readthedocs.io/) library.
    Once you obtain a `worksheet` object, you can use all the powerful methods provided by `gspread` for more complex operations.

## Advanced Usage

Since the `Spreadsheet` class is a wrapper around the [gspread](https://gspread.readthedocs.io/) library, you can use all the functionality provided by gspread once you have a worksheet:

```python title="Advanced Usage with gspread Methods"
worksheet = spreadsheet.worksheet("Sheet1")

worksheet.update_cell(1, 1, "New Value") # (1)!
worksheet.update("A1:B2", [["A1", "B1"], ["A2", "B2"]]) # (2)!
cell = worksheet.find("Value to find") # (3)!
worksheet.append_rows([["A1", "B1"], ["A2", "B2"]]) # (4)!
```

1.  Update a cell
2.  Update a range
3.  Find a cell
4.  Append rows

## Error Handling

The Spreadsheet class handles common errors and converts them to more specific exceptions:

```python title="Error Handling for Sheets"
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