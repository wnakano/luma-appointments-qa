from langgraph.checkpoint.postgres import PostgresSaver
from typing import Union, Optional
from sqlalchemy import text
import atexit

from infrastructure.database.orm import DatabaseEngine
from utils import Logger

logger = Logger(__name__)

class PostgresCheckpointer(DatabaseEngine):
    """
    PostgreSQL checkpointer that inherits from DatabaseEngine and follows
    the same singleton pattern to avoid multiple instantiations.
    """
    _checkpointer: Optional[PostgresSaver] = None
    _cm: Optional[object] = None

    def __init__(self):
        super().__init__()

        if PostgresCheckpointer._checkpointer is None:
            saver, cm = self._create_postgres_saver()
            PostgresCheckpointer._checkpointer = saver
            PostgresCheckpointer._cm = cm

            self._setup_database_tables()

            logger.info(
                f"PostgresCheckpointer singleton created with database: {self._mask_url(self.url)}"
            )

        self._checkpointer_instance = PostgresCheckpointer._checkpointer

    def _create_postgres_saver(self) -> tuple[PostgresSaver, Optional[object]]:
        """
        Create (and if necessary, enter) a PostgresSaver. Returns (saver, cm_or_none).
        """
        try:
            obj = PostgresSaver.from_conn_string(self.url)

            # Newer LangGraph may return a context manager here.
            # If it's a CM, enter it to get the actual PostgresSaver instance.
            if hasattr(obj, "__enter__") and hasattr(obj, "__exit__"):
                cm = obj
                saver = cm.__enter__()  # get the PostgresSaver
                logger.info("PostgresSaver context manager entered successfully")
                return saver, cm

            # Otherwise it's already a PostgresSaver instance
            logger.info("PostgresSaver instance created successfully")
            return obj, None

        except Exception as e:
            logger.error(f"Failed to create PostgresSaver: {e}")
            raise

    def _setup_database_tables(self):
        """
        Setup the required database tables for LangGraph checkpointing.
        This creates the 'checkpoints' table and any other required tables.
        """
        try:
            saver = PostgresCheckpointer._checkpointer
            if saver is None:
                raise ValueError("PostgresSaver not initialized")
            
            saver.setup()
            logger.info("Database tables for checkpointing created successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup database tables: {e}")
            raise

    def _safe_exit(self):
        """Called at process exit to close the context manager if used."""
        try:
            cm = PostgresCheckpointer._cm
            if cm is not None and hasattr(cm, "__exit__"):
                cm.__exit__(None, None, None)
                logger.info("PostgresSaver context manager exited cleanly")
        except Exception as e:
            logger.warning(f"Error while exiting PostgresSaver context: {e}")

    def _mask_url(self, url: str) -> str:
        if "@" in url:
            left, right = url.split("@", 1)
            if ":" in left:
                protocol_user = left.rsplit(":", 1)[0]
                return f"{protocol_user}:****@{right}"
        return url

    def get_checkpointer(self) -> PostgresSaver:
        return self._checkpointer_instance

    @classmethod
    def get_singleton_checkpointer(cls) -> Optional[PostgresSaver]:
        return cls._checkpointer

    def test_connection(self) -> bool:
        """
        Test both SQLAlchemy engine and LangGraph checkpointer connections.
        """
        try:
            # SQLAlchemy test
            with self.get_session() as session:
                session.execute(text("SELECT 1"))

            # LangGraph saver test (only if we actually have a saver)
            saver = self._checkpointer_instance
            if saver is None:
                logger.error("Checkpointer not initialized")
                return False

            test_config = {"configurable": {"thread_id": "test_connection"}}
            # `get_tuple` is a light read; if unsupported in your version, you can replace with `put`/`get`
            saver.get_tuple(test_config)

            logger.info("Database connections tested successfully")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def get_checkpointer_info(self) -> dict:
        return {
            "singleton_created": PostgresCheckpointer._checkpointer is not None,
            "instance_id": id(PostgresCheckpointer._checkpointer) if PostgresCheckpointer._checkpointer else None,
            "database_url": self._mask_url(self.url),
            "connection_healthy": self.test_connection(),
            "using_context_manager": PostgresCheckpointer._cm is not None,
        }

    @classmethod
    def reset_singleton(cls):
        # try to exit CM if present
        try:
            if cls._cm is not None and hasattr(cls._cm, "__exit__"):
                cls._cm.__exit__(None, None, None)
        except Exception:
            pass
        cls._checkpointer = None
        cls._cm = None
        logger.warning("PostgresCheckpointer singleton has been reset")
