from typing import NewType

State = NewType('State', str)

ERROR:State = State("Error")
LOADING:State = State("Loading")
LOADED:State = State("Loaded")
NOT_LOADED:State = State("Not Loaded")
STANDBY:State = State("Standby")
QUERYING:State = State("Querying")

