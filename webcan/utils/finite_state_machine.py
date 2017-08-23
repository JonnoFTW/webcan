class State:
    def __init__(self, name):
        self.name = name
        self.transitions = {}

    def add_transition(self, other_state, condition):
        self.transitions[other_state] = condition


class FSM:
    def __init__(self):
        self.states = []
        self.current_state = None
        self.last_value = None
    def add_state(self, state):
        self.states.append(state)

    def start(self, state):
        if state not in self.states:
            raise ValueError("Please start on a state in this machine")
        self.current_state = state
    def run(self, value):
        if self.last_value is None:
            self.last_value = value

        self.last_value = value


if __name__ == "__main__":
    fsm = FSM()
    idle_state = State("Idle")
