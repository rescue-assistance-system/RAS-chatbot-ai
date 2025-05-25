import os
import re


def extract_section(content: str, heading: str) -> str:
    """
    Extract a section from markdown based on the heading.
    """
    pattern = rf"##+\s*{re.escape(heading)}\s*\n(.*?)(?=\n##|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ""


def read_ras_info_md():
    file_path = os.path.join("public", "rescue_system_description.md")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        parsed = {
            "ras_info": extract_section(content, "1. What is RAS?"),
            "ras_usage": extract_section(content, "3. How to Use RAS"),
            "ras_features": extract_section(content, "4. Key Features"),
            "ras_target": extract_section(content, "5. Who Is RAS For?"),
        }

        return parsed
    except Exception as e:
        return {"error": f"Error reading RAS info: {e}"}
