from enum import Enum


class State(Enum):

    SLEEPING = "sleeping"

    IDLE = "idle"

    LISTENING = "listening"

    THINKING = "thinking"

    SPEAKING = "speaking"