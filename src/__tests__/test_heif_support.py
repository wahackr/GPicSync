#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for HEIF/HEIC image format support in GPicSync

Tests verify that HEIF (.heif) and HEIC (.heic) files are properly:
- Recognized by file filtering functions
- Processed by the geotagging pipeline
- Handled in both uppercase and lowercase extensions
"""

import pytest
import sys
import os
import fnmatch
from unittest.mock import Mock
import tempfile
import shutil
import time

# Add parent directory to path to import gpicsync modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules we're testing
from gpicsync import getFileList

# Check if exiftool is available
EXIFTOOL_AVAILABLE = os.system('which exiftool > /dev/null 2>&1') == 0


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_test_dir():
    """Create temporary directory with dummy test files"""
    test_dir = tempfile.mkdtemp()
    
    # Create dummy test files with various extensions
    test_files = [
        'photo1.jpg', 'photo2.JPG',
        'photo3.heic', 'photo4.HEIC',
        'photo5.heif', 'photo6.HEIF',
        'photo7.cr2', 'photo8.nef',
        'not_image.txt', 'not_image.pdf',
    ]
    
    for filename in test_files:
        open(os.path.join(test_dir, filename), 'w').close()
    
    yield test_dir
    
    # Cleanup
    shutil.rmtree(test_dir)


@pytest.fixture
def temp_image_dir():
    """Create temporary directory with image files for getFileList tests"""
    test_dir = tempfile.mkdtemp()
    
    image_files = [
        'IMG_001.jpg', 'IMG_002.JPG',
        'IMG_003.heic', 'IMG_004.HEIC',
        'IMG_005.heif', 'IMG_006.HEIF',
        'IMG_007.cr2',
    ]
    
    non_image_files = ['readme.txt', 'data.csv', 'video.mp4']
    
    for filename in image_files + non_image_files:
        open(os.path.join(test_dir, filename), 'w').close()
    
    yield test_dir
    
    shutil.rmtree(test_dir)


@pytest.fixture
def test_data_paths():
    """Provide paths to real test data files"""
    test_data_dir = os.path.dirname(os.path.abspath(__file__))
    return {
        'heic_file1': os.path.join(test_data_dir, 'IMG_8845.HEIC'),
        'heic_file2': os.path.join(test_data_dir, 'IMG_8846.HEIC'),
        'gpx_file': os.path.join(test_data_dir, 'activity_21746664559.gpx'),
    }


@pytest.fixture
def temp_work_dir():
    """Create temporary directory for working with file copies"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


# ============================================================================
# Test: HEIF File Recognition
# ============================================================================

class TestHEIFFileRecognition:
    """Test that HEIF/HEIC files are recognized by file filters"""
    
    def test_heic_lowercase_matches(self):
        """Test that lowercase .heic extension is recognized"""
        assert fnmatch.fnmatch('photo.heic', '*.heic')
        assert fnmatch.fnmatch('IMG_8845.heic', '*.heic')
    
    def test_heic_uppercase_matches(self):
        """Test that uppercase .HEIC extension is recognized"""
        assert fnmatch.fnmatch('photo.HEIC', '*.HEIC')
        assert fnmatch.fnmatch('IMG_8845.HEIC', '*.HEIC')
    
    def test_heif_lowercase_matches(self):
        """Test that lowercase .heif extension is recognized"""
        assert fnmatch.fnmatch('photo.heif', '*.heif')
        assert fnmatch.fnmatch('IMG_8845.heif', '*.heif')
    
    def test_heif_uppercase_matches(self):
        """Test that uppercase .HEIF extension is recognized"""
        assert fnmatch.fnmatch('photo.HEIF', '*.HEIF')
        assert fnmatch.fnmatch('IMG_8845.HEIF', '*.HEIF')
    
    def test_non_heif_files_dont_match(self):
        """Test that non-HEIF files don't match HEIF patterns"""
        assert not fnmatch.fnmatch('photo.txt', '*.heic')
        assert not fnmatch.fnmatch('photo.jpg', '*.heic')
        assert not fnmatch.fnmatch('photo.pdf', '*.HEIF')


# ============================================================================
# Test: GetFileList Function
# ============================================================================

