import json
import re
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage


# --------------------------------------------------
# LLM ENTITY PARSER
# --------------------------------------------------
async def llm_parse_entity(llm, user_input: str) -> Dict[str, Any]:
    system = SystemMessage(
        content=(
            "You are an intent parser.\n"
            "Extract the main person or topic from the user input.\n"
            "Return ONLY JSON.\n\n"
            "Format:\n"
            "{\n"
            '  "entity": "...",\n'
            '  "aliases": ["...", "..."]\n'
            "}"
        )
    )

    human = HumanMessage(
        content=f'User input: "{user_input}"'
    )

    response = await llm.ainvoke([system, human])
    text = response.content.strip()

    
    print("\n🧠 RAW LLM OUTPUT:\n", text)

    
    try:
        return json.loads(text)
    except Exception:
        pass

    
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    
    raise ValueError(f"LLM returned invalid JSON:\n{text}")


# --------------------------------------------------
# TWITTER SEARCH QUERY BUILDER
# --------------------------------------------------
def build_query_from_entity(entity_data: Dict[str, Any]) -> str:
    aliases = entity_data.get("aliases", [])

    if not aliases:
        raise ValueError("No aliases found for search")

    terms = []

    for alias in aliases:
        alias = alias.strip()
        if len(alias) < 3:
            continue

        terms.append(f'"{alias}"')
        terms.append(f'#{alias.replace(" ", "")}')

    if not terms:
        raise ValueError("Query too weak after processing")

    query = " OR ".join(set(terms))
    return f"({query}) -is:retweet"


# --------------------------------------------------
# USERNAME EXTRACTION (TIMELINE)
# --------------------------------------------------
def extract_username(text: str) -> str | None:
    text = text.lower()

    
    match = re.search(r"@([a-zA-Z0-9_]{1,15})", text)
    if match:
        return match.group(1)

    
    match = re.search(r"(?:by|from)\s+([a-zA-Z0-9_ ]+)", text)
    if match:
        candidate = match.group(1).strip()

        
        candidate = re.split(
            r"\s+(about|on|regarding|latest|recent)",
            candidate
        )[0]

        return candidate.replace(" ", "")

    return None


# --------------------------------------------------
# SAFE JSON LOADER (OPTIONAL UTILITY)
# --------------------------------------------------
def safe_json_load(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        raise ValueError(f"Invalid JSON:\n{text}")



