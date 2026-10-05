import re

target_file = r"c:\Users\lenovo\OneDrive\Desktop\Hackathons\Jarvis - Living Assistent\agent\reasoning\planner.py"
with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

new_generate_steps = '''    def _generate_steps(
        self,
        user_req: UserRequest,
        context: RelevantContext,
        intent: Intent,
        goal: Goal
    ) -> List[PlanStep]:
        target_name = intent.target.name or "active workspace"
        
        fallback_steps = [
            PlanStep(
                id="step_1",
                type=PlanStepType.OBSERVE,
                description=f"Gather perception metadata and context snapshot for {target_name}",
                target_id=target_name,
                reason="Establish baseline context"
            ),
            PlanStep(
                id="step_2",
                type=PlanStepType.ANALYZE,
                description=f"Analyze user request '{user_req.text}' against target state",
                reason="Identify requirements and potential constraints"
            ),
            PlanStep(
                id="step_3",
                type=PlanStepType.PROPOSE,
                description=f"Prepare candidate plan and strategy proposal",
                reason="Structure solution for human evaluation"
            ),
            PlanStep(
                id="step_4",
                type=PlanStepType.VERIFY,
                description=f"Verify alignment with user goal and safety policies",
                reason="Confirm plan safety before presenting to user"
            )
        ]
        
        if self.provider:
            # We must map context to WorkspaceContextModel for provider
            from agent.context.workspace_context import WorkspaceContextModel
            ws_ctx = WorkspaceContextModel({"activeAppDomain": context.active_app_domain, "activeFile": context.active_file, "elements": context.elements})
            success, plan_dict, err = self.provider.generate_plan(ws_ctx, user_req.text)
            if success and plan_dict and "steps" in plan_dict:
                steps = []
                for s in plan_dict["steps"]:
                    steps.append(PlanStep(
                        id=s.get("id", "step_1"),
                        type=s.get("type", "PROPOSE"),
                        description=s.get("description", "Generated step"),
                        target_id=s.get("target_id", target_name),
                        reason=s.get("reason", "")
                    ))
                return steps
                
        return fallback_steps'''

content = re.sub(r'    def _generate_steps\(.*?\]', new_generate_steps, content, flags=re.DOTALL)

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)
