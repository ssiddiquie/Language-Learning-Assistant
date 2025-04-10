# database.py
from datetime import datetime
from typing import List, Dict

class MistakeDatabase:
    def __init__(self):
        """
        In-memory database structure:
        - sessions: {session_id: {session_data}}
        - mistakes: {session_id: [list_of_mistakes]}
        """
        self.sessions = {}
        self.mistakes = {}
        self.current_session_id = 1

    def create_session(self, language: str, level: str) -> int:
        """Create a new learning session"""
        session_id = self.current_session_id
        self.sessions[session_id] = {
            "language": language,
            "level": level,
            "start_time": datetime.now(),
            "end_time": None,
            "active": True
        }
        self.mistakes[session_id] = []
        self.current_session_id += 1
        return session_id

    def end_session(self, session_id: int):
        """Mark a session as completed"""
        if session_id in self.sessions:
            self.sessions[session_id]["end_time"] = datetime.now()
            self.sessions[session_id]["active"] = False

    def add_mistake(self, session_id: int, user_input: str, errors: List[Dict]):
        """Record a learner's mistake"""
        if session_id in self.mistakes:
            self.mistakes[session_id].append({
                "timestamp": datetime.now(),
                "user_input": user_input,
                "errors": errors
            })

    def get_session_mistakes(self, session_id: int) -> List[Dict]:
        """Retrieve all mistakes for a session"""
        return self.mistakes.get(session_id, [])

    def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        return [
            {"id": sid, **data} 
            for sid, data in self.sessions.items() 
            if data.get("active")
        ]

    def clear_all_data(self):
        """Reset the database (for testing)"""
        self.sessions = {}
        self.mistakes = {}
        self.current_session_id = 1