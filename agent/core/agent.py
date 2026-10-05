"""
JARVIS Python Agent Core — Central Agent Orchestrator with Phase 10 Controlled Execution Pipeline
"""

from typing import Dict, Any, Optional, Tuple, List
from agent.core.types import AgentRequest, AgentResponse, IntentCategory
from agent.context.workspace_context import WorkspaceContextModel
from agent.intent.models import (
    UserRequest,
    RequestNormalizer,
    Intent,
    Goal,
    Constraint,
    Plan,
    PlanStep,
    ClarificationRequest
)
from agent.proposals.models import Proposal, ProposalOperation, ProposalStatus
from agent.proposals.generator import ProposalGenerator
from agent.proposals.validator import ProposalValidator
from agent.execution.models import ExecutionRequest, ExecutionResult, ExecutionStatus
from agent.execution.living_canvas_executor import LivingCanvasExecutor
from agent.execution.domain_router import DomainRouter
from agent.context.relevance_filter import ContextRelevanceFilter, RelevantContext
from agent.intent.classifier import IntentClassifier
from agent.intent.goal_extractor import GoalExtractor
from agent.reasoning.planner import Planner
from agent.reasoning.proposal_generator import ProposalGenerator as Phase3ProposalGenerator
from agent.proposals.sanitizer import ProposalSanitizer
from agent.core.logging import logger
from agent.perception.visual.gemini_provider import GeminiVisionProvider
from agent.perception.visual.mock_provider import MockVisionProvider
from agent.perception.visual.models import VisualContext
from agent.perception.types import PerceptionResult
from agent.context.fusion.resolver import ContextResolver
from agent.context.fusion.models import GroundedContext


