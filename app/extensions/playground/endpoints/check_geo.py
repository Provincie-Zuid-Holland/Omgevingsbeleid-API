import geopandas as gpd
import pandas as pd
from fastapi import APIRouter, Depends, Response
from shapely import wkt
from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Point, Polygon
from sqlalchemy import text
from sqlalchemy.orm import Session
from collections import Counter

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver


class CheckGeoEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            db: Session = Depends(depends_db),
        ) -> Response:
            query = f"""
            SELECT UUID, Werkingsgebied, SHAPE.STAsText() FROM
            Werkingsgebieden WHERE Created_Date >= '2024-02-06' AND Werkingsgebied = 'Windenergie'
            """
            # SHAPE.STAsText()
            result = db.execute(text(query)).all()
            uuids, titles, shapes = [], [], []
            print("\n\n")
            for row in result:
                uuid = row[0]
                title = row[1]
                geo = row[2]
                wkt_geo = wkt.loads(row[2])

                uuids.append(uuid)
                titles.append(title)
                shapes.append(wkt_geo)
            print("\n\n")

            df = pd.DataFrame({"UUID": uuids, "TITLE": titles, "SHAPE": shapes})
            gdf = gpd.GeoDataFrame(df, geometry="SHAPE")

            def get_duplicates(a):
                element_counts = Counter(a)
                duplicates = [element for element, count in element_counts.items() if count > 1]
                return duplicates

            def simplify_geometry(geom):
                tolerance = (
                    0.01  # Adjust the tolerance based on your data's coordinate system and accuracy requirements
                )
                return geom.simplify(tolerance, preserve_topology=True)

            def fix_invalid_geometry(geom):
                if not geom.is_valid:
                    return geom.buffer(0)
                return geom

            def remove_repeated_points(geom):
                if isinstance(geom, Polygon):
                    # Simplify Polygon by removing repeated points in exterior and interiors
                    exterior = geom.exterior.coords[:-1]  # Exclude last point because it's a repeat of the first
                    interiors = [ring.coords[:-1] for ring in geom.interiors]
                    return Polygon(exterior, interiors)

                elif isinstance(geom, LineString):
                    # Simplify LineString by removing repeated points
                    return LineString(list(set(geom.coords)))

                elif isinstance(geom, MultiPolygon):
                    # Apply the process to each Polygon in the MultiPolygon
                    simplified_polygons = [remove_repeated_points(polygon) for polygon in geom.geoms]
                    return MultiPolygon(simplified_polygons)

                return geom

            def check_coords_unique(geom):
                """Check if a geometry has unique coordinates."""
                if isinstance(geom, Point):
                    # Points always have unique coordinates
                    return True

                elif isinstance(geom, LineString):
                    # Check coordinates in a LineString
                    coords = list(geom.coords)
                    return len(coords) == len(set(coords))

                elif isinstance(geom, Polygon):
                    # Check coordinates in the exterior and interior rings of a Polygon
                    exterior_coords = list(geom.exterior.coords)
                    if len(exterior_coords) != len(set(exterior_coords)):
                        print(f"exterior error on these: {get_duplicates(exterior_coords)}")
                        return False
                    for interior in geom.interiors:
                        interior_coords = list(interior.coords)
                        if len(interior_coords) != len(set(interior_coords)):
                            print(f"interior error on these: {get_duplicates(interior_coords)}")
                            return False
                    return True

                elif isinstance(geom, GeometryCollection):
                    # Recursively check each geometry in a GeometryCollection
                    return all(check_coords_unique(part) for part in geom.geoms)

                return True  # Assume unique for other geometry types

            def check_geometry(geometry):
                errors = []

                # Check for validity
                if not geometry.is_valid:
                    errors.append("invalid_geometry")

                # Check for simplicity
                if not geometry.is_simple:
                    errors.append("not_simple")

                # Check for self-intersections
                if isinstance(geometry, (Polygon, MultiPolygon)):
                    simplified = geometry.buffer(0)
                    if not geometry.equals(simplified):
                        errors.append("self_intersection")

                # Check for repeated points
                if not check_coords_unique(geometry):
                    errors.append("repeated_points")

                # Summarize the results
                if errors:
                    return f"Error: {', '.join(errors)}"
                else:
                    return "OK"

            gdf["Check"] = gdf["SHAPE"].apply(check_geometry)
            gdf["Fixed_SHAPE"] = (
                gdf["SHAPE"].apply(fix_invalid_geometry).apply(simplify_geometry).apply(remove_repeated_points)
            )
            gdf["Check_After_Fix"] = gdf["Fixed_SHAPE"].apply(check_geometry)
            print(gdf[["UUID", "TITLE", "Check"]])

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            summary=f"Check GEO",
            description=None,
            tags=["Playground"],
        )

        return router


class CheckGeoEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "playground_check_geo"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return CheckGeoEndpoint(path)
