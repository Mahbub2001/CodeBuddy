from PyQt6.QtCore import QThread, pyqtSignal

class AIWorker(QThread):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, code_buddy, language, code, prompt, assistant):
        super().__init__()
        self.code_buddy = code_buddy
        self.language = language
        self.code = code
        self.prompt = prompt
        self.assistant = assistant

    def run(self):
        try:
            for chunk in self.code_buddy.process_query_stream(self.language, self.code, self.prompt, self.assistant):
                self.result_signal.emit(chunk)
        except ValueError as e:
            self.error_signal.emit(f"⚠️ Error: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"⚠️ An unexpected error occurred: {str(e)}")