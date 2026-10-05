import os
import re

def rewrite_tests():
    for root, _, files in os.walk('tests/python'):
        for file in files:
            if not file.endswith('.py'): continue
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            original = content

            # Add import
            if "from agent.execution.authorization import auth_service" not in content:
                content = "from agent.execution.authorization import auth_service\n" + content

            # Find all instances of ExecutionRequest(...)
            # We want to replace `approval_token=...` inside ExecutionRequest with `approval_token=auth_service.generate_token(proposal)`
            # Since `proposal` is usually available in the test body as `proposal`.
            content = re.sub(r'approval_token\s*=\s*[^,]+,', 'approval_token=auth_service.generate_token(proposal),', content)
            # If it's at the end of the argument list:
            content = re.sub(r'approval_token\s*=\s*[^\)]+\)', 'approval_token=auth_service.generate_token(proposal))', content)

            if content != original:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated {path}")

rewrite_tests()
