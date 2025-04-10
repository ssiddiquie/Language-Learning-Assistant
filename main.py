import os
import json
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from database import MistakeDatabase
from langchain_core.prompts import (
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
        self.llm = None
        self.chain = None

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
            google_api_key=("API KEY")
        )
            
        system_template = SystemMessagePromptTemplate.from_template(
            f"""Act as a {self.learning_lang} tutor. Strictly follow these rules:
            1. Compare new inputs with previous taught content
            2. ALWAYS start responses with error analysis if mistakes exist
            3. Use this format:
            - Error Highlight → Explanation → Correction → Exercise
            4. Maintain 50% new material vs 50% reinforcement
            5. Never introduce new phrases without addressing mistakes
            6. Repeat phrases if there is any error 
            7. If no mistakes move to next phrase
            Current Level: {self.current_level}

            You are an expert {self.learning_lang} language tutor for {self.current_level} students. 
            Your goal is to provide comprehensive and engaging language instruction.

            Teaching based on level:
            * Currently your student wants to learn {self.learning_lang} at {self.current_level} level
            * Teaching must be level-appropriate:
            
            Beginner:
                Focus on Basic Communication:
                    - Vocabulary: Essential words (greetings, numbers, basic adjectives)
                    - Pronunciation: Clear enunciation of key sounds
                    - Simple Sentences: Subject-verb-object structures
                    - Common Phrases: Everyday interactions
                    - Listening: Slow, clear dialogues
                    - Grammar: Present tense, basic nouns
            
            Intermediate:
                Expand Expression & Comprehension:
                    - Vocabulary: Travel, hobbies, daily routines
                    - Pronunciation: Stress and intonation
                    - Complex Sentences: Compound structures
                    - Grammar: Past/future tenses, modals
                    - Listening: Podcasts, news
                    - Writing: Short essays, emails
            
            Expert:
                Nuance & Cultural Fluency:
                    - Vocabulary: Idioms, specialized terms
                    - Grammar: Advanced tenses
                    - Speaking: Abstract topics
                    - Listening: Native-speed content
                    - Writing: Formal documents
                    - Culture: Humor, historical context
            
            Master:
                Near-Native Proficiency:
                    - Vocabulary: Rare/specialized terms
                    - Pronunciation: Regional variations
                    - Expression: Subtle nuances
                    - Listening: Complex media
                    - Writing: Creative/professional work
                    - Culture: Social contexts

            Teaching Philosophy:
            * Focus on {self.level_config['focus']}
            * Responses < {self.level_config['max_length']} words
            * Primary language: {self.learning_lang}
            * English explanations in brackets
            * Gentle error correction
            * Cultural insights
            * Encouraging tone
            * Varied exercises

            Required Components:
            1. Target Phrase/Word
            2. Pronunciation (*italics*)
            3. Literal Translation
            4. Grammatical Breakdown
            5. Contextual Usage
            6. Interactive Exercise
            7. Cultural Note (when relevant)

            Example Interaction:
            User: Hi
            AI:
            * Target: こんにちは (Konnichiwa)
            * Pronunciation: *Konnichiwa*
            * Translation: Hello
            * Grammar: Daytime greeting
            * Usage: こんにちは、元気ですか？
            * Exercise: Translate "Good afternoon"
            * Culture: Bowing etiquette"""
        )
        # Create prompt chain with memory
        self.prompt = ChatPromptTemplate.from_messages([
            system_template,
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{text}")
        ])
        
        # Initialize the chain
        self.chain = self.prompt | self.llm
        
    def end_session(self):
        if self.current_session_id:
            self.db.end_session(self.current_session_id)
            self.current_session_id = None
            self.memory.clear()
            self.chain = None


    def _analyze_errors(self, user_input: str) -> List[Dict]:
        analysis_prompt = f"""Analyze this {self.learning_lang} text from a {self.current_level} learner:
        Text: '{user_input}'
        
        Return STRICT JSON format with this structure:
        {{
            "errors": [
                {{
                    "type": "grammar/vocabulary/pronunciation/cultural",
                    "incorrect_part": "exact text that's wrong",
                    "correct_version": "corrected version",
                    "explanation": "simple explanation",
                    "severity": "low/medium/high"
                }}
            ]
        }}
        
        Example:
        {{
            "errors": [
                {{
                    "type": "pronunciation",
                    "incorrect_part": "namate",
                    "correct_version": "namaste",
                    "explanation": "Missing 's' sound in greeting",
                    "severity": "medium"
                }}
            ]
        }}"""

        try:
            response = self.llm.invoke(analysis_prompt)
            if not response.content.strip():
                print("Error: Empty response from LLM")
                return []
                
            # First try parsing directly
            try:
                result = json.loads(response.content)
                if "errors" in result:
                    return result["errors"]
                return []
            except json.JSONDecodeError:
                # If direct parse fails, try extracting JSON from markdown
                json_str = response.content.split("```json")[-1].split("```")[0].strip()
                result = json.loads(json_str)
                return result.get("errors", [])
                
        except Exception as e:
            print(f"Error analysis failed. Raw response: {response.content if 'response' in locals() else 'No response'}")
            print(f"Error details: {str(e)}")
            return []


    def generate_response(self, user_input: str) -> str:
        if not self.chain:
            return "Please start a session first"
            
        errors = self._analyze_errors(user_input)
        
        if self.current_session_id and errors:
            self.db.add_mistake(
                session_id=self.current_session_id,
                user_input=user_input,
                errors=errors
            )

        history = self.memory.load_memory_variables({})["history"]
        response = self.chain.invoke({"text": user_input, "history": history})
        ai_response = response.content
        
        self.memory.save_context({"input": user_input}, {"output": ai_response})
        return ai_response
        
    def generate_session_report(self) -> str:
        if not self.current_session_id:
            return "No active session"
            
        mistakes = self.db.get_session_mistakes(self.current_session_id)
        if not mistakes:
            return "Perfect session! No mistakes found!"
        
        report_prompt = f"""Create learning report for {self.current_level} {self.learning_lang} learner:
        - Total mistakes: {len(mistakes)}
        - Error types: {', '.join(set(m['errors'][0]['error_type'] for m in mistakes))}
        Format: Markdown with analysis and recommendations"""
        
        response = self.llm.invoke(report_prompt)
        return response.content