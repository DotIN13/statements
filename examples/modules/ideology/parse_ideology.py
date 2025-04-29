import re
import json

def parse_markdown(markdown_text):
    pattern = (
        r'(.*?)\s*'       # Capture reasoning inside square brackets
        r'---\s*'                          # Separator line with dashes
        r'- \*\*Political Compass Score\*\*: (.*?)\s*'  # Capture score
        r'- \*\*Categorical Label\*\*: ([\w-]+)\s*'             # Capture label
    )
    
    match = re.search(pattern, markdown_text.strip(), re.DOTALL)
    
    if match:
        reasoning, score, label = match.groups()
        score = score.split()[0]  # Extract the first part of the score
        score = (
            float(score)
            if score and score not in ['NA', 'na', 'Na', 'n/a', 'N/A']
            else None
        )
        
        return {
            "score": score,
            "label": label.lower(),
            "reasoning": reasoning.strip()
        }
    
    raise ValueError(f"Markdown format is incorrect: {markdown_text}")

# Example markdown input
if __name__ == "__main__":
    markdown_text = """
```markdown
Reasoning:

- **Potentially Biased Coverage**:
  - Mentions of celebrities (e.g., Dick Van Dyke, Cher) evacuating could subtly emphasize the impact on affluent communities, potentially resonating with left-wing critiques of wealth inequality or climate injustice.
  - The inclusion of Southern California Edison’s role in the 2018 Woolsey Fire (linked to corporate infrastructure) might imply criticism of corporate accountability, aligning with progressive environmental regulation advocacy.
  - Quotations from residents focus on personal loss and emotional trauma (e.g., pet bunnies dying, fleeing in pajamas), evoking sympathy but not overtly partisan language.

- **Alignment with US Political Ideologies**:
  - Left-wing perspectives in the 2020s often emphasize climate change as a driver of wildfires and advocate for stricter utility regulations (e.g., Green New Deal). The article’s mention of preemptive power shutoffs and Edison’s past liability aligns with these concerns.
  - Right-wing narratives might downplay climate change’s role in wildfires and emphasize individual preparedness or criticize government overreach (e.g., power shutoffs disrupting lives). The article avoids this framing, focusing on firefighters’ efforts and community resilience.
  - The neutral tone on the fire’s cause (no explicit blame on climate change or arson) and balanced inclusion of utility spokesperson statements (e.g., “significant progress”) avoid overt partisanship.

- **Overall Assessment**:
  - The article leans slightly left due to its implicit emphasis on corporate accountability (Edison’s past role) and humanizing stories of displacement, which align with progressive priorities. However, it avoids explicit advocacy or partisan language, maintaining factual reporting.

---

- **Political Compass Score**: -0.3 (Slight left-center tilt due to thematic alignment with climate/regulatory concerns but no overt ideological framing)
- **Categorical Label**: left-center
```
    """
    
    parsed_json = parse_markdown(markdown_text)
    print(json.dumps(parsed_json, indent=2))
