from langchain.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from sentence_transformers import SentenceTransformer
import numpy as np
# import chromadb
from prompts import (
    CHAT_TEMPLATE, INITIAL_TEMPLATE, CORRECTION_CONTEXT,
    COMPLETION_CONTEXT, OPTIMIZATION_CONTEXT, GENERAL_ASSISTANT_CONTEXT,
    GENERATION_CONTEXT, COMMENTING_CONTEXT, EXPLANATION_CONTEXT,
    LEETCODE_CONTEXT, SHORTENING_CONTEXT
)
import sqlite3
from PyQt6.QtCore import QThread  

def generate_embeddings(text, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    return model.encode([text])[0].tolist()  

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
    
    def retrieve_relevant_docs(self, query, top_k=3, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        conn = sqlite3.connect("embeddings.db")
        cursor = conn.cursor()

        query_embedding = generate_embeddings(query, model_name)
        query_embedding_array = np.array(query_embedding, dtype=np.float32)

        cursor.execute('''
            SELECT doc_id, chunk_id, chunk, embedding
            FROM embeddings
        ''')

        results = []
        for doc_id, chunk_id, chunk, embedding_blob in cursor.fetchall():
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            similarity = np.dot(query_embedding_array, embedding) / (np.linalg.norm(query_embedding_array) * np.linalg.norm(embedding))
            results.append((similarity, doc_id, chunk_id, chunk))

        results.sort(reverse=True, key=lambda x: x[0])
        
        return results[:top_k]

    def get_conversation_history(self, session_id):
            conn = sqlite3.connect('conversation_history.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_query, ai_response FROM conversations
                WHERE session_id = ?
                ORDER BY timestamp
            ''', (session_id,))
            history = cursor.fetchall()
            conn.close()
            return history

    def process_query_stream(self, language, code, query, scenario, session_id):
        if scenario not in self.scenario_map:
            raise ValueError(f"Invalid scenario. Choose from: {list(self.scenario_map.keys())}")
        
        self.current_state['scenario'] = scenario
        self.current_state['scenario_context'] = self.scenario_map[scenario]
        self.current_state['language'] = language

        history = self.get_conversation_history(session_id)  
        chat_history = self.format_conversation_history(history)

        relevant_docs = self.retrieve_relevant_docs(query)
        docs_text = "\n\n".join([doc[3] for doc in relevant_docs])
        if not history:
            prompt_template = PromptTemplate(
                input_variables=['input', 'language', 'scenario', 'scenario_context', 'code_context', 'libraries', 'docs', 'chat_history'],
                template=INITIAL_TEMPLATE
            )
        else:
            prompt_template = PromptTemplate(
                input_variables=['input', 'language', 'scenario', 'scenario_context', 'code_context', 'libraries', 'docs', 'chat_history', 'most_recent_ai_message', 'code_input'],
                template=CHAT_TEMPLATE
            )
            most_recent_ai_message = history[-1][1] if history else ""

        chain = self.create_llm_chain(prompt_template)
        
        if not history:
            response = chain.run(
                input=code,
                code_context=query,
                language=self.current_state['language'],
                scenario=self.current_state['scenario'],
                scenario_context=self.current_state['scenario_context'],
                libraries=self.current_state['libraries'],
                docs=docs_text,
                chat_history=chat_history
            )
        else:
            response = chain.run(
                input=query, 
                code_context=query,  
                language=self.current_state['language'],
                scenario=self.current_state['scenario'],
                scenario_context=self.current_state['scenario_context'],
                libraries=self.current_state['libraries'],
                docs=docs_text,
                chat_history=chat_history,
                most_recent_ai_message=most_recent_ai_message,
                code_input=code  
            )
        
        conn = sqlite3.connect('conversation_history.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (session_id, user_query, ai_response)
            VALUES (?, ?, ?)
        ''', (session_id, query, response))
        conn.commit()
        conn.close()

        formatted_response = "\n".join(line for line in response.splitlines() if line.strip())
        yield formatted_response
    
    def format_conversation_history(self, history):
        return "\n".join([f"User: {q}\nAI: {a}" for q, a in history])

    def create_llm_chain(self, prompt_template):
        memory = ConversationBufferMemory(input_key="input", memory_key="chat_history")
        llm = Ollama(model="qwen2.5-coder:7b", temperature=self.current_state['temperature'])
        return LLMChain(llm=llm, prompt=prompt_template, memory=memory)