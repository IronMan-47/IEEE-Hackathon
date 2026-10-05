import re
from typing import Optional
from agent.voice.models import VoiceTranscript, VoiceCommand, InteractionIntentType

class VoiceCommandRouter:
    """
    Classifies a transcript into a VoiceCommand and determines its InteractionIntentType.
    Does NOT execute commands.
    """
    @classmethod
    def route_transcript(cls, transcript: VoiceTranscript, active_task_id: Optional[str] = None) -> VoiceCommand:
        text = transcript.text.lower().strip()
        
        # Simple rule-based routing for demonstration
        if re.match(r'^(cancel|stop|abort)\b', text):
            intent = InteractionIntentType.CONTROL_COMMAND
        elif re.match(r'^(why|explain|how|what)\b', text):
            intent = InteractionIntentType.EXPLANATION_REQUEST
        elif re.match(r'^(change|no|wrong|fix|target)\b', text):
            intent = InteractionIntentType.CORRECTION
        elif re.match(r'^(approve|yes|ok|go ahead|do it)\b', text):
            intent = InteractionIntentType.TASK_INTERACTION
        else:
            intent = InteractionIntentType.NEW_REQUEST
            
        return VoiceCommand(
            transcript_id=transcript.transcript_id,
            text=transcript.text,
            interaction_intent=intent,
            confidence=transcript.confidence,
            target_task_id=active_task_id
        )
