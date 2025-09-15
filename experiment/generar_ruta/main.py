import logging
import os
import random

import googlemaps
import functions_framework

from google.maps import routeoptimization_v1 as ro
from datetime import datetime, timedelta

from .schemas.schemas import RequestBody, GenericResponse, Location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

project_id = os.environ.get("PROJECT_ID")
api_key = os.environ.get("API_KEY")

gmaps = googlemaps.Client(key=api_key)
client = ro.RouteOptimizationClient()


def _geocode_address(address: str):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return Location(latitude=location['lat'], longitude=location['lng'])
    else:
        raise ValueError(f"Address {address} not found.")


def _calculate_route(order):
    global_start_time = datetime.now().replace(microsecond=0)
    global_end_time = (datetime.now() + timedelta(weeks=1)).replace(microsecond=0)

    logger.info("Geocodificando las direcciones...")
    delivery_location = _geocode_address(order.client_location)
    shipments = []
    for item in order.order_items:
        item_warehouse_location = _geocode_address(item.warehouse_location)
        shipments.append({
            "display_name": f"Envío para el producto {item.product_id}",
            "pickups": [
                {
                    "label": f"Recogida del producto {item.product_id}",
                    "arrival_location": item_warehouse_location.model_dump()
                }
            ],
            "deliveries": [
                {
                    "label": f"Entrega al cliente {order.client}",
                    "arrival_location": delivery_location.model_dump()
                }
            ]
        })

    logger.info("Calculando la ruta óptima...")
    request = ro.OptimizeToursRequest(
        parent="projects/" + project_id,
        model={
            "shipments": shipments,
            "vehicles": [
                {
                    "label": f"vehicle-{random.randint(1, 10)}",
                    "fixed_cost": 50,
                    "cost_per_kilometer": 0.08,
                    "cost_per_hour": 30,
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

        logger.info(f"Generando la ruta para el pedido {order_id}...")
        route_response = _calculate_route(body)
        logger.info(f"Ruta generada: {route_response}")

        return GenericResponse(msg=f"La ruta para el pedido {order_id} ha sido creada correctamente.").model_dump(), 201
    except Exception as e:
        logger.error(f"Error al generar la ruta: {str(e)}")
        return {"msg": "Error interno del servidor"}, 500
