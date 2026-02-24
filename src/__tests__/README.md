# GPicSync Test Suite

## Test Files

This directory contains test files for verifying HEIF/HEIC support in GPicSync:

- `IMG_8845.HEIC` - Test HEIC image file
- `IMG_8846.HEIC` - Test HEIC image file  
- `activity_21746664559.gpx` - GPS track log with 5049 trackpoints

## Running Tests

### Prerequisites

**Python and pytest:**
```bash
pip3 install pytest --user
```

**ExifTool** (required for full test coverage):

**Ubuntu/Debian:**
```bash
sudo apt install libimage-exiftool-perl
```

**macOS:**
```bash
brew install exiftool
```

**Fedora/RHEL:**
```bash
sudo dnf install perl-Image-ExifTool
```

### Run All Tests

```bash
cd src/__tests__
pytest test_heif_support.py -v
```

### Run with Detailed Output

```bash
pytest test_heif_support.py -vv
```

### Run Specific Test Class

```bash
pytest test_heif_support.py::TestHEIFFileRecognition -v
```

### Run Specific Test

```bash
pytest test_heif_support.py::TestHEIFGeotaggingIntegration::test_heic_geotagging_writes_gps_data -v
```

### Show Print Statements

```bash
pytest test_heif_support.py -v -s
```

## Test Coverage

### TestHEIFFileRecognition
- ✓ Verifies .heic/.HEIC/.heif/.HEIF extensions are recognized
- ✓ Tests pattern matching for file filters

### TestGetFileList  
- ✓ Verifies HEIF files are included in file lists
- ✓ Ensures traditional formats still work
- ✓ Confirms non-image files are excluded

### TestHEIFGeotaggingIntegration (requires exiftool)
- ✓ Verifies GPS data is actually written to HEIC files
- ✓ Confirms written coordinates match expected values
- ✓ Tests that other EXIF metadata is preserved
- ✓ Validates multiple HEIC files can be processed

### TestFileExtensionCoverage
- ✓ Ensures all HEIF/HEIC variants are supported

## Notes

- Tests that require ExifTool will be **skipped** if it's not installed
- The integration tests create temporary copies of files (originals are never modified)
- Tests verify actual EXIF data is written, not just mocked
- Using **pytest** for cleaner output and better assertion messages
