from enum import Enum


class APIStatus(str, Enum):
    ERROR: str = "error"
    COMPLETED: str = "completed"
    INPROGRESS: str = "in-progress"
    
