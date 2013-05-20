try:
    STRING_TYPES = (unicode, str)
except NameError: #pragma NO COVER
    STRING_TYPES = (str,)

try:
    from urllib.parse import quote
except ImportError: #pragma NO COVER
    from urllib import quote

try:
    from urllib.parse import urlsplit
except ImportError: #pragma NO COVER
    from urlparse import urlsplit
