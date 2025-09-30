import os
import json

from pathlib import Path
from typing import Any, Dict

from ai.ocr import PyPDFParser
from ai.chunker import TextChunker
from ai.providers.openai import OpenAIClient
from ai.providers.openai.encoder import OpenAITextEmbedder
from infrastructure.vectordb.qdrant import (
    QdrantUpserter, 
    QdrantReader
)

from utils import Logger 

logger = Logger(__name__)


class UpsertToVDB:
    def __init__(self):
        self.ocr = PyPDFParser()
        self.chuncker = TextChunker()
        self.embedder = OpenAITextEmbedder()
        self.upserter = QdrantUpserter()
        self.reader = QdrantReader()
    
    def get_all_indexes(self) -> Dict[str, Any]:
        indexes = []
        for index in self.reader.iterate_all(batch_size=500):
            indexes.append(index)
        return indexes

    def process_json(
        self, 
        json_file: Path
    ):
        json_data = json.loads(json_file.read_text())
        page_content = json_data["page_content"]
        sintomas = [s.strip() for s in page_content["descricao_sintomas_consolidadas"].split(";") if s.strip()]
        testes = [t.strip() for t in page_content["descricao_testes_consolidados"].split(";") if t.strip()]
        causas = [c.strip() for c in page_content["causas_consolidadas"].split(";") if c.strip()]
        codigos = [c.strip() for c in page_content["codigo"].split(";") if c.strip()]
        descricoes = [d.strip() for d in page_content["descricao"].split(";") if d.strip()]
        
        max_len = max(len(sintomas), len(testes), len(causas), len(codigos), len(descricoes))
        entries = []

        for i in range(max_len):
            text = []
            if i < len(codigos):
                text.append(f"Código: {codigos[i]}")
            if i < len(descricoes):
                text.append(f"Descrição: {descricoes[i]}")
            if i < len(sintomas):
                text.append(f"Sintoma: {sintomas[i]}")
            if i < len(testes):
                text.append(f"Teste: {testes[i]}")
            if i < len(causas):
                text.append(f"Causa: {causas[i]}")
            entries.append("\n".join(text))
        
        return {
            'text': "\n".join(entries),
            'file': json_file.name
        }

    def parse_and_upsert(
        self, 
        file: str
    ) -> int:
        file = Path(file)
        if file.suffix == ".pdf":
            extract_struct = self.ocr.extract_text_from_pdf(
                pdf_path=file,
                out_txt_path=None
            )
        if file.suffix == ".json":
            extract_struct = self.process_json(
                json_file=file
            )

        text = extract_struct.get('text', None)
        file = extract_struct.get('file', None)
        total = 0

        if text:
            states = self.chuncker.chunk_from_pdf(
                text=text,
                base_meta={'file': file}
            )
            states_embed = self.embedder.embed_chunks(states=states)
            # logger.info(states_embed[0])
            total = self.upserter.upsert(
                states=states_embed,
                batch=4
            )

        return total
    
    def check(self) -> bool:
        data_root = os.getenv("DATA_ROOT", "/data")
        data_root = Path(data_root)

        files = [file for file in data_root.rglob("*") if file.is_file()]

        indexes = self.get_all_indexes()

        files_in_indexes = [Path(index['payload']['file']).name for index in indexes]
        total = 0
        num_files = len(files)
        for i, file in enumerate(files):
            file_name = file.name
            logger.info(f"[{i+1}/{num_files}] ({file_name})")
            if file_name in files_in_indexes:
                continue
            
            inserted_indexes = self.parse_and_upsert(file=file) 
            total += inserted_indexes
            logger.info(f"[{i+1}/{num_files}] ({file_name}) Inserted: {inserted_indexes} | Total: {total}")

