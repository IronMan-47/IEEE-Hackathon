"""
JARVIS Python Agent Core — Phase 9 Proposal Generator & Acceptance Engine
Translates validated plans into structured proposals and handles human proposal modifications and sign-off.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from agent.intent.models import Plan, UserRequest
from agent.context.relevance_filter import RelevantContext
from agent.proposals.models import (
    Proposal,
    ProposalOperation,
    ProposalStatus,
    RiskLevel
)
from agent.proposals.validator import ProposalValidator
from agent.core.logging import logger


class ProposalGenerator:
    @classmethod
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
            from agent.context.workspace_context import WorkspaceContextModel
            ws_ctx = WorkspaceContextModel({"revision": context.workspace_revision, "elements": context.extracted_fields, "activeAppDomain": context.active_app_domain})
            success, raw_prop, err = provider.generate_proposal(ws_ctx, user_req_text or plan.goal.primary_goal, plan)
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
            "plan_id": plan.plan_id,
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
            base_revision=context.workspace_revision,
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

        return proposal

    @classmethod
    def modify_proposal(
        cls,
        original_proposal: Proposal,
        modified_operations: List[ProposalOperation],
        context: RelevantContext,
        user_reason: Optional[str] = None
    ) -> Proposal:
        # Leave original immutable
        original_proposal.status = ProposalStatus.MODIFIED

        child_proposal = Proposal(
            proposal_id=f"prop_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}",
            request_id=original_proposal.request_id,
            plan_id=original_proposal.plan_id,
            domain=original_proposal.domain,
            base_context_id=original_proposal.base_context_id,
            base_context_hash=original_proposal.base_context_hash,
            base_revision=original_proposal.base_revision,
            title=f"Modified: {original_proposal.title}",
            summary=user_reason or f"Human modified parameters of proposal {original_proposal.proposal_id}",
            reason=original_proposal.reason,
            operations=modified_operations,
            constraints=original_proposal.constraints,
            risk=RiskLevel.LOW,
            status=ProposalStatus.DRAFT,
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            source="HUMAN_MODIFIED",
            parent_proposal_id=original_proposal.proposal_id,
            version=original_proposal.version + 1,
            trace=original_proposal.trace
        )

        valid, err = ProposalValidator.validate(child_proposal, context)
        if not valid:
            raise ValueError(f"Modified proposal failed validation: {err}")

        child_proposal.status = ProposalStatus.READY_FOR_REVIEW
        logger.info(f"Created modified child proposal [{child_proposal.proposal_id}] (Parent: {original_proposal.proposal_id})")
        return child_proposal

    @classmethod
    def accept_proposal(
        cls,
        proposal: Proposal,
        context: RelevantContext
    ) -> Tuple[Proposal, Dict[str, Any]]:
        if proposal.is_stale(context.context_hash):
            proposal.status = ProposalStatus.STALE
            raise ValueError("Cannot accept STALE proposal: Context snapshot hash has changed.")

        if proposal.is_expired():
            proposal.status = ProposalStatus.EXPIRED
            raise ValueError("Cannot accept EXPIRED proposal: Expiration limit (5 mins) exceeded.")

        proposal.status = ProposalStatus.ACCEPTED

        # Reusing Phase 4 Approval Token Contract
        from agent.execution.authorization import auth_service
        approval_token = auth_service.generate_token(proposal)

        logger.info(f"Proposal [{proposal.proposal_id}] ACCEPTED. Issued ApprovalToken [{approval_token.get('token_id')}]. NO EXECUTION PERFORMED.")
        return proposal, approval_token

