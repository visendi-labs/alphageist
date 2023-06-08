from alphageist import state

class Alphageist:
    vectorstore_state: state.State
    query_state: state.State

    def __init__(self):
        self.vectorstore_state = state.NOT_LOADED
        self.query_state = state.STANDBY