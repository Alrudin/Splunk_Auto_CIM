from pydantic import BaseModel
from typing import Dict, Optional, List

class PropsConf(BaseModel):
    sourcetype: str
    evals: Dict[str, str]
    extracts: Dict[str, str]
    lookups: Dict[str, str]

class TransformsConf(BaseModel):
    transforms: Dict[str, Dict[str, str]]

class TagsConf(BaseModel):
    tags: Dict[str, List[str]]
