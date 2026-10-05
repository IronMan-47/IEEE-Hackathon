import os

for r, d, files in os.walk('agent/execution'):
    for f in files:
        if not f.endswith('.py'): continue
        path = os.path.join(r, f)
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        new_content = content.replace('get("tokenId"', 'get("token_id"')
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(new_content)
                print(f"Fixed {path}")
