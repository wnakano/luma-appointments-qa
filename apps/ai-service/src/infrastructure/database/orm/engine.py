import os
from typing import Union
from sqlalchemy import create_engine, engine
from sqlalchemy.orm import sessionmaker


class DatabaseEngine:
	""" Class to handle configuration and creation of a SQLAlchemy Engine for PostgreSQL. """
	_engine: Union[None, engine.Engine]  = None
	_SessionLocal: Union[None, sessionmaker] = None
	
	def __init__(self):

		
		url = os.getenv("DATABASE_URL")
		url = url.replace("postgres://", "postgresql://", 1)
		
		self._url = url

		if DatabaseEngine._engine is None:
			DatabaseEngine._engine  = create_engine(
				url=url, 
				echo=False
			)
			DatabaseEngine._Session = sessionmaker(
				bind=DatabaseEngine._engine,
				autoflush=False,
				autocommit=False
			)

		self._engine  = DatabaseEngine._engine
		self.SessionLocal = DatabaseEngine._Session

	@property
	def engine(self) -> engine.Engine:
		""" Returns the SQLAlchemy Engine instance. """
		return self._engine
	
	@property
	def url(self) -> str:
		""" Returns the database connection URL. """
		return self._url
	
	def get_session(self):
		""" Returns a new SQLAlchemy Session. """
		return self.SessionLocal()

