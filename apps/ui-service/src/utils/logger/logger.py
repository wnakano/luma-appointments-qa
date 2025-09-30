import logging


class Logger:
	"""
	A Logger class that encapsulates logging functionality for streamlined logging setup 
	with support for console and optional file output.

	Parameters
	----------
	name : str
		Name of the logger, usually `__name__` when used in scripts.
	log_file : str, optional
		Path to a file where logs should be written. If None, logs are only output to console.
	level : int, optional
		Logging level, by default `logging.DEBUG`.

	Attributes
	----------
	logger : logging.Logger
		The logger instance configured for console and optional file output.
	"""

	def __init__(self, name, log_file=None, level=logging.INFO):
		self._logger = logging.getLogger(name)
		self._logger.setLevel(level)

		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

		console_handler = logging.StreamHandler()
		console_handler.setLevel(level)
		console_handler.setFormatter(formatter)
		self._logger.addHandler(console_handler)

		if log_file:
			file_handler = logging.FileHandler(log_file)
			file_handler.setLevel(level)
			file_handler.setFormatter(formatter)
			self._logger.addHandler(file_handler)

	def overwrite_level(self, level: int) -> None:
		"""
		Overwrite the logging level of the logger.

		Parameters
		----------
		level : int
			The new logging level to set.
		"""
		self._logger.setLevel(level)
		
	@property
	def logger(self):
		"""
		Returns the logger instance.

		Returns
		-------
		logging.Logger
			The configured logger instance.
		"""
		return self._logger
	
	def debug(self, message: str):
		"""
		Log a message with severity 'DEBUG'.

		Parameters
		----------
		message : str
			The message to be logged.
		"""
		self._logger.debug(message)

	def info(self, message: str):
		"""
		Log a message with severity 'INFO'.

		Parameters
		----------
		message : str
			The message to be logged.
		"""
		self._logger.info(message)

	def warning(self, message: str):
		"""
		Log a message with severity 'WARNING'.

		Parameters
		----------
		message : str
			The message to be logged.
		"""
		self._logger.warning(message)

	def error(self, message: str):
		"""
		Log a message with severity 'ERROR'.

		Parameters
		----------
		message : str
			The message to be logged.
		"""
		self._logger.error(message)

	def critical(self, message: str):
		"""
		Log a message with severity 'CRITICAL'.

		Parameters
		----------
		message : str
			The message to be logged.
		"""
		self._logger.critical(message)

