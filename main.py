from ai.conversation_agent import ConversationAgent
from ai.groq_provider import GroqProvider
from ai.speech_to_text import SpeechToText

from brain.brain import Brain
from brain.state import State

brain = Brain()

provider = GroqProvider(
    model="llama-3.3-70b-versatile"
)

stt = SpeechToText()


agent = ConversationAgent(provider)

while True:

    user_text = input("\nTú: ")

    if user_text.lower() == "salir":
        break

    brain.set_state(State.THINKING)

    answer = agent.answer(user_text)

    brain.set_state(State.SPEAKING)

    print(f"\nKaito: {answer}")

    brain.set_state(State.IDLE)

    print()