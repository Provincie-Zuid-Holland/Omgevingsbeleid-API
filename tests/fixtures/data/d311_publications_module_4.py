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
                key="publication_module_4_programma",
                module_id=col.ref(ModuleSpec, "module_4"),
                document_type="programma",
                template_id=col.ref(PublicationTemplateSpec, "publication_template_programma_2"),
                environment_id=col.ref(PublicationEnvironmentSpec, "publication_environment_pre"),
                act_id=col.ref(PublicationActSpec, "publication_act_programma"),
            ),
            PublicationVersionSpec(
                key="publication_version_module_4_programma",
                publication_id=col.ref(PublicationSpec, "publication_module_4_programma"),
                module_status_id=col.ref(ModuleStatusHistorySpec, "module_4_status_ontwerp_gs_concept"),
            ),
        ]
    )
