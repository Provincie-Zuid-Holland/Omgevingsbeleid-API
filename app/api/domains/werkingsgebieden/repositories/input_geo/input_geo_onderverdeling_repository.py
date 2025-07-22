import hashlib
import uuid
from abc import ABCMeta, abstractmethod
from shapely import wkt

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingTable


class InputGeoOnderverdelingRepository(BaseRepository, metaclass=ABCMeta):
    @abstractmethod
    def _text_to_shape(self, key: str) -> str:
        pass

    @abstractmethod
    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        pass

    def store(
        self,
        session: Session,
        onderverdeling: InputGeoOnderverdelingTable,
        geometry_text: str,
    ):
        session.add(onderverdeling)
        session.flush()

        params = {
            "uuid": self._format_uuid(onderverdeling.UUID),
            "shape": geometry_text,
        }
        sql = f"""
            UPDATE
                areas
            SET
                Shape = {self._text_to_shape("shape")}
            WHERE
                UUID = :uuid
            """
        session.execute(text(sql), params)
        session.commit()

    def _calculate_geometry_hash(self, wkt_text: str) -> str:
        """
        Calculate SHA-256 hash of normalized WKT geometry text.
        
        Args:
            wkt_text: WKT format geometry string
            
        Returns:
            SHA-256 hash as hexadecimal string
        """
        try:
            # Parse and normalize the WKT to ensure consistent formatting
            geom = wkt.loads(wkt_text)
            # Use normalized WKT for consistent hashing
            normalized_wkt = geom.wkt
            
            # Calculate SHA-256 hash
            hash_obj = hashlib.sha256(normalized_wkt.encode('utf-8'))
            return hash_obj.hexdigest()
        except Exception as e:
            raise ValueError(f"Invalid WKT geometry: {e}")
