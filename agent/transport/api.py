"""
JARVIS Python Agent Core — FastAPI Transport API with Phase 10 Controlled Execution Pipeline
"""

from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.core.types import AgentRequest, AgentResponse
from agent.intent.models import Plan, PlanStep, ClarificationRequest
from agent.proposals.models import Proposal, ProposalOperation
from agent.execution.models import ExecutionRequest, ExecutionResult
from agent.core.agent import JarvisAgent
from agent.core.config import config
from agent.core.logging import logger
from agent.perception.capture import CaptureManager
from agent.adapters.registry import AdapterRegistry
from agent.context.visual import compare_living_canvas_ground_truth
from agent.tasks.orchestrator import TaskOrchestrator

app = FastAPI(title="JARVIS Python Agent Core", version="0.15.0")
agent_instance = JarvisAgent()
task_orchestrator = TaskOrchestrator(agent=agent_instance)
capture_manager = CaptureManager()
adapter_registry = AdapterRegistry()


class VisualAnalyzePayload(BaseModel):
    scenario: Optional[str] = None
    request_capture: bool = True
    workspace_context: Optional[Dict[str, Any]] = None


class GroundTruthEvalPayload(BaseModel):
    actual_elements: List[Dict[str, Any]]


class PerceptionRequestPayload(BaseModel):
    request_capture: bool = True
    workspace_context: Optional[Dict[str, Any]] = None


class PolicyTogglePayload(BaseModel):
    enabled: bool


class PlanRequestPayload(BaseModel):
    text: str
    perception_context: Optional[Dict[str, Any]] = None
    workspace_context: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class PlanModifyPayload(BaseModel):
    original_plan: Dict[str, Any]
    new_steps: List[Dict[str, Any]]


class PlanAcceptPayload(BaseModel):
    plan: Dict[str, Any]


class ProposalFromPlanPayload(BaseModel):
    plan: Dict[str, Any]
    perception_context: Optional[Dict[str, Any]] = None
    workspace_context: Optional[Dict[str, Any]] = None
    user_req_text: Optional[str] = None


class ProposalModifyPhase9Payload(BaseModel):
    original_proposal: Dict[str, Any]
    modified_operations: List[Dict[str, Any]]
    perception_context: Optional[Dict[str, Any]] = None
    workspace_context: Optional[Dict[str, Any]] = None
    user_reason: Optional[str] = None


class ProposalAcceptPhase9Payload(BaseModel):
    proposal: Dict[str, Any]
    perception_context: Optional[Dict[str, Any]] = None
    workspace_context: Optional[Dict[str, Any]] = None


class ExecutePayload(BaseModel):
    execution_request: Dict[str, Any]
    proposal: Dict[str, Any]
    perception_context: Optional[Dict[str, Any]] = None
    workspace_context: Optional[Dict[str, Any]] = None


from agent.transport.health import get_subsystem_health
from agent.runtime.lifecycle import runtime_manager

@app.post("/api/runtime/stop")
def stop_runtime():
    runtime_manager.trigger_emergency_stop()
    return {"status": "STOPPED"}

@app.post("/api/runtime/resume")
def resume_runtime():
    runtime_manager.clear_emergency_stop()
    return {"status": "READY"}

@app.get("/health")
def health_check():
    return get_subsystem_health()


@app.post("/agent/perceive")
def perceive_desktop(payload: Optional[PerceptionRequestPayload] = None):
    try:
        req_cap = payload.request_capture if payload else True
        ws_ctx = payload.workspace_context if payload else None

        perception_result = capture_manager.perceive_desktop(request_capture=req_cap)
        app_context = adapter_registry.get_application_context(
            perception_result,
            workspace_context=ws_ctx
        )

        response_dict = perception_result.to_summary_dict()
        response_dict["application_context"] = app_context.model_dump()
        return response_dict
    except Exception as e:
        logger.error(f"Perception API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/perceive/policy")
