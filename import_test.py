import sys
import os

sys.path.insert(0, os.path.abspath('.'))

errors = []
try:
    from agent.main import main
except Exception as e:
    errors.append(f"main.py: {e}")

try:
    from agent.transport.api import app
except Exception as e:
    errors.append(f"api.py: {e}")

try:
    from agent.core.config import config
except Exception as e:
    errors.append(f"config.py: {e}")

try:
    import agent.runtime.lifecycle
except Exception as e:
    errors.append(f"runtime/lifecycle.py: {e}")

try:
    from agent.core.agent import JarvisAgent
except Exception as e:
    errors.append(f"JarvisAgent: {e}")

if not errors:
    print("All imports successful.")
else:
    for err in errors:
        print(f"IMPORT ERROR: {err}")
