# appdata/utils/random_user_agent.py
from typing import Optional

from appdata.utils.browser_identity import get_random_real_identity, get_latest_stable_identity


def generate_random_user_agent(platform_key: Optional[str] = None) -> str:
    """Return a recent real desktop Chrome user-agent string."""
    return get_random_real_identity(platform_key).get("user_agent")


def generate_latest_stable_user_agent(platform_key: Optional[str] = None) -> str:
    """Return the latest stable real desktop Chrome user-agent string."""
    return get_latest_stable_identity(platform_key).get("user_agent")