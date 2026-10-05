from agent.perception.types import AppClassification

class AppClassifier:
    CODE_PROCESSES = {"code.exe", "devenv.exe", "pycharm64.exe", "idea64.exe", "sublime_text.exe", "atom.exe", "webstorm64.exe"}
    BROWSER_PROCESSES = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "vivaldi.exe"}
    DESIGN_PROCESSES = {"figma.exe", "photoshop.exe", "illustrator.exe", "acad.exe", "blender.exe", "canva.exe"}
    TERMINAL_PROCESSES = {"cmd.exe", "powershell.exe", "wt.exe", "bash.exe", "zsh.exe", "conhost.exe", "windowsterminal.exe"}
    DOCUMENT_PROCESSES = {"winword.exe", "excel.exe", "powerpnt.exe", "acrord32.exe", "notepad.exe", "wordpad.exe"}

    @classmethod
    def classify(cls, process_name: str, window_title: str = "") -> AppClassification:
        proc = (process_name or "").lower().strip()
        title = (window_title or "").lower().strip()

        if proc in cls.CODE_PROCESSES or "visual studio code" in title or "vsc" in title:
            return AppClassification.CODE_EDITOR
        elif proc in cls.BROWSER_PROCESSES or "chrome" in title or "edge" in title or "firefox" in title:
            return AppClassification.BROWSER
        elif proc in cls.DESIGN_PROCESSES or "figma" in title or "photoshop" in title:
            return AppClassification.DESIGN_TOOL
        elif proc in cls.TERMINAL_PROCESSES or "powershell" in title or "command prompt" in title:
            return AppClassification.TERMINAL
        elif proc in cls.DOCUMENT_PROCESSES or "word" in title or "excel" in title:
            return AppClassification.DOCUMENT_EDITOR
        
        return AppClassification.UNKNOWN
