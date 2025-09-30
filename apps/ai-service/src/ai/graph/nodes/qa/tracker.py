from typing import Any, Dict, List
from ...types.qa import FlowPhase
from utils import Logger

logger = Logger(__name__)



class VerificationStepTracker:
    """Helper class to track verification steps and determine completion"""
    
    REQUIRED_STEPS = ["name", "phone", "dob"]
    STEP_ORDER = {"name": 0, "phone": 1, "dob": 2}
    
    @classmethod
    def is_complete(cls, collected_info: Dict[str, Any]) -> bool:
        """Check if all required verification steps are complete"""
        logger.info(f"Checking verification completion: {list(collected_info.keys())}")
        return all(
            step in collected_info and collected_info[step]
            for step in cls.REQUIRED_STEPS
        )
    
    @classmethod
    def get_next_step(cls, collected_info: Dict[str, Any]) -> str:
        """Get the next step needed in verification"""
        for step in cls.REQUIRED_STEPS:
            if step not in collected_info or not collected_info[step]:
                return step
        return "complete"
    
    @classmethod
    def get_missing_steps(cls, collected_info: Dict[str, Any]) -> List[str]:
        """Get list of missing verification steps"""
        return [
            step for step in cls.REQUIRED_STEPS 
            if step not in collected_info or not collected_info[step]
        ]
    
    @classmethod
    def get_step_index(cls, step: str) -> int:
        """Get the order index of a verification step"""
        return cls.STEP_ORDER.get(step, -1)
