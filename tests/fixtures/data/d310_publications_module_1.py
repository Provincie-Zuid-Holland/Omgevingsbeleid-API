from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.modules.module_spec import ModuleSpec
from tests.fixtures.internal.spec.modules.module_status_history_spec import ModuleStatusHistorySpec
from tests.fixtures.internal.spec.publications import (
    PublicationActSpec,
    PublicationEnvironmentSpec,
    PublicationSpec,
    PublicationTemplateSpec,
    PublicationVersionSpec,
)


def load(col: Collector) -> None:
    col.adds(
        [
            PublicationSpec(
                key="publication_module_1_visie",
                module_id=col.ref(ModuleSpec, "module_1"),
                document_type="omgevingsvisie",
                template_id=col.ref(PublicationTemplateSpec, "publication_template_visie_2"),
                environment_id=col.ref(PublicationEnvironmentSpec, "publication_environment_prod"),
                act_id=col.ref(PublicationActSpec, "publication_act_visie"),
            ),
            PublicationVersionSpec(
                key="publication_version_module_1_visie",
                publication_id=col.ref(PublicationSpec, "publication_module_1_visie"),
                module_status_id=col.ref(ModuleStatusHistorySpec, "module_1_status_ter_inzage"),
            ),
        ]
    )
