from app.api.domains.publications.services.state.versions.v1 import StateV1
from app.api.domains.publications.services.state.versions.v2 import StateV2, StateV2Upgrader
from app.api.domains.publications.services.state.versions.v3 import StateV3, StateV3Upgrader
from app.api.domains.publications.services.state.versions.v4 import StateV4, StateV4Upgrader
from app.api.domains.publications.services.state.versions.v5 import StateV5, StateV5Upgrader
from app.api.domains.publications.services.state.versions.v6 import StateV6, StateV6Upgrader
from app.api.domains.publications.services.state.versions.v7 import StateV7, StateV7Upgrader
from app.api.domains.publications.services.state.versions.v8 import StateV8, StateV8Upgrader
from app.api.domains.publications.services.state.versions.v8 import actions as active_actions
from app.api.domains.publications.services.state.versions.v8 import models as active_models

ActiveState = StateV8
