from typing import List
from domain.value_objects.column import Column

TEMPLATE = """
You are an AI assistant tasked with extracting structured data from the provided document text.

**Context:**
{context}

**Fields to extract:**
{fields_block}

For each field listed above, determine:
  1. `value` – the extracted value (string) or "not specified".
  2. `justification` – a brief reference to where you found it (e.g. "Page 4, paragraph 2") or "not found".

**Document to process:**
{file_name}

**Important**
Output a single JSON object with one key per field, where each key maps to an object with `value` and `justification`.
For the 'Country' field: If the document clearly applies to more than one country, list all relevant country names, separated by comma (e.g., "Austria, Germany") in its value key.
For the 'Country Alpha-3 Code' field: If the document clearly applies to more than one country, list all corresponding alpha-3 codes separated by comma (e.g., "AUT, DEU") in its value key.
Do **not** output any additional text.
You **can** extract information from the document name.
Always return the 'justification' field even if the value is "not found".
The alpha-3 code for brazil is BRA.
"""

def build_prompt(context: str, columns: List[Column], file_name: str) -> str:
    """
    Build the prompt for the LLM given the context and columns. It will add a justification field for each column.
    """
    lines = []
    for col in columns:
        d = col.to_dict()
        lines.append(f"- **{d['name']}**: {d['description']}")
    fields_block = "\n".join(lines)
    return TEMPLATE.format(context=context.strip(), fields_block=fields_block, file_name=file_name)
