# compiler.py
import os
import tempfile
import subprocess

class Compiler:
    def __init__(self, output_console):
        self.output_console = output_console

    def compile_and_run(self, code, language):
        if not code.strip():
            self.output_console.setText("⚠️ No code to compile!")
            return

        with tempfile.TemporaryDirectory() as tempdir:
            output_file = os.path.join(tempdir, 'temp.out')
            if language == "c":
                compileCommand = ['gcc', '-x', 'c', '-', '-o', output_file]
            elif language == "c++":
                compileCommand = ['g++', '-x', 'c++', '-', '-o', output_file]
            elif language == "java":
                compileCommand = ['javac', '-d', tempdir, '-']
                output_file = os.path.join(tempdir, 'Main')
            elif language == "python":
                compileCommand = ['python3', '-c', code]
                output_file = None
            else:
                self.output_console.setText("❌ Unsupported language!")
                return

            try:
                if language != "python":
                    compileProcess = subprocess.Popen(
                        compileCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    compileStdout, compileStderr = compileProcess.communicate(input=code.encode('utf-8'))
                    if compileProcess.returncode != 0:
                        self.output_console.setText(f"❌ Compilation Error:\n\n{compileStderr.decode()}")
                        return

                if language == "python":
                    runProcess = subprocess.Popen(
                        compileCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                else:
                    runProcess = subprocess.Popen(
                        output_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )

                executionStdout, executionStderr = runProcess.communicate()

                if executionStderr:
                    self.output_console.setText(f"❌ Execution Error:\n\n{executionStderr.decode()}")
                else:
                    self.output_console.setText(f"✅ Output:\n\n{executionStdout.decode()}")

            except Exception as e:
                self.output_console.setText(f"⚠️ Error occurred: {str(e)}")