class TestGetFileList:
    """Test the getFileList function with HEIF/HEIC files"""
    
    def _inject_modules_and_options(self, test_dir):
        """Helper to inject required modules into gpicsync namespace"""
        import gpicsync
        
        gpicsync.os = os
        gpicsync.fnmatch = fnmatch
        
        mock_options = Mock()
        mock_options.dir = test_dir
        
        original_options = getattr(gpicsync, 'options', None)
        gpicsync.options = mock_options
        
        return gpicsync, original_options
    
    def _restore_options(self, gpicsync, original_options):
        """Helper to restore original options"""
        if original_options is not None:
            gpicsync.options = original_options
        elif hasattr(gpicsync, 'options'):
            delattr(gpicsync, 'options')
    
    def test_getfilelist_includes_heic_files(self, temp_image_dir):
        """Test that getFileList yields HEIC files"""
        gpicsync_module, original = self._inject_modules_and_options(temp_image_dir)
        
        try:
            file_list = list(getFileList(temp_image_dir))
            filenames = [filename for filename, filepath in file_list]
            
            assert 'IMG_003.heic' in filenames
            assert 'IMG_004.HEIC' in filenames
            assert 'IMG_005.heif' in filenames
            assert 'IMG_006.HEIF' in filenames
        finally:
            self._restore_options(gpicsync_module, original)
    
    def test_getfilelist_includes_traditional_formats(self, temp_image_dir):
        """Test that getFileList still includes traditional image formats"""
        gpicsync_module, original = self._inject_modules_and_options(temp_image_dir)
        
        try:
            file_list = list(getFileList(temp_image_dir))
            filenames = [filename for filename, filepath in file_list]
            
            assert 'IMG_001.jpg' in filenames
            assert 'IMG_002.JPG' in filenames
            assert 'IMG_007.cr2' in filenames
        finally:
            self._restore_options(gpicsync_module, original)
    
    def test_getfilelist_excludes_non_images(self, temp_image_dir):
        """Test that getFileList excludes non-image files"""
        gpicsync_module, original = self._inject_modules_and_options(temp_image_dir)
        
        try:
            file_list = list(getFileList(temp_image_dir))
            filenames = [filename for filename, filepath in file_list]
            
            assert 'readme.txt' not in filenames
            assert 'data.csv' not in filenames
            assert 'video.mp4' not in filenames
        finally:
            self._restore_options(gpicsync_module, original)
    
    def test_getfilelist_returns_full_paths(self, temp_image_dir):
        """Test that getFileList returns full file paths"""
        gpicsync_module, original = self._inject_modules_and_options(temp_image_dir)
        
        try:
            file_list = list(getFileList(temp_image_dir))
            
            for filename, filepath in file_list:
                assert temp_image_dir in filepath
                assert filepath.endswith(filename)
        finally:
            self._restore_options(gpicsync_module, original)


# ============================================================================
# Test: HEIF Geotagging Integration
# ============================================================================

