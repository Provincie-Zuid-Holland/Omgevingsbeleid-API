import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationError,
    ValidatePublicationObject,
    ValidatePublicationRequest,
    ValidatePublicationRule,
)


class AttachmentInBillReferenceRule(ValidatePublicationRule):
    async def validate(self, db: AsyncSession, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        bill_compact: dict[str, Any] = request.input_data.publication_version.bill_compact or {}
        referenced_ids: set[int] = self._extract_ref_ids(bill_compact)

        attachment_ids: set[int] = set()
        attachment_title_map: dict[int, str] = {}

        for attachment in request.input_data.publication_data.bill_attachments:
            attachment_ids.add(attachment["id"])
            attachment_title_map[attachment["id"]] = attachment.get("title", attachment.get("filename", ""))

        unreferenced_attachments: set[int] = attachment_ids - referenced_ids
        for unreferenced_attachment_id in unreferenced_attachments:
            errors.append(
                ValidatePublicationError(
                    rule="attachment_in_bill_reference_rule",
                    object=ValidatePublicationObject(
                        object_id=unreferenced_attachment_id,
                        title=attachment_title_map.get(unreferenced_attachment_id, ""),
                    ),
                    messages=[f"Attachment with id '{unreferenced_attachment_id}' is not referenced in bill compact"],
                )
            )

        not_found_referenced_ids: set[int] = referenced_ids - attachment_ids

        for not_found_id in not_found_referenced_ids:
            errors.append(
                ValidatePublicationError(
                    rule="attachment_in_bill_reference_rule",
                    object=ValidatePublicationObject(
                        object_id=not_found_id,
                    ),
                    messages=[
                        f"Attachment with id '{not_found_id}' is referenced in bill compact but not found in attachments"
                    ],
                )
            )
        return errors

    def _extract_ref_ids(self, bill_compact: dict) -> set[int]:
        ref_ids: set[int] = set()
        pattern = re.compile(r"\[REF_BILL_PDF:(\d+)\]")

        for appendix in bill_compact.get("appendices", []):
            matches = pattern.findall(appendix.get("content", ""))
            for match in matches:
                ref_ids.add(int(match))

        motivation: dict | None = bill_compact.get("motivation")
        if motivation:
            for appendix in motivation.get("appendices", []):
                matches = pattern.findall(appendix.get("content", ""))
                for match in matches:
                    ref_ids.add(int(match))
        return ref_ids
