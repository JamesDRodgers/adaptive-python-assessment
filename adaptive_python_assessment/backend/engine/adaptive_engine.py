import json
from engine.scoring import evaluate_answer, generate_followup_question
from models.session import SessionState

with open("backend/engine/questions.jsonl") as f:
    QUESTIONS = [json.loads(l) for l in f]

def select_question(bloom, difficulty, last_misconception):
    if last_misconception:
        return generate_followup_question(bloom, difficulty, last_misconception)
    for q in QUESTIONS:
        if q["bloom"]==bloom and q["difficulty"]==difficulty:
            return q
    return QUESTIONS[0]

def next_question(session: SessionState):
    if session.question_number > session.max_questions:
        session.finished=True
        return None
    q = select_question(session.bloom_level, session.difficulty, session.last_misconception)
    session.current_question = q
    return q

def score_response(session: SessionState, resp):
    evaluation = evaluate_answer(session.current_question, resp)
    session.record_evaluation(evaluation)

    if evaluation["final_score"]>=0.85:
        session.difficulty=min(5,session.difficulty+1)
        session.bloom_level=min(5,session.bloom_level+1)
    elif evaluation["final_score"]<0.5:
        session.difficulty=max(1,session.difficulty-1)

    if evaluation["misconceptions"]:
        session.last_misconception = evaluation["misconceptions"][0]
    else:
        session.last_misconception = None

    session.question_number+=1
    return evaluation
