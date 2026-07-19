from transformers import pipeline
from fastapi import FastAPI, Response
from pydantic import BaseModel

generator = pipeline('text-generation', model='gpt2')

app = FastAPI()

class Body(BaseModel):
    text: str

@app.get('/')
def root():
    return Response("<h1>A self-documenting API to interact with a GPT2 model and generate text</h1>")

# REQUIRED LAB ROUTE
@app.get("/lab")
def lab():
    return {"request": "GET"}

# Text generation
@app.post("/generate")
def generate_text(body: Body):
    results = generator(
        body.text,
        max_length=35,
        num_return_sequences=1,
        truncation=True
    )
    return {"generated_text": results[0]["generated_text"]}