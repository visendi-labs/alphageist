from alphageist import state

class Alphageist:
    vectorstore_state: state.State
    query_state: state.State
    config: dict

    def __init__(self, config: dict):
        self.config = config
        self.vectorstore_state = state.NOT_LOADED
        self.query_state = state.STANDBY