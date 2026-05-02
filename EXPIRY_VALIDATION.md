# Device Expiry Validation Implementation

## Overview
Added validation logic to check Mars and Pluto device project expiry dates before allowing game launch. This prevents expired projects from running the game.

## Implementation Details

### Function: `validate_device_expiry(device_name, setup_file, other_setup_file)`
Validates device project expiry before game load, with special handling for first-time setup.

**Parameters:**
- `device_name` (str): "Mars" or "Pluto"
- `setup_file` (str): Path to `uploadStatus.txt` file for this device
- `other_setup_file` (str): Path to `uploadStatus.txt` file for the other device

**Returns:**
- `tuple`: `(is_valid: bool, message: str)`
  - `is_valid`: `True` if allowed to run, `False` if validation fails
  - `message`: Status message

### Validation Flow

1. **Check File Consistency (First-Time vs Suspicious)**
   - Both setup files missing → **FIRST-TIME SETUP**: Allow game to run (files will be created)
   - One file exists, other missing → **SUSPICIOUS**: Block (possible tampering or unauthorized access)
   - Both files exist → Continue to expiry validation

2. **Check Setup File Content**
   - Reads `C:\DeviceSetups\{Device}\uploadStatus.txt`
   - Fails if file empty

3. **Extract Project Path**
   - Gets first CSV value from uploadStatus.txt
   - Trims whitespace
   - Fails if empty

4. **Check Config File Exists**
   - Constructs path: `<project_path>/data/configdata.csv`
   - Fails if file missing

5. **Read End Date**
   - Reads last row of configdata.csv
   - Extracts 3rd column value (EndDate, index 2)
   - CSV format: `HomerID,StartDate,EndDate,TotalTime,...`
   - Fails if empty or invalid format

6. **Parse Date Safely**
   - Supports multiple date formats:
     - `YYYY-MM-DD`
     - `DD-MM-YYYY`
     - `MM/DD/YYYY`
     - `YYYY/MM/DD`
     - `DD/MM/YYYY`
     - `YYYY-MM-DD HH:MM:SS`
     - `DD-MM-YYYY HH:MM:SS`
   - Fails if format not recognized

7. **Compare with Current Time**
   - Checks: `now > endDate` → Block
   - Checks: `now ≤ endDate` → Allow
   - All exceptions → Block

### Error Handling

**Graceful Failure Cases:**
- Both setup files missing → Allow (first-time setup)
- One setup file missing, other exists → Block (suspicious/tampering)
- Project path empty → Block (return `False`)
- Config file missing → Block (return `False`)
- End date missing or invalid → Block (return `False`)
- Date parse error → Block (return `False`)
- Any unexpected exception → Block (return `False`)

**User Message:**, other_setup_file)`**
- Validates device expiry BEFORE checking game executable
- Passes both setup file paths to validation function
- Shows error if validation fails
- Only launches game if validation passes

**Event Handlers Updated:**
```python
canvas1.bind("<Button-1>", lambda e: launch_game(GAME1_PATH, "Pluto", PLUTO_SETUP, MARS_SETUP))
canvas2.bind("<Button-1>", lambda e: launch_game(GAME2_PATH, "Mars", MARS_SETUP, PLUTO

**Event Handlers Updated:**
```python
canvas1.bind("<Button-1>", lambda e: launch_game(GAME1_PATH, "Pluto", PLUTO_SETUP))
canvas2.bind("<Button-1>", lambda e: launch_game(GAME2_PATH, "Mars", MARS_SETUP))
```

## File Structure Expected

```
C:\DeviceSetups\
├── Mars\
│   └── uploadStatus.txt          # Contains CSV with project path
└── Pluto\
    └── uploadStatus.txt          # Contains CSV with project path

<project_path>\
└── data\
    └── configdata.csv            # Last row contains endDate
```

### Example uploadStatus.txt:
```
C:\Projects\Mars_Project,value1,value2
```

### Example configdata.csv:
```
header1,header2,endDate
data1,data2,2025-12-31
data1,data2,2026-06-30
```
(Last row is read; endDate extracted from last column)

## First-Time Setup

If setup files don't exist on first run:
- Validation will fail (files missing)
- User will see: "Project expired. Contact support."
- Game will NOT launch
- Admin must create proper setup files before game is playable

**Action Required:**
1. Create `C:\DeviceSetups\{Device}\uploadStatus.txt` with project path
2. Ensure project path has `data/configdata.csv`
3. Set valid endDate in configdata.csv

## Testing

### Test Case 1: Valid Project (Not Expired)
- uploadStatus.txt exists with valid path
- configdata.csv exists with future endDate
- **Expected:** Game launches

### Test Case 2: Expired Project
- uploadStatus.txt and configdata.csv exist
- endDate is in the past
- **Expected:** Error shown, game blocked

### Test Case 3: Missing Setup File
- uploadStatus.txt does not exist
- **Expected:** Error shown, game blocked

### Test Case 4: Missing Config File
- uploadStatus.txt exists but referenced path/configdata.csv missing
- **Expected:** Error shown, game blocked

### Test Case 5: Invalid Date Format
- configdata.csv has invalid date format
- **Expected:** Error shown, game blocked

## Constants
- `MARS_SETUP` = `r"C:\DeviceSetups\Mars\uploadStatus.txt"`
- `PLUTO_SETUP` = `r"C:\DeviceSetups\Pluto\uploadStatus.txt"`

## Dependencies
- `datetime` module (Python standard library)
- Existing: `tkinter`, `subprocess`, `os`, `sys`

## Notes
- All date/time comparisons use `datetime.now()` (local system time)
- All file reads use UTF-8 encoding
- All values are trimmed of whitespace before processing
- Validation fails safely (no crashes) on any unexpected error
- Error messages are consistent for all failure cases

