from brain.state import State


class Brain:

    def __init__(self):

        self._state = State.IDLE

    def get_state(self):

        return self._state

    def set_state(self, state):

        if self._state == state:
            return

        self._state = state

        print(f"\nEstado -> {state.value}")