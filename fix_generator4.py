import re

target_file = r"c:\Users\lenovo\OneDrive\Desktop\Hackathons\Jarvis - Living Assistent\agent\proposals\generator.py"
with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

new_code = '''        if provider:
            from agent.context.workspace_context import WorkspaceContextModel
            ws_ctx = WorkspaceContextModel({"revision": context.workspace_revision, "elements": context.extracted_fields, "activeAppDomain": context.active_app_domain})
            success, raw_prop, err = provider.generate_proposal(ws_ctx, user_req_text or plan.goal.primary_goal, plan)'''

content = re.sub(r'        if provider:\n            from agent.context.workspace_context import WorkspaceContextModel\n            ws_ctx = WorkspaceContextModel\({"revision": context.workspace_revision, "elements": context.extracted_fields}\)\n            success, raw_prop, err = provider.generate_proposal\(ws_ctx, user_req_text or plan.goal.primary_goal, plan\)', new_code, content, flags=re.DOTALL)

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)
