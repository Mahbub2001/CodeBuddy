from worker import AIWorker

class AIAssistantHandler:
    def __init__(self, ide):
        self.ide = ide

    def assist_code(self):
        editor = self.ide.get_current_editor()
        assistant = self.ide.assistantSelector.currentText()
        code_optional_scenarios = ["Code Generation", "LeetCode Solver", "General Assistant"]

        if assistant not in code_optional_scenarios:
            if not editor or not editor.toPlainText().strip():
                self.ide.outputConsole.setText("⚠️ No code to assist!")
                return
            code = editor.toPlainText()
        else:
            code = ""

        prompt = self.ide.aiPanel.toPlainText()
        if not prompt.strip():
            self.ide.aiPanel.setText("💡 AI Code Assistant: Please write a prompt!")
            return

        language = self.ide.languageSelector.currentText().lower()

        self.ide.aiPanel.setText("⏳ AI Code Assistant is processing...")

        self.worker = AIWorker(self.ide.code_buddy, language, code, prompt, assistant)
        self.worker.result_signal.connect(self.update_ai_response)
        self.worker.error_signal.connect(self.update_ai_error)
        self.worker.start()

    def update_ai_response(self, response):
        current_text = self.ide.aiPanel.toPlainText()
        if current_text == "⏳ AI Code Assistant is processing...":
            self.ide.aiPanel.setText(f"💡 AI Code Assistant:\n\n{response}")
        else:
            self.ide.aiPanel.append(response)

    def update_ai_error(self, error_message):
        self.ide.aiPanel.setText(error_message)
