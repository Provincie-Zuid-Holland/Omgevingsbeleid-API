from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.publications import PublicationEnvironmentSpec


def load(col: Collector) -> None:
    col.adds(
        [
            PublicationEnvironmentSpec(
                key="publication_environment_prod",
                title="Productie",
                code="PROD",
                description="Productie omgeving",
            ),
            PublicationEnvironmentSpec(
                key="publication_environment_pre",
                title="Pre-productie",
                code="PRE",
                description="Pre-productie omgeving",
            ),
        ]
    )
