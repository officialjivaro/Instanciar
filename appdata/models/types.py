# appdata/model/types.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass(slots=True)
class ProxyConf:
    ip: str
    port: str
    protocol: str
    auth: bool = False
    user: Optional[str] = None
    password: Optional[str] = None

@dataclass(slots=True)
class Instance:
    name: str
    folder_id: str
    proxy: Optional[ProxyConf] = None
    group: str = "Unassigned"
    hwid: Dict = field(default_factory=dict)
    identity: Dict = field(default_factory=dict)

@dataclass(slots=True)
class Group:
    name: str
