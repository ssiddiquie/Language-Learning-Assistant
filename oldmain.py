import os
import json
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from database import MistakeDatabase
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

class LanguageLearningAssistant:
    def __init__(self):
        self.available_languages = {
            'hindi': 'Hindi',
            'spanish': 'Spanish',
            'french': 'French',
            'japanese': 'Japanese',
            'chinese': 'Chinese'
        }
        self.levels = {
            'beginner': {'focus': 'basic words and numerals', 'max_length': 3},
            'intermediate': {'focus': 'sentence construction', 'max_length': 8},
            'expert': {'focus': 'cultural fluency', 'max_length': 15},
            'master': {'focus': 'natural conversations', 'max_length': 30}
        }
        self.memory = ConversationBufferMemory(
            memory_key="history",
            return_messages=True
        )
        self.db = MistakeDatabase()
        self.current_session_id = None

    def start_session(self, learning_lang: str, level: str):
        """Start a new learning session with memory"""
        self.learning_lang = self.available_languages[learning_lang.lower()]
        self.level_config = self.levels[level.lower()]
        self.current_level = level.lower()
        
        # Create database session
        self.current_session_id = self.db.create_session(
            language=self.learning_lang,
            level=self.current_level
        )
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=("Gemini key")
        )
            
        system_template = SystemMessagePromptTemplate.from_template(
            f"""You are a {self.learning_lang} tutor for {self.current_level} learners.
            Focus on: {self.level_config['focus']}. Keep responses under {
                self.level_config['max_length']} words.
            Rules:
            1. Respond in {self.learning_lang}
            2. Include English explanations in brackets
            3. Politely correct major errors
            4. Highlight cultural context
            5. Always include romanization (Latin script) and a english translation after native script
            6. Follow this pattern:
            - Romanization (parentheses)
            - Simple English translation
            - Contextual example
            
            Example for Japanese:
            こんにちは！(Konnichiwa!) - Hello! 
            It is said when... etc."""

        )
        
        
        # Create prompt chain with memory
        self.prompt = ChatPromptTemplate.from_messages([
            system_template,
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{text}")
        ])
        
        self.chain = self.prompt | self.llm
        
    def end_session(self):
        """Cleanly terminate the current session"""
        if self.current_session_id:
            self.db.end_session(self.current_session_id)
            self.current_session_id = None
            self.memory.clear()

    def _analyze_errors(self, user_input: str) -> List[Dict]:
        """Perform error analysis using Gemini"""
        analysis_prompt = f"""Analyze this {self.learning_lang} text from a {
            self.current_level} learner:
        Text: '{user_input}'
        
        Return JSON list with:
        - error_type (grammar/vocabulary/pronunciation/cultural)
        - incorrect_part
        - correction
        - explanation
        - severity (low/medium/high)"""

        try:
            response = self.llm.invoke(analysis_prompt)
            return json.loads(response.content)
        except Exception as e:
            print(f"Error analysis failed: {e}")
            return []

    def generate_response(self, user_input: str) -> str:
        """Process user input with memory context and generate response"""
        # Analyze and store errors
        if self.current_session_id:
            errors = self._analyze_errors(user_input)
            if errors:
                self.db.add_mistake(
                    session_id=self.current_session_id,
                    user_input=user_input,
                    errors=errors
                )

        # Get historical context from memory
        history = self.memory.load_memory_variables({})["history"]
        
        # Generate response with context
        response = self.chain.invoke({
            "text": user_input,
            "history": history
        })
        ai_response = response.content
        
        # Store interaction in memory
        self.memory.save_context(
            {"input": user_input},
            {"output": ai_response}
        )
        
        return ai_response
        
    def generate_session_report(self) -> str:
        """Generate comprehensive learning report"""
        if not self.current_session_id:
            return "No active session to generate report for"
            
        mistakes = self.db.get_session_mistakes(self.current_session_id)
        if not mistakes:
            return "Perfect session! No mistakes found!"
        
        report_prompt = f"""Create a learning report for a {self.current_level} {
            self.learning_lang} learner:
        
        Session Data:
        - Language: {self.learning_lang}
        - Level: {self.current_level}
        - Total mistakes: {len(mistakes)}
        
        Analysis Requirements:
        1. Categorize error types
        2. Highlight frequent mistakes
        3. Suggest targeted exercises
        4. Provide cultural tips
        5. Recommend study resources
        
        Format: Markdown with headings and bullet points"""
        
        response = self.llm.invoke(report_prompt)
        return response.content