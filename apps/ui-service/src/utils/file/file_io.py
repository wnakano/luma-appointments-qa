from pathlib import Path
from typing import Union


class FileIO:
	"""
	Utility for reading and writing files.
	"""

	@staticmethod
	def read_text(path: Union[str, Path], encoding: str = "utf-8") -> str:
		"""
		Read a text file and return its contents as a string.

		Args:
			path: Path to the text file.
			encoding: File encoding (default "utf-8").

		Raises:
			FileNotFoundError: If the path does not exist.
			ValueError: If the path exists but is not a file.
		"""
		p = Path(path)
		if not p.exists():
			raise FileNotFoundError(f"No such file: {p}")
		if not p.is_file():
			raise ValueError(f"Not a file: {p}")
		return p.read_text(encoding=encoding)

	@staticmethod
	def write_text(
		path: Union[str, Path],
		content: str,
		encoding: str = "utf-8",
		overwrite: bool = True,
	) -> None:
		"""
		Write a string to a text file, creating parent directories if needed.

		Args:
			path: Path to the text file.
			content: The string to write.
			encoding: File encoding (default "utf-8").
			overwrite: If True, overwrite existing file; if False, error if file exists.
		"""
		p = Path(path)
		p.parent.mkdir(parents=True, exist_ok=True)
		mode = "w" if overwrite else "x"
		# open manually so we can control the mode
		with p.open(mode, encoding=encoding) as f:
			f.write(content)