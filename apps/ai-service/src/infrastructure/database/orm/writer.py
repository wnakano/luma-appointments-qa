from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.orm import Session

from .tables import DBTables
from .engine import DatabaseEngine
from .models.schemas import Base
from utils import Logger

logger = Logger(__name__)


class DatabaseWriter(DatabaseEngine):
    def __init__(self):
        super().__init__()

    # ---- helpers -------------------------------------------------------------

    def _serialize(self, val: Any) -> Any:
        if isinstance(val, UUID):
            return str(val)
        if isinstance(val, (datetime, date)):
            return val.isoformat()
        return val

    def _get_mapping(self, table_name: str):
        mapping = DBTables.TABLE_MAP.get(table_name)
        if not mapping:
            raise NoSuchTableError(f"Table '{table_name}' not found in TABLE_MAP")
        orm_cls, model_cls = mapping
        return orm_cls, model_cls

    def _filter_payload(self, payload: Dict[str, Any], model_cls) -> Dict[str, Any]:
        allowed = set(getattr(model_cls, "__annotations__", {}).keys())
        print(f"allowed = {allowed}")
        return {k: v for k, v in payload.items() if k in allowed}

    # ---- basic CRUD ----------------------------------------------------------

    def insert_one(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a single row and return the persisted record as a dict.
        """
        orm_cls, model_cls = self._get_mapping(table_name)
        row_data = self._filter_payload(data, model_cls)

        session: Session = self.get_session()
        try:
            obj = orm_cls(**row_data)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return {
                field: self._serialize(getattr(obj, field))
                for field in model_cls.__annotations__
            }
        except Exception as e:
            session.rollback()
            logger.error(f"insert_one failed: {e}")
            raise
        finally:
            session.close()

    def insert_many(
        self,
        table_name: str,
        rows: Iterable[Dict[str, Any]],
        *,
        return_count_only: bool = True,
        chunk_size: int = 1000,
    ) -> Any:
        """
        Bulk insert many rows. By default returns number of inserted rows.
        Set return_count_only=False to return the ORM objects (serialized).
        """
        orm_cls, model_cls = self._get_mapping(table_name)

        session: Session = self.get_session()
        try:
            objs = []
            count = 0
            batch: List[orm_cls] = []  # type: ignore[name-defined]
            for data in rows:
                batch.append(orm_cls(**data))
                print(f"batch = {batch[0].to_dict()}")
                if len(batch) >= chunk_size:
                    session.add_all(batch)
                    session.commit()
                    count += len(batch)
                    if not return_count_only:
                        for o in batch:
                            session.refresh(o)
                            objs.append(
                                {
                                    f: self._serialize(getattr(o, f))
                                    for f in model_cls.__annotations__
                                }
                            )
                    batch = []

            if batch:
                session.add_all(batch)
                session.commit()
                count += len(batch)
                if not return_count_only:
                    for o in batch:
                        session.refresh(o)
                        objs.append(
                            {
                                f: self._serialize(getattr(o, f))
                                for f in model_cls.__annotations__
                            }
                        )

            return count if return_count_only else objs
        except Exception as e:
            session.rollback()
            logger.error(f"insert_many failed: {e}")
            raise
        finally:
            session.close()

    def update_by_id(
        self,
        table_name: str,
        id_value: Any,
        data: Dict[str, Any],
        *,
        id_field: str = "id",
    ) -> Dict[str, Any]:
        """
        Update a row by primary key (default 'id') and return the updated record.
        """
        orm_cls, model_cls = self._get_mapping(table_name)
        payload = self._filter_payload(data, model_cls)

        session: Session = self.get_session()
        try:
            obj = session.query(orm_cls).filter(getattr(orm_cls, id_field) == id_value).one()
            for k, v in payload.items():
                setattr(obj, k, v)
            session.commit()
            session.refresh(obj)
            return {
                field: self._serialize(getattr(obj, field))
                for field in model_cls.__annotations__
            }
        except Exception as e:
            session.rollback()
            logger.error(f"update_by_id failed: {e}")
            raise
        finally:
            session.close()
