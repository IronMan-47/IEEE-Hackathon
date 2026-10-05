import re
import os

target_file = r"c:\Users\lenovo\OneDrive\Desktop\Hackathons\Jarvis - Living Assistent\agent\proposals\generator.py"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# Replace generate_from_plan
new_generate_from_plan = '''    @classmethod
    def generate_from_plan(
        cls,
        plan: Plan,
        context: RelevantContext,
        user_req_text: Optional[str] = None,
        provider: Optional[Any] = None
    ) -> Proposal:
        domain = context.active_app_domain.lower()
        if domain not in ["living_canvas", "vscode", "browser", "terminal", "figma"]:
            domain = "living_canvas"

        target_name = plan.goal.target.value if hasattr(plan.goal.target, "value") else str(plan.goal.target)
        target_id = context.active_file or "active_target"
        
        operations = []
        title = f"Proposal for {plan.goal.primary_goal}"
        summary = f"Structured strategy payload targeting {target_id} under {domain.upper()} domain context."
        
        if provider:
            success, raw_prop, err = provider.generate_proposal(context, user_req_text or plan.goal.primary_goal, plan)
            if success and raw_prop:
                if "operations" in raw_prop:
                    for i, op_dict in enumerate(raw_prop.get("operations", [])):
                        operations.append(ProposalOperation(
                            operation_id=f"op_{i+1}",
                            op_type=op_dict.get("op_type", op_dict.get("op", "UPDATE_STYLE")),
                            target=op_dict.get("target", op_dict.get("targetId", target_id)),
                            parameters=op_dict.get("parameters", op_dict.get("proposedValue", {})),
                            reason=op_dict.get("reason", f"AI proposed operation {i+1}"),
                            risk=RiskLevel.LOW
                        ))
                title = raw_prop.get("title", title)
                summary = raw_prop.get("reason", summary)
        else:
            # Fallback when no provider is passed (shouldn't happen now, but MockProvider handles mock generation)
            operations = [ProposalOperation(
                operation_id="op_1",
                op_type="UPDATE_STYLE",
                target=target_id,
                parameters={"style": {"fontWeight": "bold"}},
                reason="Default visual prominence update proposal",
                risk=RiskLevel.LOW
            )]

        trace = {
            "request_text": user_req_text or "User request",
            "intent_type": plan.intent.value if hasattr(plan.intent, "value") else str(plan.intent),
            "goal_primary": plan.goal.primary_goal,
            "domain_target": domain,
            "provider_used": bool(provider)
        }

        proposal = Proposal(
            request_id=plan.request_id,
            plan_id=plan.plan_id,
            domain=domain,
            base_context_id=context.context_id,
            base_context_hash=context.context_hash,
            base_revision=context.revision,
            title=title,
            summary=summary,
            reason=f"Derived dynamically from plan reasoning: {plan.reasoning_summary}",
            operations=operations,
            constraints=plan.constraints,
            risk=RiskLevel.LOW,
            status=ProposalStatus.DRAFT,
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            source="AI",
            version=1,
            trace=trace
        )

        return proposal'''

content = re.sub(r'    @classmethod\n    def generate_from_plan\(.*?\n        return proposal', new_generate_from_plan, content, flags=re.DOTALL)

# Delete _build_operations_for_domain completely
content = re.sub(r'    @classmethod\n    def _build_operations_for_domain\(.*', '', content, flags=re.DOTALL)

with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)
