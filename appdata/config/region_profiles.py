# appdata/config/region_profiles.py
"""
Region and browser-mode presets for Instanciar.

These presets are for legitimate browser-profile consistency. They help users
keep language, timezone, and profile expectations aligned with the region they
intend to use. They do not bypass website security systems.
"""

REGION_PROFILES = [
    {
        "key": "us",
        "label": "United States",
        "timezone": "America/New_York",
        "language": "English (en-US)",
        "locale": "en-US",
        "suggested_homepage": "https://www.google.com/",
    },
    {
        "key": "uk",
        "label": "United Kingdom",
        "timezone": "Europe/London",
        "language": "English (en-GB)",
        "locale": "en-GB",
        "suggested_homepage": "https://www.google.co.uk/",
    },
    {
        "key": "ca",
        "label": "Canada",
        "timezone": "America/Toronto",
        "language": "English (en-CA)",
        "locale": "en-CA",
        "suggested_homepage": "https://www.google.ca/",
    },
    {
        "key": "mx",
        "label": "Mexico",
        "timezone": "America/Mexico_City",
        "language": "Spanish (es-MX)",
        "locale": "es-MX",
        "suggested_homepage": "https://www.google.com.mx/",
    },
    {
        "key": "br",
        "label": "Brazil",
        "timezone": "America/Sao_Paulo",
        "language": "Portuguese (pt-BR)",
        "locale": "pt-BR",
        "suggested_homepage": "https://www.google.com.br/",
    },
    {
        "key": "de",
        "label": "Germany",
        "timezone": "Europe/Berlin",
        "language": "German (de-DE)",
        "locale": "de-DE",
        "suggested_homepage": "https://www.google.de/",
    },
    {
        "key": "fr",
        "label": "France",
        "timezone": "Europe/Paris",
        "language": "French (fr-FR)",
        "locale": "fr-FR",
        "suggested_homepage": "https://www.google.fr/",
    },
    {
        "key": "es",
        "label": "Spain",
        "timezone": "Europe/Madrid",
        "language": "Spanish (es-ES)",
        "locale": "es-ES",
        "suggested_homepage": "https://www.google.es/",
    },
    {
        "key": "nl",
        "label": "Netherlands",
        "timezone": "Europe/Amsterdam",
        "language": "Dutch (nl-NL)",
        "locale": "nl-NL",
        "suggested_homepage": "https://www.google.nl/",
    },
    {
        "key": "jp",
        "label": "Japan",
        "timezone": "Asia/Tokyo",
        "language": "Japanese (ja-JP)",
        "locale": "ja-JP",
        "suggested_homepage": "https://www.google.co.jp/",
    },
    {
        "key": "kr",
        "label": "South Korea",
        "timezone": "Asia/Seoul",
        "language": "Korean (ko-KR)",
        "locale": "ko-KR",
        "suggested_homepage": "https://www.google.co.kr/",
    },
    {
        "key": "sg",
        "label": "Singapore",
        "timezone": "Asia/Singapore",
        "language": "English (en-SG)",
        "locale": "en-SG",
        "suggested_homepage": "https://www.google.com.sg/",
    },
    {
        "key": "au",
        "label": "Australia",
        "timezone": "Australia/Sydney",
        "language": "English (en-AU)",
        "locale": "en-AU",
        "suggested_homepage": "https://www.google.com.au/",
    },
]

REGION_PROFILE_MAP = {profile["key"]: profile for profile in REGION_PROFILES}

LAUNCH_MODES = [
    {
        "key": "normal",
        "label": "Normal Browser Mode",
        "description": "Keeps Chrome closer to a regular profile with fewer startup restrictions.",
    },
    {
        "key": "privacy",
        "label": "Privacy Mode",
        "description": "Uses stricter quiet/private startup options from the previous launch behavior.",
    },
]

LAUNCH_MODE_MAP = {mode["key"]: mode for mode in LAUNCH_MODES}
DEFAULT_NEW_LAUNCH_MODE = "normal"
DEFAULT_LEGACY_LAUNCH_MODE = "privacy"
