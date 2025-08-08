from app.api.domains.publications.services.state.versions.v1 import StateV1
from app.api.domains.publications.services.state.versions.v2 import StateV2, StateV2Upgrader
from app.api.domains.publications.services.state.versions.v3 import StateV3, StateV3Upgrader
from app.api.domains.publications.services.state.versions.v4 import StateV4, StateV4Upgrader
from app.api.domains.publications.services.state.versions.v5 import StateV5, StateV5Upgrader

ActiveState = StateV5
