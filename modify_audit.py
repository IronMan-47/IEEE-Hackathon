import re

with open(r'c:\Users\lenovo\OneDrive\Desktop\Hackathons\Jarvis - Living Assistent\agent\tasks\audit.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    (r'logger\.info\(\s*f"AUDIT EVENT \[TASK_CREATED\]', "_emit_runtime_event('TASK_CREATED', task)\n        logger.info(\n            f\"AUDIT EVENT [TASK_CREATED]"),
    (r'logger\.info\(\s*f"AUDIT EVENT \[TASK_STEP_PROPOSED\]', "_emit_runtime_event('TASK_STEP_PROPOSED', task, {}, step)\n        logger.info(\n            f\"AUDIT EVENT [TASK_STEP_PROPOSED]"),
    (r'logger\.info\(\s*f"AUDIT EVENT \[TASK_STEP_APPROVED\]', "_emit_runtime_event('TASK_STEP_APPROVED', task, {'token_id': token_id}, step)\n        logger.info(\n            f\"AUDIT EVENT [TASK_STEP_APPROVED]"),
    (r'logger\.info\(\s*f"AUDIT EVENT \[TASK_STEP_EXECUTED\]', "_emit_runtime_event('TASK_STEP_EXECUTED', task, {'execution_id': exec_id, 'status': status}, step)\n        logger.info(\n            f\"AUDIT EVENT [TASK_STEP_EXECUTED]"),
    (r'logger\.info\(\s*f"AUDIT EVENT \[TASK_STEP_VERIFIED\]', "_emit_runtime_event('TASK_STEP_VERIFIED', task, {'result': result}, step)\n        logger.info(\n            f\"AUDIT EVENT [TASK_STEP_VERIFIED]"),
    (r'logger\.info\(\s*f"AUDIT EVENT \[TASK_REASSESSED\]', "_emit_runtime_event('TASK_REASSESSED', task, {'context_hash': context_hash})\n        logger.info(\n            f\"AUDIT EVENT [TASK_REASSESSED]"),
    (r'logger\.info\(\s*f"AUDIT EVENT \[TASK_REPLANNED\]', "_emit_runtime_event('TASK_REPLANNED', task, {'replan_count': replan_count})\n        logger.info(\n            f\"AUDIT EVENT [TASK_REPLANNED]"),
    (r'logger\.info\(f"AUDIT EVENT \[TASK_COMPLETED\]', "_emit_runtime_event('TASK_COMPLETED', task)\n        logger.info(f\"AUDIT EVENT [TASK_COMPLETED]"),
    (r'logger\.warning\(f"AUDIT EVENT \[TASK_BLOCKED\]', "_emit_runtime_event('TASK_BLOCKED', task, {'reason': reason})\n        logger.warning(f\"AUDIT EVENT [TASK_BLOCKED]"),
    (r'logger\.error\(f"AUDIT EVENT \[TASK_FAILED\]', "_emit_runtime_event('TASK_FAILED', task, {'error': error})\n        logger.error(f\"AUDIT EVENT [TASK_FAILED]"),
    (r'logger\.info\(f"AUDIT EVENT \[TASK_PAUSED\]', "_emit_runtime_event('TASK_PAUSED', task)\n        logger.info(f\"AUDIT EVENT [TASK_PAUSED]"),
    (r'logger\.info\(f"AUDIT EVENT \[TASK_CANCELLED\]', "_emit_runtime_event('TASK_CANCELLED', task)\n        logger.info(f\"AUDIT EVENT [TASK_CANCELLED]"),
]

for old, new in replacements:
    content = re.sub(old, new, content)

with open(r'c:\Users\lenovo\OneDrive\Desktop\Hackathons\Jarvis - Living Assistent\agent\tasks\audit.py', 'w', encoding='utf-8') as f:
    f.write(content)
