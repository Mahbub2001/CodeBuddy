from worker import AIWorker
import uuid

class AIAssistantHandler:
    def __init__(self, ide):
        self.ide = ide
        self.session_id = str(uuid.uuid4()) 

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

        prompt = self.ide.promptInput.toPlainText() 
        if not prompt.strip():
            self.ide.promptInput.setText("💡 AI Code Assistant: Please write a prompt!")
            return

        language = self.ide.languageSelector.currentText().lower()

        user_query = self.ide.promptInput.toPlainText().strip()
        self.ide.aiPanel.append(f'<div style="color: blue;"><b>You:</b> {user_query}</div>')
        self.ide.aiPanel.append('<div style="color: gray;"><b>AI:</b> ⏳ Processing...</div>')

        self.worker = AIWorker(self.ide.code_buddy, language, code, prompt, assistant, self.session_id)
        self.worker.result_signal.connect(self.update_ai_response)
        self.worker.error_signal.connect(self.update_ai_error)
        self.worker.start()

    def update_ai_response(self, response):
        current_text = self.ide.aiPanel.toPlainText()
        formatted_response = "\n".join(response.splitlines())  
        if current_text == "⏳ AI Code Assistant is processing...":
            self.ide.aiPanel.setText(f"💡 AI Code Assistant:\n\n{formatted_response}")
        else:
            self.ide.aiPanel.setText(current_text + "\n" + formatted_response) 

    def update_ai_error(self, error_message):
        self.ide.aiPanel.append(f'<div style="color: red;"><b>Error:</b> {error_message}</div>')