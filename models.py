from typing import Optional, Sequence
from dataclasses import dataclass, field
from urllib.parse import urljoin

def asset_url(url, asset):
    return urljoin(url, asset) or None

@dataclass
class Tweak:
    name: Optional[str] = None
    bundleid: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    long_description: Optional[str] = None
    version: Optional[str] = None
    icon: Optional[str] = None
    banner: Optional[str] = None
    path: Optional[str] = None
    screenshots: Sequence[str] = field(default_factory=list)
    varOnly: bool = True

    @classmethod
    def from_json(cls, data: dict, url: str):
        return cls(
            *(data.get(key) for key in ('name', 'bundleid', 'author', 'description', 'long_description', 'version')),
            *(asset_url(url, data.get(asset)) for asset in ('icon', 'banner', 'path')),
            [asset_url(url, s) for s in data.get('screenshots', [])],
            data.get('varOnly', False)
            )

@dataclass
class BaseRepo:
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    packages: Sequence[Tweak] = field(default_factory=list)
    # TODO: featured

    @classmethod
    def from_json(cls, data: dict, url: str):
        return cls(
            *(data.get(key) for key in ('name','description')),
            asset_url(url, data.get('icon')),
            [Tweak.from_json(json, url) for json in data.get('packages', ())]
            )
    
    def load(self):
        raise NotImplementedError("loading a repo not implemented in dataclass")