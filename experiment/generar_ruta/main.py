import logging
import os
import random

import googlemaps
import functions_framework

from google.maps import routeoptimization_v1 as ro
from datetime import datetime, timedelta

from generar_ruta.schemas.schemas import RequestBody, GenericResponse, Location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

project_id = os.environ.get("PROJECT_ID", "cloud-native-miso-450004")
api_key = os.environ.get("API_KEY", "AIzaSyDozq4UkMH25P9lXu7bos8XIxobYen491Q")

gmaps = googlemaps.Client(key=api_key)
client = ro.RouteOptimizationClient()


def _geocode_address(address: str):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return Location(latitude=location['lat'], longitude=location['lng'])
    else:
        raise ValueError(f"Address {address} not found.")


def _calculate_route(start: Location, end: Location):
    global_start_time = datetime.now().replace(microsecond=0)
    global_end_time = (datetime.now() + timedelta(weeks=1)).replace(microsecond=0)
    request = ro.OptimizeToursRequest(
        parent="projects/" + project_id,
        model={
            "shipments": [
                {
                    "pickups": [
                        {
                            "arrival_location": start.model_dump()
                        }
                    ],
                    "deliveries": [
                        {
                            "arrival_location": end.model_dump()
                        }
                    ]
                }
            ],
            "vehicles": [
                {
                    "label": f"vehicle-{random.randint(1, 10)}"
                }
            ],
            "global_start_time": global_start_time,
            "global_end_time": global_end_time
        }
    )

    return client.optimize_tours(request=request)


@functions_framework.http
def create_route(request):
    """
    Función que simula la generación de la ruta de entrega.

    Args:
      `request` (flask.Request): Petición para generar la ruta de entrega.
      - `oder_id` Id de la orden.
    Returns:
      `HTTP 400` Si campos de la petición faltan o son inválidos.
      `HTTP 201` Si se genera la ruta correctamente.
      `HTTP 500` Si ocurre un error durante la generación de la ruta.
    """
    try:
        try:
            body = RequestBody(**request.get_json(silent=True))
        except Exception as e:
            logger.error("El cuerpo de la petición es inválido o faltan campos")
            return {"msg": f"Error de validación: {str(e)}"}, 400

        order_id = body.order_id

        logger.info("Geocodificando las direcciones...")
        order_start_location = _geocode_address(body.start_location)
        order_end_location = _geocode_address(body.end_location)

        logger.info(f"Generando la ruta para el pedido {order_id}...")
        route_response = _calculate_route(order_start_location, order_end_location)
        logger.info(f"Ruta generada: {route_response}")

        return GenericResponse(msg=f"La ruta para el pedido {order_id} ha sido creada correctamente.").model_dump(), 201
    except Exception as e:
        logger.error(f"Error al generar la ruta: {str(e)}")
        return {"msg": "Error interno del servidor"}, 500


import generar_ruta.main as main_module


class MockRequest:
    def get_json(self, silent=True):
        return {
            "order_id": "123e4567-e89b-12d3-a456-426614174000",
            "start_location": "Universidad Nacional de Colombia",
            "end_location": "Universidad de los andes"
        }


if __name__ == "__main__":
    mock_request = MockRequest()
    response, status = main_module.create_route(mock_request)
    print("Status:", status)
    print("Response:", response)
