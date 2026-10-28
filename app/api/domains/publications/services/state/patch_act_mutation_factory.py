from app.api.domains.publications.services.assets.publication_asset_provider import PublicationAssetProvider
from app.api.domains.publications.services.state.patch_act_mutation import PatchActMutation
from app.api.domains.publications.services.state.versions import active_models


class PatchActMutationFactory:
    def __init__(self, asset_provider: PublicationAssetProvider):
        self._asset_provider: PublicationAssetProvider = asset_provider

    def create(self, active_act: active_models.ActiveAct) -> PatchActMutation:
        return PatchActMutation(
            self._asset_provider,
            active_act,
        )
