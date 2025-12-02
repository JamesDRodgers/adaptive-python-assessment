from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from engine.adaptive_engine import next_question, score_response
from models.session import SessionState

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SESSION = SessionState()

@app.get("/start")
def start():
    SESSION.reset()
    return {"question": next_question(SESSION)}

@app.post("/answer")
def answer(response: dict):
    evaluation = score_response(SESSION, response)
    if SESSION.finished:
        return {"evaluation": evaluation, "finished": True, "summary": SESSION.summary()}
    return {"evaluation": evaluation, "finished": False, "next_question": next_question(SESSION)}
