# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.ambitie import Ambitie, Beleidskeuze_Ambities  # noqa
from app.models.belang import Belang, Beleidskeuze_Belangen  # noqa
from app.models.beleidsdoel import Beleidsdoel, Beleidskeuze_Beleidsdoelen  # noqa
from app.models.beleidskeuze import Beleidskeuze, Beleidsmodule_Beleidskeuzes  # noqa
from app.models.beleidsmodule import Beleidsmodule  # noqa
from app.models.beleidsprestatie import Beleidsprestatie, Beleidskeuze_Beleidsprestaties  # noqa
from app.models.beleidsregel import Beleidsregel, Beleidskeuze_Beleidsregels  # noqa
from app.models.beleidsrelatie import Beleidsrelatie  # noqa
from app.models.gebruiker import Gebruiker  # noqa
from app.models.maatregel import Maatregel, Beleidskeuze_Maatregelen, Beleidsmodule_Maatregelen  # noqa
from app.models.onderverdeling import Onderverdeling  # noqa
from app.models.thema import Thema, Beleidskeuze_Themas  # noqa
from app.models.verordening import Verordening, Beleidskeuze_Verordeningen  # noqa
from app.models.verordeningstructuur import Verordeningstructuur  # noqa
from app.models.werkingsgebied import Werkingsgebied, Beleidskeuze_Werkingsgebieden  # noqa
