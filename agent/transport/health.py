import os

def get_subsystem_health():
    from agent.core.config import config
    
    # Python Core is always READY if this runs
    python_state = "READY"
    
    # LLM
    if config.provider_name == "mock" or not config.gemini_api_key:
        llm_state = "MOCK"
    else:
        llm_state = "READY"
        
    # Vision
    vision_state = "MOCK" # Currently hardcoded to mock in gemini_provider if no vision specific setup
    
    # Voice
    voice_state = "MOCK" # We don't have real STT built-in
    
    # Executors
    browser_state = "SIMULATED"
    vscode_state = "READY" # Filesystem-backed
    canvas_state = "READY" # Real JSON patching
    
    return {
        "status": "ok",
        "subsystems": {
            "Electron": "READY",
            "Python": python_state,
            "Perception": "READY",
            "LLM": llm_state,
            "Vision": vision_state,
            "Voice": voice_state,
            "Task Runtime": "READY",
            "Browser": browser_state,
            "VS Code": vscode_state,
            "Living Canvas": canvas_state,
            "Terminal": "UNAVAILABLE",
            "Figma": "UNAVAILABLE"
        }
    }
