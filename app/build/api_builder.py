from sqlalchemy.orm import Session

from app.build.objects.types import BuildData
from app.build.services.config_parser import ConfigParser
from app.core.settings import Settings



class ApiBuilder:
    
    def __init__(
        self,
        settings: Settings,
        db: Session,
        config_parser: ConfigParser,
    ):
        self._settings: Settings = settings
        self._db: Session = db
        self._config_parser: ConfigParser = config_parser

    def build(self):
        build_data: BuildData = self._config_parser.parse(
            self._settings.MAIN_CONFIG_FILE,
            self._settings.OBJECT_CONFIG_PATH,
        )
        a = True
        pass
        
