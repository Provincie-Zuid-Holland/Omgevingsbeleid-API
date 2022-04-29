# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.ambitie import Ambitie  # noqa
from app.models.belang import Belang  # noqa
from app.models.beleidskeuze import Beleidskeuze  # noqa
from app.models.beleidsmodule import Beleidsmodule  # noqa
from app.models.gebruiker import Gebruiker  # noqa
from app.models.maatregel import Maatregel  # noqa
