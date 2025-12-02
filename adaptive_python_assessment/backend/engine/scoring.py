import os, json, re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def evaluate_answer(question, resp):
    prompt = f"""Evaluate response.

Question: {question['question']}
Correct Answer: {question['answer']}
Student Answer: {resp['student_answer']}
Explanation: {resp['explanation']}

Return JSON: {{
 "accuracy":float,
 "explanation_score":float,
 "final_score":float,
 "misconceptions":[]
}}
"""

    r = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return json.loads(r.output_text)

def generate_followup_question(bloom, difficulty, misconception):
    prompt = f"""Generate Python Module 1 question.

Bloom: {bloom}
Difficulty: {difficulty}
Misconception: {misconception}

Return JSON: {{
 "id":999,
 "bloom":{bloom},
 "difficulty":{difficulty},
 "question":"..",
 "answer":"..",
 "misconceptions":[]
}}
"""
    r = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return json.loads(r.output_text)
