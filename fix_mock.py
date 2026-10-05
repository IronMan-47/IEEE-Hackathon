import re

target_file = r"c:\Users\lenovo\OneDrive\Desktop\Hackathons\Jarvis - Living Assistent\agent\llm\mock_provider.py"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

new_ops = '''        operations = [
            {
                "op_type": "UPDATE_STYLE",
                "target": "btn_pay",
                "parameters": {
                    "w": 320,
                    "style": {
                        "fill": "#06B6D4",
                        "fontWeight": "bold"
                    }
                },
                "reason": "Enlarge Pay Now CTA button width (180px -> 320px) and apply cyan fill for visual prominence."
            }
        ]'''

content = re.sub(r'        operations = \[.*?\]', new_ops, content, flags=re.DOTALL)

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)
