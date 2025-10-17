# Python 2/3 compatibility layer
import sys

# Handle input function
if sys.version_info[0] >= 3:
    # Python 3
    raw_input = input
    import configparser as ConfigParser
    import io as StringIO
else:
    # Python 2
    import ConfigParser
    import StringIO

# Make available for import
__all__ = ['raw_input', 'ConfigParser', 'StringIO']