class JarvisAgent:
    def __init__(self, provider: Optional[Any] = None, vision_provider: Optional[Any] = None):
        self.provider = provider
        self.vision_provider = vision_provider or GeminiVisionProvider()
        self.intent_classifier = IntentClassifier()
        self.planner = Planner(provider=provider)
        self.proposal_generator = Phase3ProposalGenerator(provider=provider)
        self.living_canvas_executor = LivingCanvasExecutor()
        self.domain_router = DomainRouter()
        self.is_system_ready: bool = True
        self.current_visual_context: Optional[VisualContext] = None
        self.current_grounded_context: Optional[GroundedContext] = None

    def analyze_visual_screen(
        self,
        perception_result: PerceptionResult,
        scenario: Optional[str] = None
    ) -> VisualContext:
        vctx = self.vision_provider.analyze_screen(perception_result, scenario=scenario)
        self.current_visual_context = vctx
        logger.info(f"AUDIT EVENT [VISUAL_PERCEPTION_ANALYZED] ID [{vctx.context_id}]: Hash [{vctx.context_hash[:8]}], Elements [{len(vctx.elements)}]")
        return vctx

    def fuse_context(
        self,
        perception_result: Optional[PerceptionResult] = None,
        application_context: Optional[Dict[str, Any]] = None,
        visual_context: Optional[VisualContext] = None,
        user_text: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> GroundedContext:
        gctx = ContextResolver.fuse(
            perception_result=perception_result,
            application_context=application_context,
            visual_context=visual_context or self.current_visual_context,
            user_text=user_text,
            request_id=request_id
        )
        self.current_grounded_context = gctx
        logger.info(f"AUDIT EVENT [CONTEXT_FUSED] ID [{gctx.context_id}]: Hash [{gctx.context_hash[:8]}], Primary App [{gctx.primary_application.name}], Conflicts [{len(gctx.conflicts)}]")
        return gctx

    def plan_request(
        self,
        raw_text: str,
        perception_context: Optional[Dict[str, Any]] = None,
        workspace_context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Tuple[Optional[Plan], Optional[ClarificationRequest], RelevantContext, Intent, Goal]:
        logger.info(f"AUDIT EVENT [REQUEST_RECEIVED]: Raw prompt length {len(raw_text)}")
        user_req = RequestNormalizer.normalize(raw_text, request_id=request_id)
        logger.info(f"AUDIT EVENT [REQUEST_NORMALIZED] ID [{user_req.id}]: '{user_req.text}'")

        rel_context = ContextRelevanceFilter.filter(perception_context, workspace_context)
        logger.info(f"AUDIT EVENT [CONTEXT_SELECTED] ID [{rel_context.context_id}]: App Domain '{rel_context.active_app_domain}', Active File '{rel_context.active_file}'")

        intent, clarification = self.intent_classifier.classify(user_req, rel_context, provider=self.provider)
        logger.info(f"AUDIT EVENT [INTENT_CLASSIFIED]: Type '{intent.intent_type.value}', Confidence '{intent.confidence.value}', Target '{intent.target.type.value}'")

        if clarification:
            logger.warn(f"AUDIT EVENT [CLARIFICATION_REQUIRED]: Question '{clarification.question}'")
            empty_goal = Goal(primary_goal="Clarification required", success_condition="User specifies missing details")
            return None, clarification, rel_context, intent, empty_goal

        goal, constraints = GoalExtractor.extract(user_req, intent)
        logger.info(f"AUDIT EVENT [GOAL_EXTRACTED]: '{goal.primary_goal}'")
        logger.info(f"AUDIT EVENT [CONSTRAINTS_EXTRACTED]: Count {len(constraints)}")

        plan = self.planner.plan(user_req, rel_context, intent, goal, constraints)
        logger.info(f"AUDIT EVENT [PLAN_CREATED] ID [{plan.plan_id}]: {len(plan.steps)} non-executable steps")
        logger.info(f"AUDIT EVENT [PLAN_VALIDATED]: Status '{plan.status.value}'")

        return plan, None, rel_context, intent, goal

    def generate_proposal_from_plan(
        self,
        plan: Plan,
        perception_context: Optional[Dict[str, Any]] = None,
        workspace_context: Optional[Dict[str, Any]] = None,
        user_req_text: Optional[str] = None
    ) -> Tuple[Proposal, RelevantContext]:
        rel_context = ContextRelevanceFilter.filter(perception_context, workspace_context)
        from agent.proposals.generator import ProposalGenerator
        proposal = ProposalGenerator.generate_from_plan(
            plan=plan,
            context=rel_context,
            user_req_text=user_req_text,
            provider=self.proposal_generator.provider
        )
        logger.info(f"AUDIT EVENT [PROPOSAL_CREATED] ID [{proposal.proposal_id}]: Domain '{proposal.domain}', Risk '{proposal.risk.value}'")
        
        from agent.proposals.validator import ProposalValidator
        valid, err = ProposalValidator.validate(proposal, rel_context)
        if not valid:
            raise ValueError(f"Proposal validation failed: {err}")
            
        logger.info(f"AUDIT EVENT [PROPOSAL_VALIDATED] ID [{proposal.proposal_id}]: Status '{proposal.status.value}'")
        return proposal, rel_context

    def modify_proposal_phase9(
        self,
        original_proposal: Proposal,
        modified_ops: List[ProposalOperation],
        perception_context: Optional[Dict[str, Any]] = None,
        workspace_context: Optional[Dict[str, Any]] = None,
        user_reason: Optional[str] = None
    ) -> Tuple[Proposal, RelevantContext]:
        rel_context = ContextRelevanceFilter.filter(perception_context, workspace_context)
        child_proposal = ProposalGenerator.modify_proposal(original_proposal, modified_ops, rel_context, user_reason=user_reason)
        logger.info(f"AUDIT EVENT [PROPOSAL_MODIFIED]: Parent [{original_proposal.proposal_id}] -> Child [{child_proposal.proposal_id}]")
        return child_proposal, rel_context

    def accept_proposal_phase9(
        self,
        proposal: Proposal,
        perception_context: Optional[Dict[str, Any]] = None,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Proposal, Dict[str, Any], RelevantContext]:
        rel_context = ContextRelevanceFilter.filter(perception_context, workspace_context)
        accepted_proposal, approval_token = ProposalGenerator.accept_proposal(proposal, rel_context)
        logger.info(f"AUDIT EVENT [PROPOSAL_ACCEPTED] ID [{accepted_proposal.proposal_id}]: Token [{approval_token.get('token_id')}]. NO EXECUTION.")
        return accepted_proposal, approval_token, rel_context

    def execute_proposal(
        self,
        exec_request: ExecutionRequest,
        proposal: Proposal,
        perception_context: Optional[Dict[str, Any]] = None,
        workspace_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        rel_context = ContextRelevanceFilter.filter(perception_context, workspace_context)
        logger.info(f"AUDIT EVENT [EXECUTION_REQUESTED] ID [{exec_request.execution_id}]: Proposal [{proposal.proposal_id}], Domain [{proposal.domain}]")

        executor = self.domain_router.get_executor(proposal.domain)
        if not executor:
            logger.warn(f"AUDIT EVENT [EXECUTION_BLOCKED] ID [{exec_request.execution_id}]: Domain '{proposal.domain}' is not supported")
            return ExecutionResult(
                status=ExecutionStatus.BLOCKED,
                execution_id=exec_request.execution_id,
                proposal_id=proposal.proposal_id,
                workspace_id=exec_request.workspace_id,
                previous_revision=exec_request.base_revision,
                new_revision=exec_request.base_revision,
                verification="SKIPPED",
                error=f"UNAVAILABLE: Domain '{proposal.domain}' is not executable. Supported domains: living_canvas, vscode, browser."
            )

        result = executor.execute(
            request=exec_request,
            proposal=proposal,
            context=rel_context,
            workspace_context=workspace_context
        )

        return result

    def modify_plan(self, original_plan: Plan, new_steps: List[PlanStep]) -> Plan:
        logger.info(f"AUDIT EVENT [PLAN_MODIFIED]: Modifying plan [{original_plan.plan_id}] -> New step count {len(new_steps)}")
        return self.planner.modify_plan(original_plan, new_steps)

    def accept_plan(self, plan: Plan) -> Plan:
        logger.info(f"AUDIT EVENT [PLAN_ACCEPTED]: Accepted plan [{plan.plan_id}]")
        return self.planner.accept_plan(plan)

    def handle_request(self, req: AgentRequest) -> AgentResponse:
        logger.info(f"Handling Legacy Agent Request [{req.request_id}]: '{req.text}'")

        context = WorkspaceContextModel(req.workspace_context)
        known_element_ids = list(context.elements.keys())
        text_lower = req.text.lower().strip()

        unsupported_keywords = [
            "delete my computer", "rm -rf", "format c:", "drop table",
            "exec(", "eval(", "system(", "powershell", "cmd.exe", "bash"
        ]
        for kw in unsupported_keywords:
            if kw in text_lower:
                return AgentResponse(
                    request_id=req.request_id,
                    status="UNSUPPORTED",
                    intent=IntentCategory.UNSUPPORTED_REQUEST,
                    error="Security Violation: Unsupported command or script execution request rejected."
                )

        explain_keywords = ["what is", "what elements", "explain", "describe", "show me what", "summarize"]
        for kw in explain_keywords:
            if kw in text_lower:
                elements = context.get_element_summary()
                names = [f"{e['id']} ({e['type']})" for e in elements]
                explanation = f"Workspace contains {len(elements)} elements: {', '.join(names)}."
                return AgentResponse(
                    request_id=req.request_id,
                    status="SUCCESS",
                    intent=IntentCategory.EXPLAIN_WORKSPACE,
                    explanation=explanation
                )

        success, raw_proposal, err = self.proposal_generator.generate(context, req.text)
        if not success or not raw_proposal:
            return AgentResponse(
                request_id=req.request_id,
                status="ERROR",
                intent=IntentCategory.PROPOSE_CHANGE,
                error=err or "Proposal generation failed"
            )

        valid, clean_proposal, sanitize_err = ProposalSanitizer.sanitize(raw_proposal, known_element_ids)
        if not valid or not clean_proposal:
            return AgentResponse(
                request_id=req.request_id,
                status="ERROR",
                intent=IntentCategory.PROPOSE_CHANGE,
                error=f"Sanitization Failed: {sanitize_err}"
            )

        return AgentResponse(
            request_id=req.request_id,
            status="SUCCESS",
            intent=IntentCategory.PROPOSE_CHANGE,
            proposal=clean_proposal,
            explanation=f"Generated proposal '{clean_proposal['title']}'"
        )
