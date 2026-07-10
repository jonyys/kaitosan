import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Conectando con Groq...")

stream = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "system",
            "content": "Eres un robot asistente de escritorio simpatico y conciso. Respondes siempre en español."
        },
        {
            "role": "user",
            "content": "Hola, puedes presentarte?"
        }
    ],
    stream=True,
    max_tokens=150
)

for chunk in stream:
    token = chunk.choices[0].delta.content
    if token:
        print(token, end="", flush=True)