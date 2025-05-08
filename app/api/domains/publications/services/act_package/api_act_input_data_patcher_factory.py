from app.api.domains.publications.services.act_package.api_act_input_data_patcher import ApiActInputDataPatcher
from app.api.domains.publications.services.state.patch_act_mutation_factory import PatchActMutationFactory
from app.api.domains.publications.services.state.versions import ActiveState


class ApiActInputDataPatcherFactory:
    def __init__(self, mutation_factory: PatchActMutationFactory):
        self._mutation_factory: PatchActMutationFactory = mutation_factory

    def create(self, state: ActiveState) -> ApiActInputDataPatcher:
        return ApiActInputDataPatcher(
            self._mutation_factory,
            state,
        )