def set_perception_policy(payload: PolicyTogglePayload):
    try:
        capture_manager.policy_manager.set_enabled(payload.enabled)
        agent_instance.is_system_ready = payload.enabled
        return {"status": "ok", "perception_enabled": capture_manager.policy_manager.is_enabled()}
    except Exception as e:
        logger.error(f"Policy Toggle API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/plan")
def generate_plan(payload: PlanRequestPayload):
    try:
        plan, clarification, context, intent, goal = agent_instance.plan_request(
            raw_text=payload.text,
            perception_context=payload.perception_context,
            workspace_context=payload.workspace_context,
            request_id=payload.request_id
        )

        if clarification:
            return {
                "status": "CLARIFICATION_REQUIRED",
                "clarification": clarification.model_dump(),
                "context": context.model_dump(),
                "intent": intent.model_dump()
            }

        return {
            "status": "SUCCESS",
            "plan": plan.model_dump(),
            "context": context.model_dump(),
            "intent": intent.model_dump(),
            "goal": goal.model_dump()
        }
    except ValueError as ve:
        logger.warn(f"Plan validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Plan Generation API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/plan/modify")
def modify_plan(payload: PlanModifyPayload):
    try:
        orig_plan = Plan(**payload.original_plan)
        steps = [PlanStep(**s) for s in payload.new_steps]
        modified = agent_instance.modify_plan(orig_plan, steps)
        return {
            "status": "SUCCESS",
            "plan": modified.model_dump()
        }
    except Exception as e:
        logger.error(f"Plan Modify API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/plan/accept")
def accept_plan(payload: PlanAcceptPayload):
    try:
        plan_obj = Plan(**payload.plan)
        accepted = agent_instance.accept_plan(plan_obj)
        return {
            "status": "SUCCESS",
            "plan": accepted.model_dump(),
            "message": "Plan accepted as strategy. No execution performed."
        }
    except Exception as e:
        logger.error(f"Plan Accept API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/propose/from-plan")
def generate_proposal_from_plan(payload: ProposalFromPlanPayload):
    try:
        plan_obj = Plan(**payload.plan)
        proposal, context = agent_instance.generate_proposal_from_plan(
            plan=plan_obj,
            perception_context=payload.perception_context,
            workspace_context=payload.workspace_context,
            user_req_text=payload.user_req_text
        )
        return {
            "status": "SUCCESS",
            "proposal": proposal.model_dump(),
            "context": context.model_dump()
        }
    except ValueError as ve:
        logger.warn(f"Proposal generation validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Proposal Generation API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/propose/modify")
def modify_proposal_phase9(payload: ProposalModifyPhase9Payload):
    try:
        orig_prop = Proposal(**payload.original_proposal)
        ops = [ProposalOperation(**op) for op in payload.modified_operations]
        child_prop, context = agent_instance.modify_proposal_phase9(
            original_proposal=orig_prop,
            modified_ops=ops,
            perception_context=payload.perception_context,
            workspace_context=payload.workspace_context,
            user_reason=payload.user_reason
        )
        return {
            "status": "SUCCESS",
            "proposal": child_prop.model_dump(),
            "context": context.model_dump()
        }
    except Exception as e:
        logger.error(f"Proposal Modify API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/propose/accept")
def accept_proposal_phase9(payload: ProposalAcceptPhase9Payload):
    try:
        prop_obj = Proposal(**payload.proposal)
        accepted_prop, approval_token, context = agent_instance.accept_proposal_phase9(
            proposal=prop_obj,
            perception_context=payload.perception_context,
            workspace_context=payload.workspace_context
        )
        return {
            "status": "SUCCESS",
            "proposal": accepted_prop.model_dump(),
            "approval_token": approval_token,
            "message": "Proposal ACCEPTED and ApprovalToken issued. NO EXECUTION PERFORMED."
        }
    except Exception as e:
        logger.error(f"Proposal Accept API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/execute")
