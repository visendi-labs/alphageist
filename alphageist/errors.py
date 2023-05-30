
class MissingConfigComponentError(Exception):
    def __init__(self, missing_key:str):
        super().__init__(f"Missing config key: {missing_key}")
