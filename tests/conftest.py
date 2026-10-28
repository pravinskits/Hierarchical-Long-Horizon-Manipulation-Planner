import sys
from unittest.mock import MagicMock

# Mock pybullet for tests since it cannot be installed in this environment
sys.modules['pybullet'] = MagicMock()
sys.modules['pybullet_data'] = MagicMock()
