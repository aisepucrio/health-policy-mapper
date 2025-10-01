import json
from typing import List
from fastapi import HTTPException

from presentation.schema import ColumnInput
from domain.value_objects.column import Column


def parse_columns_payload(raw: str) -> List[Column]:
    """Parse and validate the JSON list of columns using ColumnInput + VO Column."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid columns JSON: {e}")
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Columns payload must be a JSON list")
    inputs: List[ColumnInput] = []
    for idx, item in enumerate(data, start=1):
        try:
            inputs.append(ColumnInput(**item))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid column at index {idx}: {e}")
    domain_columns: List[Column] = []
    for idx, ci in enumerate(inputs, start=1):
        try:
            domain_columns.append(Column(name=ci.name, description=ci.description))
        except Exception as vo_err:
            raise HTTPException(status_code=400, detail=f"Invalid column at index {idx} (name={ci.name!r}): {vo_err}")
    # detect duplicates after normalization
    seen = set()
    dups = set()
    for c in domain_columns:
        if c.name in seen:
            dups.add(c.name)
        seen.add(c.name)
    if dups:
        raise HTTPException(status_code=400, detail=f"Duplicate column names: {sorted(dups)}")
    return domain_columns