def execute_proposal(payload: ExecutePayload):
    try:
        exec_req = ExecutionRequest(**payload.execution_request)
        prop_obj = Proposal(**payload.proposal)
        result = agent_instance.execute_proposal(
            exec_request=exec_req,
            proposal=prop_obj,
            perception_context=payload.perception_context,
            workspace_context=payload.workspace_context
        )
        return {
            "status": result.status.value,
            "execution_result": result.model_dump()
        }
    except Exception as e:
        logger.error(f"Execution API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/propose", response_model=AgentResponse)
def propose_action(request: AgentRequest):
    try:
        response = agent_instance.handle_request(request)
        return response
    except Exception as e:
        logger.error(f"HTTP Endpoint Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/visual/analyze")
def analyze_visual_screen(payload: Optional[VisualAnalyzePayload] = None):
    try:
        req_cap = payload.request_capture if payload else True
        ws_ctx = payload.workspace_context if payload else None
        sc = payload.scenario if payload else None

        perception_result = capture_manager.perceive_desktop(request_capture=req_cap)
        vctx = agent_instance.analyze_visual_screen(perception_result, scenario=sc)

        return {
            "status": "SUCCESS",
            "visual_context": vctx.model_dump()
        }
    except Exception as e:
        logger.error(f"Visual Perception API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/visual/current")
def get_current_visual_context():
    vctx = agent_instance.current_visual_context
    return {
        "status": "SUCCESS",
        "visual_context": vctx.model_dump() if vctx else None
    }


@app.post("/agent/visual/clear")
def clear_visual_context():
    agent_instance.current_visual_context = None
    return {"status": "SUCCESS", "message": "Visual context cleared"}


@app.post("/agent/visual/ground_truth")
def evaluate_ground_truth(payload: GroundTruthEvalPayload):
    vctx = agent_instance.current_visual_context
    visual_elements = vctx.elements if vctx else []
    eval_result = compare_living_canvas_ground_truth(payload.actual_elements, visual_elements)
    return {
        "status": "SUCCESS",
        "evaluation": eval_result.model_dump()
    }


class ContextFusePayload(BaseModel):
    user_text: Optional[str] = None
    request_id: Optional[str] = None
    request_capture: bool = True
    scenario: Optional[str] = None
    workspace_context: Optional[Dict[str, Any]] = None


class TargetResolvePayload(BaseModel):
    user_text: str


@app.post("/agent/context/fuse")
def fuse_grounded_context(payload: Optional[ContextFusePayload] = None):
    try:
        req_cap = payload.request_capture if payload else True
        ws_ctx = payload.workspace_context if payload else None
        sc = payload.scenario if payload else None
        user_txt = payload.user_text if payload else None
        req_id = payload.request_id if payload else None

        perception_result = capture_manager.perceive_desktop(request_capture=req_cap)
        app_context = adapter_registry.get_application_context(perception_result, workspace_context=ws_ctx).model_dump()

        if sc or not agent_instance.current_visual_context:
            vctx = agent_instance.analyze_visual_screen(perception_result, scenario=sc)
        else:
            vctx = agent_instance.current_visual_context

        gctx = agent_instance.fuse_context(
            perception_result=perception_result,
            application_context=app_context,
            visual_context=vctx,
            user_text=user_txt,
            request_id=req_id
        )

        return {
            "status": "SUCCESS",
            "grounded_context": gctx.model_dump()
        }
    except Exception as e:
        logger.error(f"Context Fusion API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/context/current")
def get_current_grounded_context():
    gctx = agent_instance.current_grounded_context
    return {
        "status": "SUCCESS",
        "grounded_context": gctx.model_dump() if gctx else None
    }


