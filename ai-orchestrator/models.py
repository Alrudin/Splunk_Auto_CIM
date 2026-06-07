from pydantic import BaseModel, Field
from typing import List, Dict

class PropsExtraction(BaseModel):
    name: str = Field(description="Name of the extraction, e.g., src_ip")
    regex: str = Field(description="Regular expression to extract the field")

class PropsEval(BaseModel):
    name: str = Field(description="Name of the eval field, e.g., action")
    expression: str = Field(description="Eval expression, e.g., if(status==200, \"success\", \"failure\")")

class PropsConf(BaseModel):
    extractions: List[PropsExtraction] = Field(default_factory=list, description="List of EXTRACT statements")
    evals: List[PropsEval] = Field(default_factory=list, description="List of EVAL statements")
    rename_fields: Dict[str, str] = Field(default_factory=dict, description="FIELDALIAS statements mapping original to CIM field")

class GenerationOutput(BaseModel):
    props: PropsConf
    tags: List[str] = Field(default_factory=list, description="List of tags for this sourcetype, e.g., ['network', 'communicate']")
