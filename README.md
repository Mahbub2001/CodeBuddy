# CodeBuddy - AI-Powered Code Assistant

## Overview
CodeBuddy is an AI-powered code assistant designed to streamline coding tasks with an integrated development environment (IDE). It leverages Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) to provide intelligent code assistance, including correction, completion, optimization, generation, commenting, explanation, and LeetCode problem-solving.

## Key Features
- **AI-Powered Code Assistance**: Get real-time help with code correction, completion, optimization, and generation.
- **LeetCode Solver**: AI-generated solutions for coding problems.
- **Code Shortener**: Simplify and refactor your code efficiently.
- **Multi-Language Support**: Supports Currently C, C++. But Later It will Upgrade for Java, Python, and more.
- **Semantic Search**: Retrieve relevant documentation and code snippets using embeddings.
- **Interactive IDE**: Includes a file explorer, code editor, and output console.
- **Auto-Save**: Ensures your work is saved at regular intervals.
- **Customizable AI Assistants**: Tailor AI assistance to specific tasks.

## Installation
### Prerequisites
- Python 3.8 or higher
- SQLite3
- PyQt6
- Ollama (for local LLM integration)-qwen2.5-coder:7b,deepseek-r1:8b,llava:latest 
- Sentence Transformers

### Setup Instructions
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Mahbub2001/CodeBuddy.git
   cd CodeBuddy
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up the database**:
   ```bash
   python ingest.py
   ```
4. **Run the application**:
   ```bash
   python ui.py
   ```

## Usage
1. **Launch the IDE**: Run `python main.py` to start CodeBuddy.
2. **Open or Create a File**: Use the file explorer to manage your files.
3. **Write Code**: Utilize the editor for writing and modifying code.
4. **Use AI Assistance**: Select an AI assistant and enter a prompt for real-time suggestions.
5. **Run Code**: Click "Run" to execute your code and view output in the console.

## File Structure
```
CodeBuddy/
│-- main.py        # Core logic for AI assistance
│-- ui.py          # IDE UI implementation
│-- ide.py         # Main IDE functionality with code execution. Currently working for C language
│-- sidebar.py     # File explorer management
│-- database.py    # Handles database operations
│-- prompts.py     # Contains predefined AI prompt templates
│-- README.md      # Project documentation
```

## Configuration
- **Language Selection**: Choose a programming language from the dropdown menu.
- **Assistant Selection**: Pick an AI assistant (e.g., Code Correction, Completion, Generation).
- **Auto-Save**: Adjust auto-save settings in `ui.py`.


## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments
- **PyQt6** for the GUI framework.
- **Ollama** for local LLM integration.
- **Sentence Transformers** for text embeddings.

## Upcoming Work
- Implement Web scraping for Knowledge 
- Fine Tune LLM
- Another New Features 