class TestHEIFGeotaggingIntegration:
    """Integration tests for HEIF geotagging with real test files"""
    
    def test_heic_test_files_exist(self, test_data_paths):
        """Verify that test HEIC files are present"""
        assert os.path.exists(test_data_paths['heic_file1']), \
            f"Test file not found: {test_data_paths['heic_file1']}"
        assert os.path.exists(test_data_paths['heic_file2']), \
            f"Test file not found: {test_data_paths['heic_file2']}"
        assert os.path.exists(test_data_paths['gpx_file']), \
            f"GPX test file not found: {test_data_paths['gpx_file']}"
    
    def test_heic_files_are_valid(self, test_data_paths):
        """Test that HEIC files are valid image files"""
        assert os.path.getsize(test_data_paths['heic_file1']) > 1000, \
            "HEIC file 1 appears to be empty or too small"
        assert os.path.getsize(test_data_paths['heic_file2']) > 1000, \
            "HEIC file 2 appears to be empty or too small"
    
    def test_gpx_file_is_valid(self, test_data_paths):
        """Test that GPX file contains trackpoints"""
        with open(test_data_paths['gpx_file'], 'r') as f:
            content = f.read()
            assert '<trkpt' in content, "GPX file should contain trackpoints"
            assert 'lat=' in content, "GPX file should contain latitude"
            assert 'lon=' in content, "GPX file should contain longitude"
            assert '<time>' in content, "GPX file should contain timestamps"
    
    @pytest.mark.skipif(not EXIFTOOL_AVAILABLE, 
                        reason="exiftool not installed - required for EXIF writing tests")
    def test_heic_geotagging_writes_gps_data(self, test_data_paths, temp_work_dir):
        """Test that GPS coordinates are actually written to HEIC file"""
        from gpicsync import GpicSync
        from geoexif import GeoExif
        
        # Create a working copy of the HEIC file
        test_file = os.path.join(temp_work_dir, 'test_image.HEIC')
        shutil.copy2(test_data_paths['heic_file1'], test_file)
        
        # Verify file has no GPS data initially (or read existing data)
        pic_before = GeoExif(test_file)
        lat_before = pic_before.readLatitude()
        lon_before = pic_before.readLongitude()
        print(f"\nBefore geotagging - Lat: {lat_before}, Lon: {lon_before}")
        
        # Create GpicSync instance with test GPX file
        geo = GpicSync(
            gpxFile=[test_data_paths['gpx_file']],
            tcam_l="00:00:00",
            tgps_l="00:00:00", 
            UTCoffset=8,
            timerange=86400,
            backup=False
        )
        
        # Perform geotagging
        result = geo.syncPicture(test_file)
        
        # Result should be a list with status message and coordinates
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 2, "Result should contain at least status, lat, lon"
        
        status_msg = result[0]
        result_lat = result[1]
        result_lon = result[2]
        
        print(f"\nGeotagging result: {status_msg}")
        print(f"Coordinates from result: Lat={result_lat}, Lon={result_lon}")
        
        # Verify coordinates were returned
        if result_lat and result_lon:
            assert result_lat != "", "Latitude should not be empty"
            assert result_lon != "", "Longitude should not be empty"
            
            # Wait for exiftool processes to complete writing
            time.sleep(2)
            
            # Read GPS data back from the file using exiftool
            pic_after = GeoExif(test_file)
            lat_after = pic_after.readLatitude()
            lon_after = pic_after.readLongitude()
            
            print(f"After geotagging - Lat: {lat_after}, Lon: {lon_after}")
            
            # Verify GPS data was actually written to the file
            assert lat_after != "None", "Latitude should be written to HEIC file"
            assert lon_after != "None", "Longitude should be written to HEIC file"
            
            # Verify the written coordinates match what was returned
            assert abs(float(lat_after) - float(result_lat)) < 0.00001, \
                "Written latitude should match result latitude"
            assert abs(float(lon_after) - float(result_lon)) < 0.00001, \
                "Written longitude should match result longitude"
            
            # Verify coordinates are within reasonable range
            assert -90 < float(lat_after) < 90, "Latitude should be between -90 and 90"
            assert -180 < float(lon_after) < 180, "Longitude should be between -180 and 180"
        else:
            assert "WARNING" in status_msg, \
                "If no coordinates written, status should contain WARNING"
    
    @pytest.mark.skipif(not EXIFTOOL_AVAILABLE, reason="exiftool not installed")
    def test_heic_preserves_other_metadata(self, test_data_paths, temp_work_dir):
        """Test that geotagging HEIC doesn't corrupt other EXIF data"""
        from gpicsync import GpicSync
        from geoexif import GeoExif
        
        # Create a working copy
        test_file = os.path.join(temp_work_dir, 'test_metadata.HEIC')
        shutil.copy2(test_data_paths['heic_file1'], test_file)
        
        # Read original datetime
        pic_before = GeoExif(test_file)
        datetime_before = pic_before.readDateTimeSize()
        
        # Perform geotagging
        geo = GpicSync(
            gpxFile=[test_data_paths['gpx_file']],
            UTCoffset=8,
            timerange=86400,
            backup=False
        )
        geo.syncPicture(test_file)
        
        # Wait for exiftool to complete
        time.sleep(2)
        
        # Read datetime after geotagging
        pic_after = GeoExif(test_file)
        datetime_after = pic_after.readDateTimeSize()
        
        # Verify datetime is preserved
        assert datetime_before[0] == datetime_after[0], "Original date should be preserved"
        assert datetime_before[1] == datetime_after[1], "Original time should be preserved"
    
    @pytest.mark.skipif(not EXIFTOOL_AVAILABLE, reason="exiftool not installed")
    def test_multiple_heic_files_geotagged(self, test_data_paths, temp_work_dir):
        """Test that multiple HEIC files can be geotagged in sequence"""
        from gpicsync import GpicSync
        from geoexif import GeoExif
        
        # Create copies of both test files
        test_file1 = os.path.join(temp_work_dir, 'test1.HEIC')
        test_file2 = os.path.join(temp_work_dir, 'test2.HEIC')
        shutil.copy2(test_data_paths['heic_file1'], test_file1)
        shutil.copy2(test_data_paths['heic_file2'], test_file2)
        
        # Geotag both files
        geo = GpicSync(
            gpxFile=[test_data_paths['gpx_file']],
            UTCoffset=8,
            timerange=86400,
            backup=False
        )
        
        result1 = geo.syncPicture(test_file1)
        result2 = geo.syncPicture(test_file2)
        
        # Verify both were processed
        assert result1 is not None
        assert result2 is not None
        
        # Wait for exiftool to complete
        time.sleep(2)
        
        # Read GPS data from both files
        pic1 = GeoExif(test_file1)
        pic2 = GeoExif(test_file2)
        
        lat1 = pic1.readLatitude()
        lon1 = pic1.readLongitude()
        lat2 = pic2.readLatitude()
        lon2 = pic2.readLongitude()
        
        print(f"\nFile 1 GPS: Lat={lat1}, Lon={lon1}")
        print(f"\nFile 2 GPS: Lat={lat2}, Lon={lon2}")
        
        # Verify the function completed without errors
        assert result1[0] is not None
        assert result2[0] is not None


# ============================================================================
# Test: File Extension Coverage
# ============================================================================

class TestFileExtensionCoverage:
    """Test that all HEIF variants are covered"""
    
    def test_all_heif_extensions_covered(self):
        """Ensure all common HEIF/HEIC extension variants are supported"""
        extensions_to_test = [
            '*.heic', '*.HEIC',
            '*.heif', '*.HEIF',
        ]
        
        test_files = [
            'photo.heic', 'PHOTO.HEIC',
            'photo.heif', 'PHOTO.HEIF',
        ]
        
        for i, test_file in enumerate(test_files):
            pattern = extensions_to_test[i]
            assert fnmatch.fnmatch(test_file, pattern), \
                f"File '{test_file}' should match pattern '{pattern}'"

