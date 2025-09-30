from time import sleep
from typing import (
	Any, 
	Callable, 
	Optional
)

from utils.logger import Logger

logger = Logger(__name__)


def max_retries(
	times: int, 
    exceptions: Optional[Exception] = Exception, 
    sleep_time: float = 0.1
	) -> Callable: 
    def decorator(fn):
        def retry(*args, **kwargs):
            attempt = 0
            while attempt < times:
                try: 
                    return fn(*args, **kwargs)
                except: 
                    logger.error(
                        f"[{attempt}/{times}] {fn.__name__} call failed. Process will run again\n Exception: {str(exceptions)}"
					) 
                    attempt += 1
                    sleep(sleep_time)
            return fn(*args, **kwargs)
        return retry
    return decorator

