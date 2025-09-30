import pytz
from datetime import datetime
from time import time

DATE_STR = "%Y-%m-%d %H:%M:%S.%f%z"


class TimeHandler:
    """ Class to handle time """    
    @staticmethod
    def get_timestamp(tz: str = "Brazil/West") -> str:
        """ Method to get formatted timestamp

        Returns:
            str: Formatted timestamp
        """        
        return datetime.now(tz=pytz.timezone(tz)).strftime(DATE_STR)
    
    @staticmethod
    def get_time() -> float:
        """ Method to get current time

        Returns:
            float: current time
        """        
        return time()

    @staticmethod
    def calculate_time_difference(timestamp1: str, timestamp2: str) -> float:
        """ Method to calculate the time difference between two timestamps

        Args:
            timestamp1 (str): The first timestamp
            timestamp2 (str): The second timestamp

        Returns:
            float: The difference in seconds between the two timestamps
        """
        # Parse the timestamps with UTC offset
        dt1 = datetime.strptime(timestamp1, DATE_STR)
        dt2 = datetime.strptime(timestamp2, DATE_STR)
        
        # Calculate the difference in seconds
        time_difference = abs((dt2 - dt1).total_seconds())
        
        return time_difference