@app.post("/agent/context/resolve-target")
def resolve_target(payload: TargetResolvePayload):
    try:
        gctx = agent_instance.current_grounded_context
        if not gctx:
            perception_result = capture_manager.perceive_desktop(request_capture=False)
            app_ctx = adapter_registry.get_application_context(perception_result).model_dump()
            vctx = agent_instance.analyze_visual_screen(perception_result)
            gctx = agent_instance.fuse_context(perception_result, app_ctx, vctx, payload.user_text)

        from agent.context.fusion.target_resolution import TargetResolver
        target_ref, is_ambig, question = TargetResolver.resolve_target(payload.user_text, gctx)

        return {
            "status": "SUCCESS",
            "target": target_ref.model_dump() if target_ref else None,
            "clarification_required": is_ambig,
            "clarification_question": question
        }
    except Exception as e:
        logger.error(f"Target Resolution API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Phase 15 Task Orchestration Payloads & Endpoints

class TaskCreatePayload(BaseModel):
    text: str
    perception_context: Optional[Dict[str, Any]] = None
    workspace_context: Optional[Dict[str, Any]] = None
    max_steps: int = 10
    max_replans: int = 3


class TaskStepApprovePayload(BaseModel):
    task_id: str
    step_id: str
    perception_context: Optional[Dict[str, Any]] = None
    workspace_context: Optional[Dict[str, Any]] = None


class TaskStepExecutePayload(BaseModel):
    task_id: str
    step_id: str
    perception_context: Optional[Dict[str, Any]] = None
    workspace_context: Optional[Dict[str, Any]] = None


class TaskActionPayload(BaseModel):
    task_id: str


@app.post("/agent/tasks/create")
def create_task(payload: TaskCreatePayload):
    try:
        task = task_orchestrator.create_task(
            user_text=payload.text,
            workspace_context=payload.workspace_context,
            max_steps=payload.max_steps,
            max_replans=payload.max_replans
        )
        return {
            "status": "SUCCESS",
            "task": task.model_dump()
        }
    except ValueError as ve:
        logger.warn(f"Task create validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Task Create API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/tasks/{task_id}")
def get_task(task_id: str):
    task = task_orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task ID [{task_id}] not found.")
    return {
        "status": "SUCCESS",
        "task": task.model_dump()
    }


@app.post("/agent/tasks/step/approve")
def approve_task_step(payload: TaskStepApprovePayload):
    try:
        task, token = task_orchestrator.approve_step(
            task_id=payload.task_id,
            step_id=payload.step_id,
            perception_context=payload.perception_context,
            workspace_context=payload.workspace_context
        )
        return {
            "status": "SUCCESS",
            "task": task.model_dump(),
            "approval_token": token
        }
    except ValueError as ve:
        logger.warn(f"Task step approve validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Task Step Approve API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/tasks/step/execute")
def execute_task_step(payload: TaskStepExecutePayload):
    try:
        task, exec_res = task_orchestrator.execute_step(
            task_id=payload.task_id,
            step_id=payload.step_id,
            perception_context=payload.perception_context,
            workspace_context=payload.workspace_context
        )
        return {
            "status": "SUCCESS",
            "task": task.model_dump(),
            "execution_result": exec_res.model_dump()
        }
    except ValueError as ve:
        logger.warn(f"Task step execute validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Task Step Execute API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/tasks/pause")
def pause_task(payload: TaskActionPayload):
    try:
        task = task_orchestrator.pause_task(payload.task_id)
        return {"status": "SUCCESS", "task": task.model_dump()}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/tasks/cancel")
def cancel_task(payload: TaskActionPayload):
    try:
        task = task_orchestrator.cancel_task(payload.task_id)
        return {"status": "SUCCESS", "task": task.model_dump()}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/tasks/resume")
def resume_task(payload: TaskActionPayload):
    try:
        task = task_orchestrator.resume_task(payload.task_id)
        return {"status": "SUCCESS", "task": task.model_dump()}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Phase 16 Explainability & Human-in-the-Loop endpoints

@app.get("/agent/tasks/{task_id}/explanation")
def get_task_explanation(task_id: str, depth: str = "STANDARD"):
    task = task_orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task ID [{task_id}] not found.")
    
    explanation = task.explanation.model_dump() if task.explanation else None
    return {
        "status": "SUCCESS",
        "explanation": explanation
    }

class TaskModifyStepPayload(BaseModel):
    task_id: str
    step_id: str
    modification_instructions: str
    perception_context: Optional[Dict[str, Any]] = None
    workspace_context: Optional[Dict[str, Any]] = None

@app.post("/agent/tasks/step/modify")
def modify_task_step(payload: TaskModifyStepPayload):
    try:
        task, modification = task_orchestrator.modify_step(
            task_id=payload.task_id,
            step_id=payload.step_id,
            instructions=payload.modification_instructions,
            perception_context=payload.perception_context,
            workspace_context=payload.workspace_context
        )
        return {
            "status": "SUCCESS",
            "task": task.model_dump(),
            "modification": modification.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Phase 17 Unified Agent Runtime endpoints

from agent.runtime.lifecycle import runtime_manager

@app.on_event("startup")
def startup_event():
    runtime_manager.initialize()

@app.on_event("shutdown")
def shutdown_event():
    runtime_manager.shutdown()

@app.get("/agent/runtime/state")
def get_runtime_state():
    return {
        "status": "SUCCESS",
        "runtime_state": runtime_manager.state.model_dump()
    }

class HeartbeatPayload(BaseModel):
    timestamp: int
    status: str

@app.post("/agent/runtime/heartbeat")
def handle_heartbeat(payload: HeartbeatPayload):
    runtime_manager.handle_heartbeat(payload.model_dump())
    return {"status": "SUCCESS"}

class RecoverPayload(BaseModel):
    action: str  # e.g., "reconcile", "discard"
    domain: Optional[str] = None
    workspace_context: Optional[Dict[str, Any]] = None

@app.post("/agent/runtime/recover")
def handle_recovery(payload: RecoverPayload):
    if payload.action == "reconcile" and payload.domain:
        # Dummy reconciliation call for phase 17 simulation
        runtime_manager.reconcile_execution(payload.domain, {}, {}, payload.workspace_context or {})
    else:
        # e.g. discard
        runtime_manager.state.recovery_state = "NONE"
        runtime_manager.state.recovery_required = False
        runtime_manager._transition(runtime_manager.state.status)  # forces a save
    
    return {
        "status": "SUCCESS",
        "runtime_state": runtime_manager.state.model_dump()
    }

@app.get("/agent/runtime/events")
def get_runtime_events(limit: int = 100):
    events = runtime_manager.event_bus.get_events(limit)
    return {"status": "SUCCESS", "events": [e.model_dump() for e in events]}

# Phase 18 Voice Interaction endpoints

from agent.voice.voice_session import voice_manager

@app.post("/agent/voice/start")
def start_voice_listening():
    session = voice_manager.start_listening()
    return {"status": "SUCCESS", "session": session.model_dump()}

@app.post("/agent/voice/stop")
def stop_voice_listening():
    session = voice_manager.stop_listening()
    return {"status": "SUCCESS", "session": session.model_dump() if session else None}

class ProcessSpeechPayload(BaseModel):
    text: str
    confidence: str = "HIGH"

@app.post("/agent/voice/process")
def process_voice_speech(payload: ProcessSpeechPayload):
    result = voice_manager.process_speech(payload.text, payload.confidence)
    return result

class ConfirmTranscriptPayload(BaseModel):
    transcript_id: str
    text: str

@app.post("/agent/voice/confirm")
def confirm_voice_transcript(payload: ConfirmTranscriptPayload):
    result = voice_manager.confirm_transcript(payload.transcript_id, payload.text)
    return result

@app.post("/agent/voice/cancel")
def cancel_voice_session():
    voice_manager.cancel_session()
    return {"status": "SUCCESS"}




