import re
import json

def parse_markdown(markdown_text):
    pattern = (
        r"([\s\S]+?)\n---\s*"  # Extracts the reasoning section
        r"- \**Logit Scores\**:\s*\n"
        r"\s*- \**Left\**: ([\d\.\-]+)\s*\n"
        r"\s*- \**Left-Center\**: ([\d\.\-]+)\s*\n"
        r"\s*- \**Center\**: ([\d\.\-]+)\s*\n"
        r"\s*- \**Center-Right\**: ([\d\.\-]+)\s*\n"
        r"\s*- \**Right\**: ([\d\.\-]+)\s*\n"
        r"- \**Softmax Probabilities\**:\s*\n"
        r"\s*- \**Left\**: ([\d\.\-]+)%\s*\n"
        r"\s*- \**Left-Center\**: ([\d\.\-]+)%\s*\n"
        r"\s*- \**Center\**: ([\d\.\-]+)%\s*\n"
        r"\s*- \**Center-Right\**: ([\d\.\-]+)%\s*\n"
        r"\s*- \**Right\**: ([\d\.\-]+)%\s*\n"
        r"- \**Categorical Label\**: ([\w-]+)"
    )

    match = re.search(pattern, markdown_text.strip())

    if match:
        reasoning = match.group(1).strip()
        logit_scores = {
            "Left": float(match.group(2)),
            "Left-Center": float(match.group(3)),
            "Center": float(match.group(4)),
            "Center-Right": float(match.group(5)),
            "Right": float(match.group(6))
        }
        softmax_probabilities = {
            "Left": float(match.group(7)) / 100.0,
            "Left-Center": float(match.group(8)) / 100.0,
            "Center": float(match.group(9)) / 100.0,
            "Center-Right": float(match.group(10)) / 100.0,
            "Right": float(match.group(11)) / 100.0
        }
        categorical_label = match.group(12)

        return {
            "reasoning": reasoning,
            "logit_scores": logit_scores,
            "softmax_probabilities": softmax_probabilities,
            "label": categorical_label
        }

    raise ValueError(f"Markdown format is incorrect: {markdown_text}")

# Example markdown input
if __name__ == "__main__":
    markdown_text = """
```markdown
Reasoning:

- The article focuses on sports governance controversies (playoff selection criteria) without explicit references to political policies or ideologies.
- Neutral reporting of committee decisions and coach reactions ("presumably deserving Alabama," "strength of schedule" debates) avoids overt ideological framing.
- No mention of partisan issues (e.g., taxation, social policies) or alignment with progressive/conservative agendas.
- Critiques of playoff structure fairness ("strange" byes, "no reseeding") relate to sports logistics rather than political values.
- Quotes from stakeholders (SMU coach, committee chair) present balanced perspectives without advocacy for specific ideologies.

The article avoids partisan alignment by strictly discussing athletic competition mechanics. Its focus on procedural fairness in sports governance lacks direct ties to US left/right policy positions, necessitating a neutral classification.

---

- **Logit Scores**:
  - **Left**: -1.2
  - **Left-Center**: -0.5
  - **Center**: 2.8
  - **Center-Right**: -0.6
  - **Right**: -1.3

- **Softmax Probabilities**:
  - **Left**: 3.47%
  - **Left-Center**: 10.21%
  - **Center**: 76.32%
  - **Center-Right**: 9.56%
  - **Right**: 0.44%

- **Categorical Label**: center
```
"""

    parsed_json = parse_markdown(markdown_text)
    print(json.dumps(parsed_json, indent=2))
