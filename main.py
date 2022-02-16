from flask.helpers import get_debug_flag
from dotenv import load_dotenv

from api.application import create_app
from api.settings import DevConfig, ProdConfig

load_dotenv()
CONFIG = DevConfig if get_debug_flag() else ProdConfig

app = create_app(CONFIG)
