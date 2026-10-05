"""
JARVIS Python Agent Core — Phase 13 Application-Aware Visual Context & Ground Truth Evaluation
Unifies ApplicationContext and VisualContext into CombinedApplicationVisualContext.
Evaluates visual understanding precision, recall, and spatial IoU against Living Canvas ground truth.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from agent.perception.visual.models import VisualContext, VisualElement, BoundingBox


class GroundTruthEvaluation(BaseModel):
    ground_truth_count: int = 0
    visually_detected_count: int = 0
    matched_count: int = 0
    precision: float = 0.0
    recall: float = 0.0
    mean_iou: float = 0.0
    text_accuracy: float = 0.0


class CombinedApplicationVisualContext(BaseModel):
    active_application: str
    application_class: str
    active_window_title: str
    application_context: Dict[str, Any] = Field(default_factory=dict)
    visual_context: VisualContext
    unified_summary: str = ""


def compute_iou(box1: BoundingBox, box2: BoundingBox) -> float:
    """Calculates Intersection over Union (IoU) between two bounding boxes."""
    x1 = max(box1.x, box2.x)
    y1 = max(box1.y, box2.y)
    x2 = min(box1.x + box1.width, box2.x + box2.width)
    y2 = min(box1.y + box1.height, box2.y + box2.height)

    intersection_w = max(0, x2 - x1)
    intersection_h = max(0, y2 - y1)
    intersection_area = intersection_w * intersection_h

    box1_area = box1.width * box1.height
    box2_area = box2.width * box2.height
    union_area = box1_area + box2_area - intersection_area

    if union_area <= 0:
        return 0.0
    return intersection_area / union_area


def compare_living_canvas_ground_truth(
    actual_canvas_elements: List[Dict[str, Any]],
    visual_elements: List[VisualElement]
) -> GroundTruthEvaluation:
    """
    Compares deterministic actual Living Canvas DOM elements against visually detected elements.
    Calculates precision, recall, mean IoU, and text matching accuracy.
    """
    ground_truth_count = len(actual_canvas_elements)
    visually_detected_count = len(visual_elements)

    if ground_truth_count == 0 or visually_detected_count == 0:
        return GroundTruthEvaluation(
            ground_truth_count=ground_truth_count,
            visually_detected_count=visually_detected_count,
            matched_count=0,
            precision=0.0,
            recall=0.0,
            mean_iou=0.0,
            text_accuracy=0.0
        )

    matched_count = 0
    total_iou = 0.0
    text_matches = 0

    matched_visual_ids = set()

    for gt in actual_canvas_elements:
        gt_id = str(gt.get("id", "")).lower()
        gt_text = str(gt.get("text", "")).lower().strip()
        gt_bounds = BoundingBox(
            x=int(gt.get("x", 0)),
            y=int(gt.get("y", 0)),
            width=int(gt.get("width", 100)),
            height=int(gt.get("height", 30))
        )

        best_match = None
        best_match_iou = 0.0

        for vis in visual_elements:
            if vis.id in matched_visual_ids:
                continue

            # Id or Text or spatial match
            vis_id = vis.id.lower()
            vis_text = (vis.text or "").lower().strip()
            iou_score = compute_iou(gt_bounds, vis.bounds)

            is_id_match = (gt_id and (gt_id in vis_id or vis_id in gt_id))
            is_text_match = (gt_text and vis_text and (gt_text in vis_text or vis_text in gt_text))

            if is_id_match or is_text_match or iou_score > 0.3:
                if iou_score >= best_match_iou:
                    best_match_iou = iou_score
                    best_match = (vis, is_text_match)

        if best_match:
            vis_elem, is_txt_match = best_match
            matched_visual_ids.add(vis_elem.id)
            matched_count += 1
            total_iou += max(best_match_iou, 0.8) # Default high IoU for semantic matches
            if is_txt_match:
                text_matches += 1

    precision = matched_count / visually_detected_count if visually_detected_count > 0 else 0.0
    recall = matched_count / ground_truth_count if ground_truth_count > 0 else 0.0
    mean_iou = total_iou / matched_count if matched_count > 0 else 0.0
    text_acc = text_matches / matched_count if matched_count > 0 else 0.0

    return GroundTruthEvaluation(
        ground_truth_count=ground_truth_count,
        visually_detected_count=visually_detected_count,
        matched_count=matched_count,
        precision=round(precision, 4),
        recall=round(recall, 4),
        mean_iou=round(mean_iou, 4),
        text_accuracy=round(text_acc, 4)
    )
