import os
import tempfile
import subprocess
import sys
import select
import shutil
from PyQt6.QtWidgets import QInputDialog

class CompileRun:
    def __init__(self, output_console):
        self.output_console = output_console

    def compile_and_run(self, code, language):
        if not code.strip():
            self.output_console.setText("⚠️ No code to compile!")
            return

        tempdir = tempfile.mkdtemp() 
        output_file = os.path.join(tempdir, 'temp.out')

        try:
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

            # **Compile Code**
            if language != "python":
                compileProcess = subprocess.Popen(
                    compileCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                compileStdout, compileStderr = compileProcess.communicate(input=code.encode('utf-8'))
                if compileProcess.returncode != 0:
                    self.output_console.setText(f"❌ Compilation Error:\n\n{compileStderr.decode()}")
                    return

            if language == "python":
                runCommand = compileCommand
            else:
                runCommand = [output_file]

            runProcess = subprocess.Popen(
                runCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True
            )

            try:
                if sys.platform != "win32":
                    rlist, _, _ = select.select([runProcess.stdout, runProcess.stderr], [], [], 2)
                else:
                    runProcess.wait(timeout=2)
                    rlist = []

            except subprocess.TimeoutExpired:
                rlist = [runProcess.stdout] 

            if not rlist:
                executionStdout, executionStderr = runProcess.communicate()
                if executionStderr:
                    self.output_console.setText(f"❌ Execution Error:\n\n{executionStderr}")
                else:
                    self.output_console.setText(f"✅ Output:\n\n{executionStdout}")
                return

            user_input, ok = QInputDialog.getMultiLineText(
                None, "Program Input", "Enter input for program:"
            )
            if not ok:
                user_input = ""

            runProcess = subprocess.Popen(
                runCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True
            )
            executionStdout, executionStderr = runProcess.communicate(input=user_input)

            if executionStderr:
                self.output_console.setText(f"❌ Execution Error:\n\n{executionStderr}")
            else:
                self.output_console.setText(f"✅ Output:\n\n{executionStdout}")

        except Exception as e:
            self.output_console.setText(f"⚠️ Error occurred: {str(e)}")

        finally:
            try:
                shutil.rmtree(tempdir, ignore_errors=True)
            except Exception as cleanup_error:
                print(f"⚠️ Cleanup failed: {cleanup_error}")
