import uuid
from typing import List


class UUIDHandler:
	_uuids = set()
	
	def generate_uuid(self) -> str:
		new_uuid = str(uuid.uuid4())
		while new_uuid in self._uuids:
			new_uuid = str(uuid.uuid4())
		self._uuids.add(new_uuid)
		return new_uuid

	def check_uuid(self, uuid_to_check: str) -> bool:
		return uuid_to_check in self._uuids

	def get_all_uuids(self) -> List[str]:
		return list(self._uuids)

