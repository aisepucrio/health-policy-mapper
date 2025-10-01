from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any


class ColumnInput(BaseModel):
    name: str = Field(..., description="The field name to extract")
    description: str = Field("", description="A brief description of this field")

    @field_validator('name')
    def name_not_empty(cls, v: str):
        if not v.strip():
            raise ValueError("Column name cannot be empty")
        return v


class JobCreatedResponse(BaseModel):
    job_id: str = Field(..., description="UUID of the created job")


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    files_processed: int
    total_files: int
    error_count: int = 0
    error_message: Optional[str] = None


class RawRow(BaseModel):
    # Dynamic columns unknown at design time; keep flexible
    source_file: str
    error: Optional[str] = None
    # Additional extracted columns go into arbitrary dict entries
    class Config:
        extra = 'allow'


class RawIncrementalResponse(BaseModel):
    total_rows: int
    rows_returned: int
    since: Optional[int]
    rows: List[RawRow]


class ResumeResponse(BaseModel):
    job_id: str
    status: str


class AggregateMetaResponse(BaseModel):
    aggregated_rows: int = Field(..., description="Number of aggregated rows returned in CSV")
