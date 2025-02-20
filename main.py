from langchain.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from sentence_transformers import SentenceTransformer
import numpy as np
# import chromadb
from database import create_messages_db
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
        
        create_messages_db()
        
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

    def process_query_stream(self, language, code, query, scenario):
        if scenario not in self.scenario_map:
            raise ValueError(f"Invalid scenario. Choose from: {list(self.scenario_map.keys())}")
        
        self.current_state['scenario'] = scenario
        self.current_state['scenario_context'] = self.scenario_map[scenario]
        self.current_state['language'] = language

        relevant_docs = self.retrieve_relevant_docs(query)
        docs_text = "\n\n".join([doc[3] for doc in relevant_docs])
        print(docs_text)
        
        initial_template = PromptTemplate(
            input_variables=['input', 'language', 'scenario', 'scenario_context', 'code_context', 'libraries', 'docs'],
            template=INITIAL_TEMPLATE
        )
        
        chain = self.create_llm_chain(initial_template)
        response = chain.run(
            input=code,
            code_context=query,
            language=self.current_state['language'],
            scenario=self.current_state['scenario'],
            scenario_context=self.current_state['scenario_context'],
            libraries=self.current_state['libraries'],
            docs=docs_text    
        )
        
        lines = response.splitlines()
        for line in lines:
            if line.strip(): 
                yield line + "\n"  
                QThread.msleep(100)  
                
    def create_llm_chain(self, prompt_template):
        memory = ConversationBufferMemory(input_key="input", memory_key="chat_history")
        llm = Ollama(model="qwen2.5-coder:7b", temperature=self.current_state['temperature'])
        return LLMChain(llm=llm, prompt=prompt_template, memory=memory)