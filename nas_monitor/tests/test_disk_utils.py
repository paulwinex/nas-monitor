
import unittest
import asyncio
from unittest.mock import patch, MagicMock

from nas_monitor.utils.disk_utils import get_disk_usage

class TestDiskUtils(unittest.TestCase):
    
    def test_get_disk_usage_success(self):
        """Test get_disk_usage with valid path and mocked statvfs."""
        
        # Mock os.path.exists
        with patch('os.path.exists', return_value=True):
            # Mock os.statvfs
            mock_statvfs = MagicMock()
            mock_statvfs.f_blocks = 488378112
            mock_statvfs.f_frsize = 4096
            mock_statvfs.f_bfree = 237894123

            with patch('os.statvfs', return_value=mock_statvfs):
                
                # Run the async function
                result = asyncio.run(get_disk_usage('/fake/path'))

                # Assertions
                self.assertIsNotNone(result)
                self.assertEqual(result['total_gb'], 1863.01)
                self.assertEqual(result['used_gb'], 955.52)
                self.assertEqual(result['free_gb'], 907.49)
                self.assertEqual(result['percent'], 51.3)

    def test_get_disk_usage_nonexistent_path(self):
        """Test get_disk_usage with a path that does not exist."""
        
        with patch('os.path.exists', return_value=False):
            result = asyncio.run(get_disk_usage('/nonexistent/path'))
            self.assertEqual(result, {})

    def test_get_disk_usage_exception(self):
        """Test get_disk_usage when os.statvfs raises an exception."""
        
        with patch('os.path.exists', return_value=True):
            with patch('os.statvfs', side_effect=OSError("Test error")):
                result = asyncio.run(get_disk_usage('/fake/path'))
                self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
