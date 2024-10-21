from math import e
from typing import Optional, Sequence
from dataclasses import dataclass
from urllib.parse import urljoin

def asset_url(url, asset):
    return urljoin(url, asset) or None

@dataclass
class Tweak:
    name: Optional[str]
    bundleid: Optional[str]
    author: Optional[str]
    description: Optional[str]
    long_description: Optional[str]
    version: Optional[str]
    icon: Optional[str]
    banner: Optional[str]
    path: Optional[str]
    screenshots: Sequence[str]
    varOnly: bool

    @classmethod
    def from_json(cls, data: dict, url: str):
        return cls(
            *(data.get(key) for key in ('name', 'bundleid', 'author', 'description', 'long_description', 'version')),
            *(asset_url(url, data.get(asset)) for asset in ('icon', 'banner', 'path')),
            data.get('screenshots', []),
            data.get('varOnly', False)
            )

@dataclass
class BaseRepo:
    name: Optional[str]
    description: Optional[str]
    icon: Optional[str]
    packages: Sequence[Tweak]
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