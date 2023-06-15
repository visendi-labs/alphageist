from typing import NewType

State = NewType('State', str)

NEW:State = State("New")
CONFIGURED:State = State("Configured")
LOADING_VECTORSTORE = State("Loading Vectorstore")
ERROR:State = State("Error")
LOADING:State = State("Loading")
LOADED:State = State("Loaded")
STANDBY:State = State("Standby")
QUERYING:State = State("Querying")

