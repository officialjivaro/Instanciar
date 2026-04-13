# appdata/config/constants.py
TIME_ZONES = [
    "Africa/Algiers","Africa/Cairo","Africa/Johannesburg","Africa/Nairobi",
    "America/Anchorage","America/Argentina/Buenos_Aires","America/Bogota",
    "America/Caracas","America/Chicago","America/Denver","America/Havana",
    "America/Jamaica","America/Los_Angeles","America/Mexico_City","America/New_York",
    "America/Phoenix","America/Puerto_Rico","America/Santo_Domingo","America/Sao_Paulo",
    "America/Texas","America/Toronto","Asia/Baghdad","Asia/Bangkok","Asia/Dubai",
    "Asia/Ho_Chi_Minh","Asia/Hong_Kong","Asia/Jakarta","Asia/Karachi","Asia/Kathmandu",
    "Asia/Manila","Asia/Riyadh","Asia/Seoul","Asia/Shanghai","Asia/Singapore",
    "Asia/Tbilisi","Asia/Tehran","Asia/Tokyo","Asia/Vladivostok","Atlantic/Cape_Verde",
    "Atlantic/Reykjavik","Australia/Adelaide","Australia/Brisbane","Australia/Darwin",
    "Australia/Perth","Australia/Sydney","Europe/Amsterdam","Europe/Athens",
    "Europe/Berlin","Europe/Brussels","Europe/Bucharest","Europe/Copenhagen",
    "Europe/Dublin","Europe/Helsinki","Europe/Istanbul","Europe/Kiev","Europe/Lisbon",
    "Europe/London","Europe/Madrid","Europe/Moscow","Europe/Oslo","Europe/Paris",
    "Europe/Prague","Europe/Rome","Europe/Stockholm","Europe/Vienna","Europe/Warsaw",
    "Indian/Mauritius","Indian/Reunion","Pacific/Apia","Pacific/Auckland",
    "Pacific/Fiji","Pacific/Guam","Pacific/Honolulu","Pacific/Port_Moresby",
    "Pacific/Tahiti","UTC"
]

LANGUAGES = [
    "Arabic (ar)","Bengali (bn)","Chinese (zh)","Dutch (nl)","English (en)",
    "French (fr)","German (de)","Hindi (hi)","Italian (it)","Japanese (ja)",
    "Korean (ko)","Malay (ms)","Portuguese (pt)","Punjabi (pa)","Russian (ru)",
    "Spanish (es)","Swahili (sw)","Thai (th)","Turkish (tr)","Vietnamese (vi)",
    "Greek (el)","Hebrew (he)","Swedish (sv)","Norwegian (no)","Danish (da)",
    "Finnish (fi)","Polish (pl)","Czech (cs)","Filipino (fil)","Urdu (ur)"
]

LEGACY_COMMON_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.6478.57 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126.0.6478.57 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0.6478.57 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126.0.6478.57 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 CriOS/126.0.6478.57 Mobile/15E148 Safari/604.1"
]

# note: kept for backward compatibility with older saved instances or older imports.
COMMON_USER_AGENTS = LEGACY_COMMON_USER_AGENTS[:]

DEFAULT_UA = LEGACY_COMMON_USER_AGENTS[0]

TIME_ZONE_MAP = {"America/Texas": "America/Chicago"}

LANG_CODE_MAP = {
    label: (label.split("(")[1].split(")")[0] if "(" in label else label)
    for label in LANGUAGES
}