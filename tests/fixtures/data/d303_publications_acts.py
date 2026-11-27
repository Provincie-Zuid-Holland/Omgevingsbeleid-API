from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.publications import (
    PublicationActSpec,
    PublicationEnvironmentSpec,
)


def load(col: Collector) -> None:
    col.adds(
        [
            PublicationActSpec(
                key="publication_act_visie",
                environment_id=col.ref(PublicationEnvironmentSpec, "publication_environment_prod"),
                document_type="omgevingsvisie",
                title="Omgevingsvisie Zuid-Holland",
                work_other="omgevingsvisie-1",
            ),
            PublicationActSpec(
                key="publication_act_visie_inactive",
                environment_id=col.ref(PublicationEnvironmentSpec, "publication_environment_prod"),
                document_type="omgevingsvisie",
                title="Omgevingsvisie Zuid-Holland",
                is_active=False,
                work_other="omgevingsvisie-2",
            ),
            PublicationActSpec(
                key="publication_act_programma",
                environment_id=col.ref(PublicationEnvironmentSpec, "publication_environment_pre"),
                document_type="programma",
                title="Programma Zuid-Holland",
                work_other="programma-1",
            ),
        ]
    )
