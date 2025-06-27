from datetime import datetime, timezone
from typing import List, Optional, Set

import dso.models as dso_models

from app.api.domains.others.repositories.storage_file_repository import StorageFileRepository
from app.api.domains.publications.types.api_input_data import ActFrbr
from app.core.tables.others import StorageFileTable


class PublicationDocumentsProvider:
    def __init__(self, file_repostiory: StorageFileRepository):
        self._file_repostiory: StorageFileRepository = file_repostiory

    def get_documents(
        self,
        act_frbr: ActFrbr,
        all_objects: List[dict],
        used_objects: List[dict],
    ) -> List[dict]:
        used_documents_objects: List[dict] = self._calculate_used_documents(all_objects, used_objects)
        result: List[dict] = self._resolve_files(
            act_frbr,
            used_documents_objects,
        )

        # @todo: Look for better solution, maybe filename can be auto prefixed?
        filenames: List[str] = [r["Filename"] for r in result]
        if len(filenames) != len(set(filenames)):
            raise RuntimeError("Duplicate filenames just for different `documents`")

        return result

    def _resolve_files(
        self,
        act_frbr: ActFrbr,
        documents_objects: List[dict],
    ) -> List[dict]:
        result: List[dict] = []

        for document in documents_objects:
            code = document["Code"]
            file_uuid = document["File_UUID"]
            if file_uuid is None:
                raise RuntimeError(f"Missing file for document with code: {code}")

            storage_file: Optional[StorageFileTable] = self._file_repostiory.get_by_uuid(file_uuid)
            if storage_file is None:
                raise RuntimeError(f"File UUID does not exists for code: {code}")

            dso_document: dict = self._as_dso_document(act_frbr, document, storage_file)
            result.append(dso_document)

        return result

    def _as_dso_document(
        self,
        act_frbr: ActFrbr,
        document: dict,
        storage_file: StorageFileTable,
    ) -> dict:
        work_date: str = act_frbr.Work_Date
        work_identifier = f"file-{act_frbr.Act_ID}-{act_frbr.Expression_Version}-{document['Object_ID']}"

        # Some of these expression values are set as if this is the first version
        # But should be overwritten by the state system if they are already published under this UUID/Hash
        frbr = dso_models.GioFRBR(
            Work_Province_ID=act_frbr.Work_Province_ID,
            Work_Date=work_date,
            Work_Other=work_identifier,
            Expression_Language=act_frbr.Expression_Language,
            Expression_Date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            Expression_Version=1,
        )

        result = {
            "UUID": document["UUID"],
            "Code": document["Code"],
            "Frbr": frbr,
            "New": True,
            "Filename": document["Filename"],
            "Title": document["Title"],
            "Geboorteregeling": act_frbr.get_work(),
            "Content_Type": storage_file.Content_Type,
            "Binary": storage_file.Binary,
            # Used internally
            "Object_ID": document["Object_ID"],
            "Hash": storage_file.Checksum,
        }

        return result

    def _calculate_used_documents(self, all_objects: List[dict], used_objects: List[dict]) -> List[dict]:
        used_document_codes: Set[str] = set(
            [d for o in used_objects if isinstance(o.get("Documents"), list) for d in o.get("Documents", [])]
        )

        used_documents_objects: List[dict] = [
            o for o in all_objects if o["Object_Type"] == "document" and o.get("Code") in used_document_codes
        ]

        return used_documents_objects
