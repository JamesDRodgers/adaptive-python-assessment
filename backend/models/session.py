from datetime import datetime

# Constants for validation
MAX_QUESTIONS = 15
MIN_QUESTIONS = 5


class SessionState:
    def __init__(self, max_questions: int = MAX_QUESTIONS):
        """
        Initialize a new session state.
        
        Args:
            max_questions: Number of questions in the assessment (default: 15)
        
        Raises:
            ValueError: If max_questions is outside allowed range
        """
        if not MIN_QUESTIONS <= max_questions <= MAX_QUESTIONS:
            raise ValueError(f"max_questions must be between {MIN_QUESTIONS} and {MAX_QUESTIONS}")
        
        self.max_questions = max_questions
        self.reset()

    def reset(self):
        """Reset the session to initial state."""
        self.bloom_level = 1
        self.difficulty = 1
        self.question_number = 1
        self.current_question = None
        self.finished = False
        self.history = []
        self.last_misconception = None
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def record_evaluation(self, e):
        """
        Record an evaluation in the session history.
        
        Args:
            e: Evaluation dictionary with scores and misconceptions
        """
        self.history.append(e)
        self.last_activity = datetime.now()

    def summary(self):
        """
        Generate a summary of the assessment session.
        
        Returns:
            Dictionary containing average scores and response history
        """
        # Protection against division by zero
        if not self.history:
            return {
                "final_score": 0.0,
                "average_accuracy": 0.0,
                "average_explanation": 0.0,
                "responses": []
            }
        
        acc = sum(i['accuracy'] for i in self.history) / len(self.history)
        exp = sum(i['explanation_score'] for i in self.history) / len(self.history)
        final = sum(i['final_score'] for i in self.history) / len(self.history)
        
        return {
            "final_score": final,
            "average_accuracy": acc,
            "average_explanation": exp,
            "responses": self.history
        }
