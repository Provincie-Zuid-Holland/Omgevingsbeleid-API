import logging

from fastapi import APIRouter


router = APIRouter()
logger = logging.getLogger(__name__)


# @router.get(
#     "/graph",
#     response_model=schemas.GraphView,
# )
# def graph(
#     db: Session = Depends(deps.get_db),
#     current_gebruiker: models.Gebruiker = Depends(deps.get_current_active_gebruiker),
# ) -> Any:
#     """
#     Fetch graph representations on relationships of generic models
#     """
#     try:
#         graph_data = graph_service.calculate_relations()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Error building relational graph")

#     return graph_data
