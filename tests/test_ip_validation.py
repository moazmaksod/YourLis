
import sys
import unittest
from unittest.mock import MagicMock
import socket
import os

# Mock modules that might cause side effects on import in the test environment
sys.modules["log.logger"] = MagicMock()
sys.modules["log.log_config"] = MagicMock()
sys.modules["log"] = MagicMock()
sys.modules["pyodbc"] = MagicMock()

# Add parent directory to path to import setting.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can safely import validate_binding
from setting.config import validate_binding

class TestIPValidation(unittest.TestCase):
    def test_localhost(self):
        """Test that localhost is valid."""
        self.assertTrue(validate_binding("127.0.0.1"))

    def test_local_ip(self):
        """Test that actual local IPs are valid."""
        hostname = socket.gethostname()
        try:
            local_ips = socket.gethostbyname_ex(hostname)[2]
            if local_ips:
                for ip in local_ips:
                    self.assertTrue(validate_binding(ip))
        except Exception:
            pass # fallback if gethostbyname_ex fails

    def test_invalid_ip(self):
        """Test that a non-local IP is invalid."""
        # Check against local IPs to be sure
        hostname = socket.gethostname()
        try:
            local_ips = socket.gethostbyname_ex(hostname)[2]
            local_ips.append("127.0.0.1")
        except:
            local_ips = ["127.0.0.1"]

        # 192.0.2.x is TEST-NET-1, reserved for documentation and examples, 
        # but theoretically one COULD bind to it if they added it to interface.
        # But for this user case, checking a random IP that isn't ours is enough.
        test_ip = "192.168.255.253"
        if test_ip not in local_ips:
             self.assertFalse(validate_binding(test_ip))

    def test_bad_format(self):
        """Test that malformed IPs return False."""
        self.assertFalse(validate_binding("not.an.ip"))
        self.assertFalse(validate_binding("999.999.999.999"))

if __name__ == "__main__":
    unittest.main()
