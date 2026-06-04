# appdata/utils/version_parser.py
import re

def parse_version_string(v):
    m = re.match(r"[^\d]*(\d+(\.\d+)?).*", v.lower().replace("v", ""))
    if not m:
        return 0.0
    try:
        return float(m.group(1))
    except:
        return 0.0
