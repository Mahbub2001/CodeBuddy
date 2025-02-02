import os
import re
import sqlite3
import base64
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import LLMChain, ConversationalRetrievalChain
from prompts import (
    CHAT_TEMPLATE, INITIAL_TEMPLATE, CORRECTION_CONTEXT,
    COMPLETION_CONTEXT, OPTIMIZATION_CONTEXT, GENERAL_ASSISTANT_CONTEXT,
    GENERATION_CONTEXT, COMMENTING_CONTEXT, EXPLANATION_CONTEXT,
    LEETCODE_CONTEXT, SHORTENING_CONTEXT
)
from database import create_messages_db, write_to_messages_db, get_all_thread_messages,get_unique_thread_ids
class CodeBuddyConsole:
    def __init__(self):
        self.current_state = {
            'chat_history': [],
            'initial_input': "",
            'initial_context': "",
            'scenario_context': "",
            'thread_id': "",
            'docs_processed': False,
            'docs_chain': None,
            'uploaded_docs': None,
            'language': "Python",
            'scenario': "General Assistant",
            'temperature': 0.5,
            'libraries': []
        }
        
        self.scenario_map = {
            "General Assistant": GENERAL_ASSISTANT_CONTEXT,
            "Code Correction": CORRECTION_CONTEXT,
            "Code Completion": COMPLETION_CONTEXT,
            "Code Optimization": OPTIMIZATION_CONTEXT,
            "Code Generation": GENERATION_CONTEXT,
            "Code Commenting": COMMENTING_CONTEXT,
            "Code Explanation": EXPLANATION_CONTEXT,
            "LeetCode Solver": LEETCODE_CONTEXT,
            "Code Shortener": SHORTENING_CONTEXT
        }
        
        self.languages = ['Python', 'GoLang', 'TypeScript', 'JavaScript', 
                         'Java', 'C', 'C++', 'C#', 'R', 'SQL']
        
        create_messages_db()
    
    def process_query(self,language, code, query, scenario):
        """Process a query with the given code and scenario, returning the AI's response."""
        if scenario not in self.scenario_map:
            raise ValueError(f"Invalid scenario. Choose from: {list(self.scenario_map.keys())}")
        
        self.current_state['scenario'] = scenario
        self.current_state['scenario_context'] = self.scenario_map[scenario]
        self.current_state['language'] = language
        
        initial_template = PromptTemplate(
            input_variables=['input', 'language', 'scenario', 'scenario_context', 'code_context', 'libraries'],
            template=INITIAL_TEMPLATE
        )
        
        if self.current_state['docs_processed']:
            chain = self.current_state['docs_chain']
            llm_input = initial_template.format(
                input=code,
                code_context=query,
                language=self.current_state['language'],
                scenario=self.current_state['scenario'],
                scenario_context=self.current_state['scenario_context'],
                libraries=self.current_state['libraries']
            )
            response = chain({'question': llm_input})['answer']
        else:
            chain = self.create_llm_chain(initial_template)
            response = chain.run(
                input=code,
                code_context=query,
                language=self.current_state['language'],
                scenario=self.current_state['scenario'],
                scenario_context=self.current_state['scenario_context'],
                libraries=self.current_state['libraries']
            )
        
        return response

    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        self.clear_screen()
        print("=== CodeBuddy Console ===")
        print(f"Current Settings - Language: {self.current_state['language']}, "
              f"Scenario: {self.current_state['scenario']}, "
              f"Temp: {self.current_state['temperature']}")
        print("-------------------------")
    
    def main_menu(self):
        self.show_header()
        print("1. Start New Chat")
        print("2. Load Previous Chat")
        print("3. Change Settings")
        print("4. Process Documents")
        print("5. Exit")
        choice = input("Select option: ")
        return choice
    
    def settings_menu(self):
        self.show_header()
        print("=== Settings ===")
        
        # Language selection
        print("\nAvailable Languages:")
        for i, lang in enumerate(self.languages, 1):
            print(f"{i}. {lang}")
        lang_choice = input(f"Select language (1-{len(self.languages)}): ")
        self.current_state['language'] = self.languages[int(lang_choice)-1]
        
        # Scenario selection
        print("\nAvailable Scenarios:")
        for key in self.scenario_map:
            print(f"{key}. {self.scenario_map[key][0]}")
        scenario_choice = input("Select scenario (1-9): ")
        self.current_state['scenario'], self.current_state['scenario_context'] = self.scenario_map[scenario_choice]
        
        # Temperature
        temp = float(input("Enter temperature (0.0-1.0): "))
        self.current_state['temperature'] = temp
        
        # Python libraries
        if self.current_state['language'] == "Python":
            print("\nAvailable Python Libraries:")
            python_libs = ['SQLite', 'PyGame', 'Seaborn', "Pandas", 'Numpy', 
                          'Scipy', 'Scikit-Learn', 'PyTorch', 'TensorFlow', 
                          'Streamlit', 'Flask', 'FastAPI']
            for i, lib in enumerate(python_libs, 1):
                print(f"{i}. {lib}")
            lib_choices = input("Select libraries (comma-separated, leave empty to skip): ")
            if lib_choices:
                indices = [int(c.strip())-1 for c in lib_choices.split(",")]
                self.current_state['libraries'] = [python_libs[i] for i in indices]
    
    def document_processing(self):
        self.show_header()
        print("=== Document Processing ===")
        file_paths = input("Enter PDF file paths (comma-separated): ").split(",")
        
        if file_paths:
            raw_text = self.get_pdf_text([fp.strip() for fp in file_paths])
            text_chunks = self.get_text_chunks(raw_text)
            vectorstore = self.get_vectorstore(text_chunks)
            self.current_state['docs_chain'] = self.create_retrieval_chain(vectorstore)
            self.current_state['docs_processed'] = True
            self.current_state['uploaded_docs'] = file_paths
            print(f"\nProcessed {len(file_paths)} documents successfully!")
        else:
            self.current_state['docs_processed'] = False
        input("\nPress Enter to continue...")
    
    def get_pdf_text(self, pdf_paths):
        text = ""
        for path in pdf_paths:
            with open(path, 'rb') as f:
                pdf_reader = PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        return text
    
    def get_text_chunks(self, text):
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        return text_splitter.split_text(text)
    
    def get_vectorstore(self, text_chunks):
        embeddings = OpenAIEmbeddings()
        return FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    
    def create_retrieval_chain(self, vectorstore):
        llm = Ollama(model="qwen2.5-coder:7b", temperature=self.current_state['temperature'])
        memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
        return ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            memory=memory
        )
    
    def create_llm_chain(self, prompt_template):
        memory = ConversationBufferMemory(input_key="input", memory_key="chat_history")
        llm = Ollama(model="qwen2.5-coder:7b", temperature=self.current_state['temperature'])
        return LLMChain(llm=llm, prompt=prompt_template, memory=memory)
    
    def start_new_chat(self):
        self.show_header()
        print("=== New Chat ===")
        code_input = input("Enter your code (press Enter twice to finish):\n")
        code_context = input("\nEnter any additional context: ")
        
        # Create initial prompt
        initial_template = PromptTemplate(
            input_variables=['input', 'language', 'scenario', 'scenario_context', 'code_context', 'libraries'],
            template=INITIAL_TEMPLATE
        )
        
        if self.current_state['docs_processed']:
            chain = self.current_state['docs_chain']
            llm_input = initial_template.format(
                input=code_input,
                code_context=code_context,
                language=self.current_state['language'],
                scenario=self.current_state['scenario'],
                scenario_context=self.current_state['scenario_context'],
                libraries=self.current_state['libraries']
            )
            response = chain({'question': llm_input})['answer']
        else:
            chain = self.create_llm_chain(initial_template)
            response = chain.run(
                input=code_input,
                code_context=code_context,
                language=self.current_state['language'],
                scenario=self.current_state['scenario'],
                scenario_context=self.current_state['scenario_context'],
                libraries=self.current_state['libraries']
            )
        
        # Update state
        self.current_state['initial_input'] = code_input
        self.current_state['initial_context'] = code_context
        self.current_state['thread_id'] = (code_context + code_input)[:40]
        self.current_state['chat_history'] = [
            f"USER: CODE CONTEXT: {code_context} CODE INPUT: {code_input}",
            f"AI: {response}"
        ]
        
        # Write to DB
        write_to_messages_db(
            self.current_state['thread_id'],
            'USER',
            f"USER: CODE CONTEXT: {code_context} CODE INPUT: {code_input}"
        )
        write_to_messages_db(
            self.current_state['thread_id'],
            'AI',
            f"AI: {response}"
        )
        
        print("\nAI Response:")
        print(response)
        input("\nPress Enter to continue conversation...")
        self.chat_loop()
    
    def chat_loop(self):
        chat_template = PromptTemplate(
            input_variables=[
                'input', 'language', 'scenario', 'scenario_context',
                'chat_history', 'libraries', 'code_input', 
                'code_context', 'most_recent_ai_message'
            ],
            template=CHAT_TEMPLATE
        )
        
        while True:
            self.show_header()
            print("=== Chat History ===")
            for msg in self.current_state['chat_history'][-6:]:
                if msg.startswith("USER:"):
                    print(f"> User: {msg[6:]}")
                else:
                    print(f"> AI: {msg[5:]}")
            print("\n")
            
            user_input = input("Enter your message (or 'exit' to quit): ")
            if user_input.lower() == 'exit':
                break
            
            if self.current_state['docs_processed']:
                chain = self.current_state['docs_chain']
                llm_input = chat_template.format(
                    input=user_input,
                    language=self.current_state['language'],
                    scenario=self.current_state['scenario'],
                    scenario_context=self.current_state['scenario_context'],
                    libraries=self.current_state['libraries'],
                    code_input=self.current_state['initial_input'],
                    code_context=self.current_state['initial_context'],
                    most_recent_ai_message=self.current_state['chat_history'][-1]
                )
                response = chain({'question': llm_input})['answer']
            else:
                chain = self.create_llm_chain(chat_template)
                response = chain.run(
                    input=user_input,
                    language=self.current_state['language'],
                    scenario=self.current_state['scenario'],
                    scenario_context=self.current_state['scenario_context'],
                    chat_history=self.current_state['chat_history'],
                    libraries=self.current_state['libraries'],
                    code_input=self.current_state['initial_input'],
                    code_context=self.current_state['initial_context'],
                    most_recent_ai_message=self.current_state['chat_history'][-1]
                )
            
            # Update state and DB
            self.current_state['chat_history'].extend([
                f"USER: {user_input}",
                f"AI: {response}"
            ])
            write_to_messages_db(
                self.current_state['thread_id'],
                'USER',
                f"USER: {user_input}"
            )
            write_to_messages_db(
                self.current_state['thread_id'],
                'AI',
                f"AI: {response}"
            )
            
            print("\nAI Response:")
            print(response)
            input("\nPress Enter to continue...")
    
    def load_previous_chat(self):
        self.show_header()
        print("=== Previous Chats ===")
        threads = get_unique_thread_ids()
        if not threads:
            input("No previous chats found. Press Enter to return...")
            return
        
        for i, thread in enumerate(threads, 1):
            print(f"{i}. {thread}")
        choice = int(input("\nSelect chat to load: ")) - 1
        self.current_state['thread_id'] = threads[choice]
        self.current_state['chat_history'] = get_all_thread_messages(threads[choice])
        print("\nLoaded chat history:")
        for msg in self.current_state['chat_history'][-6:]:
            print(f"> {msg}")
        input("\nPress Enter to continue...")
        self.chat_loop()
    
    def run(self):
        while True:
            choice = self.main_menu()
            if choice == '1':
                self.start_new_chat()
            elif choice == '2':
                self.load_previous_chat()
            elif choice == '3':
                self.settings_menu()
            elif choice == '4':
                self.document_processing()
            elif choice == '5':
                print("Exiting CodeBuddy...")
                break
            else:
                print("Invalid choice, please try again.")
                input("Press Enter to continue...")

if __name__ == "__main__":
    app = CodeBuddyConsole()
    app.run()