"""
JARVIS Python Agent Core — Phase 14 Context Fusion Resolver
Fuses Windows perception, application adapters, visual context, and user request into a deterministic,
provenance-aware GroundedContext. Detects conflicts and surfaces them explicitly.
"""

import time
from typing import Optional, Dict, Any, List
from agent.perception.types import PerceptionResult
from agent.perception.visual.models import VisualContext, VisualElement, VisualElementType
from agent.context.fusion.provenance import ProvenanceTag, get_provenance_precedence
from agent.context.fusion.evidence import Evidence, EvidenceType
from agent.context.fusion.conflicts import ContextConflict, ConflictType, ConflictResolution
from agent.context.fusion.models import GroundedContext, FactStatement, FactType, ApplicationRole, AppInfo
from agent.context.fusion.target_resolution import TargetResolver
from agent.context.fusion.confidence import ContextConfidenceCalculator
from agent.context.fusion.hash import compute_grounded_context_hash
from agent.core.logging import logger


class ContextResolver:
    @staticmethod
    def fuse(
        perception_result: Optional[PerceptionResult] = None,
        application_context: Optional[Dict[str, Any]] = None,
        visual_context: Optional[VisualContext] = None,
        user_text: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> GroundedContext:
        """
        Fuses all perception sources into a GroundedContext.
        Preserves provenance, resolves conflicts deterministically, and classifies facts/inferences.
        """
        ts = int(time.time() * 1000)
        evidence_list: List[Evidence] = []
        conflicts: List[ContextConflict] = []
        facts: List[FactStatement] = []

        # 1. Primary & Secondary Application Identification
        primary_app_name = "Unknown Application"
        primary_process = "unknown.exe"
        if perception_result:
            primary_app_name = perception_result.active_application.name or "Unknown Application"
            primary_process = perception_result.active_application.process_name or "unknown.exe"

            evidence_list.append(Evidence(
                evidence_id="ev_win_app",
                type=EvidenceType.WINDOW_METADATA,
                source=ProvenanceTag.WINDOWS_API,
                content_reference=f"Active Process: {primary_process}, Window: '{perception_result.active_window.title}'",
                confidence=1.0,
                timestamp=ts
            ))
            facts.append(FactStatement(
                id="fact_primary_app",
                statement=f"Active application is {primary_app_name} ({primary_process})",
                type=FactType.FACT,
                provenance=ProvenanceTag.WINDOWS_API,
                confidence=1.0
            ))

        primary_app = AppInfo(
            name=primary_app_name,
            process_name=primary_process,
            role=ApplicationRole.PRIMARY_APPLICATION,
            details=application_context or {}
        )

        secondary_apps: List[AppInfo] = []

        # 2. Application Adapter Evidence
        app_ctx = application_context or {}
        active_file = app_ctx.get("active_file") or app_ctx.get("file")
        active_url = app_ctx.get("origin") or app_ctx.get("active_url")

        if active_file:
            evidence_list.append(Evidence(
                evidence_id="ev_app_file",
                type=EvidenceType.CODE_CONTEXT,
                source=ProvenanceTag.VS_CODE_ADAPTER,
                content_reference=f"Active Document: {active_file}",
                confidence=0.95,
                timestamp=ts
            ))
            facts.append(FactStatement(
                id="fact_active_file",
                statement=f"Active document in editor is '{active_file}'",
                type=FactType.FACT,
                provenance=ProvenanceTag.VS_CODE_ADAPTER,
                confidence=0.95
            ))

        if active_url:
            evidence_list.append(Evidence(
                evidence_id="ev_app_url",
                type=EvidenceType.BROWSER_CONTEXT,
                source=ProvenanceTag.BROWSER_ADAPTER,
                content_reference=f"Browser Origin: {active_url}",
                confidence=0.95,
                timestamp=ts
            ))
            facts.append(FactStatement(
                id="fact_browser_origin",
                statement=f"Active browser page origin is '{active_url}'",
                type=FactType.FACT,
                provenance=ProvenanceTag.BROWSER_ADAPTER,
                confidence=0.95
            ))

        # Check if browser is secondary application when VS Code is primary
        if "chrome" in (perception_result.active_window.title if perception_result else "").lower() or "browser" in app_ctx:
            if "code" in primary_process.lower():
                secondary_apps.append(AppInfo(
                    name="Google Chrome",
                    process_name="chrome.exe",
                    role=ApplicationRole.SECONDARY_APPLICATION,
                    details={"origin": active_url or "https://example.com"}
                ))

        # 3. Visual Context Evidence & Conflicts
        if visual_context:
            evidence_list.append(Evidence(
                evidence_id="ev_visual_summary",
                type=EvidenceType.VISUAL_ELEMENT,
                source=visual_context.provenance,
                content_reference=visual_context.visual_summary,
                confidence=visual_context.confidence,
                timestamp=visual_context.timestamp
            ))
            facts.append(FactStatement(
                id="fact_visual_summary",
                statement=f"Observed Screen Layout: {visual_context.visual_summary}",
                type=FactType.OBSERVED,
                provenance=visual_context.provenance,
                confidence=visual_context.confidence
            ))

            # Conflict Detection: Windows API vs Visual Model Application Mismatch
            vis_app = visual_context.application.lower()
            if primary_app_name.lower() not in vis_app and vis_app not in primary_app_name.lower() and "unknown" not in vis_app:
                conflict = ContextConflict(
                    conflict_id=f"cfl_app_{ts}",
                    type=ConflictType.APPLICATION_MISMATCH,
                    sources=[ProvenanceTag.WINDOWS_API, visual_context.provenance],
                    fields=["application"],
                    values={"windows_api": primary_app_name, "visual_model": visual_context.application},
                    severity="HIGH",
                    detected_at=ts,
                    resolution=ConflictResolution.AUTHORITATIVE_SOURCE,
                    resolution_source=ProvenanceTag.WINDOWS_API,
                    details=f"Windows API process '{primary_app_name}' takes precedence over visual inference '{visual_context.application}'"
                )
                conflicts.append(conflict)
                logger.warn(f"ContextResolver CONFLICT DETECTED: {conflict.details}")

            # Conflict Detection: Active File vs Visual Editor File Mismatch
            if active_file:
                vis_code_elems = [e for e in visual_context.elements if e.type == VisualElementType.TAB]
                if vis_code_elems:
                    vis_tab_text = vis_code_elems[0].text or ""
                    if vis_tab_text and active_file.lower() not in vis_tab_text.lower() and vis_tab_text.lower() not in active_file.lower():
                        conflict_file = ContextConflict(
                            conflict_id=f"cfl_file_{ts}",
                            type=ConflictType.FILE_MISMATCH,
                            sources=[ProvenanceTag.VS_CODE_ADAPTER, visual_context.provenance],
                            fields=["active_file"],
                            values={"adapter_file": active_file, "visual_tab": vis_tab_text},
                            severity="HIGH",
                            detected_at=ts,
                            resolution=ConflictResolution.USER_CLARIFICATION_REQUIRED,
                            details=f"Conflict: Application adapter reports active file '{active_file}', but visual tab displays '{vis_tab_text}'"
                        )
                        conflicts.append(conflict_file)
                        logger.warn(f"ContextResolver CONFLICT DETECTED: {conflict_file.details}")

        # 4. Preliminary GroundedContext Construction
        gctx = GroundedContext(
            context_id=f"gctx_{ts}",
            timestamp=ts,
            request_id=request_id,
            primary_application=primary_app,
            secondary_applications=secondary_apps,
            application_context=app_ctx,
            visual_context=visual_context,
            relevant_regions=visual_context.regions if visual_context else [],
            relevant_elements=visual_context.elements if visual_context else [],
            user_request=user_text,
            conflicts=conflicts,
            evidence_list=evidence_list,
            facts=facts,
            provenance=ProvenanceTag.WINDOWS_API
        )

        # 5. Target Resolution & Ambiguity Clarification
        clarification_req = False
        clarification_q = None

        if user_text:
            target_ref, is_ambig, ambig_question = TargetResolver.resolve_target(user_text, gctx)
            gctx.active_target = target_ref

            if is_ambig:
                clarification_req = True
                clarification_q = ambig_question
            elif any(c.resolution == ConflictResolution.USER_CLARIFICATION_REQUIRED for c in conflicts):
                clarification_req = True
                unresolved_conf = [c for c in conflicts if c.resolution == ConflictResolution.USER_CLARIFICATION_REQUIRED][0]
                clarification_q = unresolved_conf.details

        gctx.clarification_required = clarification_req
        gctx.clarification_question = clarification_q

        # 6. Context Confidence & Canonical Hashing
        gctx.confidence = ContextConfidenceCalculator.calculate_confidence(
            evidence_list=evidence_list,
            conflicts=conflicts,
            target_ambiguous=clarification_req
        )
        gctx.context_hash = compute_grounded_context_hash(gctx)

        logger.info(f"ContextResolver: Fused GroundedContext [{gctx.context_id}] (Hash: {gctx.context_hash[:8]}, Conf: {gctx.confidence}, Conflicts: {len(conflicts)})")
        return gctx
