import os
from pathlib import Path
from typing import Union


class FileSizeChecker:
	"""
	Utility for checking file sizes.
	"""

	@staticmethod
	def get_size(path: Union[str, Path]) -> int:
		"""
		Return the size of the file at `path` in bytes.

		Args:
			path: Path to the file (str or Path).

		Raises:
			FileNotFoundError: if the path does not exist.
			ValueError: if the path isn’t a file.
		"""
		p = Path(path)
		if not p.exists():
			raise FileNotFoundError(f"No such file: {p}")
		if not p.is_file():
			raise ValueError(f"Not a file: {p}")
		size_bytes = p.stat().st_size
		size_mb = size_bytes / (1024 ** 2) 
		return size_mb

	@staticmethod
	def get_human_readable_size(path: Union[str, Path], decimals: int = 2) -> str:
		"""
		Return the file size at `path` as a human‑readable string
		(e.g. "3.14MB").

		Args:
			path: Path to the file.
			decimals: Number of decimal places for the output.

		Raises:
			Same as `get_size`.
		"""
		size = FileSizeChecker.get_size(path)
		for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
			if size < 1024 or unit == "PB":
				return f"{size:.{decimals}f}{unit}"
			size /= 1024

	@staticmethod
	def compare_size_to(path: Union[str, Path], threshold: int) -> str:
		"""
		Compare the file size to a threshold in bytes.

		Args:
			path:      Path to the file.
			threshold: Size in bytes to compare against.

		Returns:
			- True if file size >= threshold
			- False  if file size < threshold
		"""
		size = FileSizeChecker.get_size(path)
		
		if size >= threshold:
			return True
		if size < threshold:
			return False