from __future__ import annotations
from typing import Optional, Sequence
from dataclasses import dataclass, field
from urllib.parse import urljoin

def asset_url(url, asset):
    if asset == None: return None
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
    repo: Optional[Repo] = None

    @classmethod
    def from_json(cls, data: dict, url: str, repo: Optional[Repo] = None):
        return cls(
            *(data.get(key) for key in ('name', 'bundleid', 'author', 'description', 'long_description', 'version')),
            *(asset_url(url, data.get(asset)) for asset in ('icon', 'banner', 'path')),
            [asset_url(url, s) for s in data.get('screenshots', [])],
            data.get('varOnly', False), repo
            )
    
    def __str__(self) -> str:
        return self.bundleid or super.__str__(self)

@dataclass
class FeaturedEntry:
    name: Optional[str] = None
    bundleid: Optional[str] = None
    fontcolor: Optional[str] = None
    showname: bool = True
    square: bool = False
    banner: Optional[str] = None
    tweak_pair: Optional[Tweak] = None

    @classmethod
    def from_json(cls, data: dict, url: str, obj: Optional[Repo | Tweak] = None):
        t = obj if isinstance(obj, Tweak) else None
        if isinstance(obj, Repo) and data.get('bundleid'):
            t = obj.featured_pair(data.get('bundleid'))
        return cls(*(data.get(key) for key in ('name', 'bundleid', 'fontcolor', 'showname', 'square')), asset_url(url, data.get('banner')), t)

    def __str__(self) -> str:
        return self.bundleid or super.__str__(self)

@dataclass
class Repo:
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    url: Optional[str] = None
    packages: dict[str, Tweak] = field(default_factory=dict)
    featured: Sequence[FeaturedEntry] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict, url: str, convert_featured=True):
        c = cls(
            *(data.get(key) for key in ('name','description')),
            asset_url(url, data.get('icon')), url
            )
        for json in data.get('packages', ()):
            tweak = Tweak.from_json(json, url, c)
            if not tweak.bundleid:
                tweak.bundleid = "org.example.unknown"
            if tweak.bundleid in c.packages:
                i = 0
                while f'{tweak.bundleid}{i}' in c.packages:
                    i+=1
                tweak.bundleid = f'{tweak.bundleid}{i}'
            c.packages[tweak.bundleid] = tweak

        c.featured = [FeaturedEntry.from_json(json, url, c) for json in data.get('featured', ())]
        return c

    def featured_pair(self, obj: FeaturedEntry | str) -> Optional[Tweak]:
        bundleid = obj
        if isinstance(obj, FeaturedEntry):
            bundleid = obj.bundleid
        return self.packages.get(bundleid)