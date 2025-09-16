import json
import os
import random
from datetime import datetime, timedelta

import functions_framework
import googlemaps
import redis
from google.maps import routeoptimization_v1 as ro

from .schemas.schemas import RequestBody, GenericResponse, Location, RouteOptimizationResponse

project_id = os.environ.get("PROJECT_ID")
api_key = os.environ.get("API_KEY")
redis_host = os.environ.get("CACHE_HOST")

gmaps = googlemaps.Client(key=api_key)
client = ro.RouteOptimizationClient()
redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)


def _group_products_by_warehouse(order_items):
    warehouse_dict = {}
    for item in order_items:
        if item.warehouse_location not in warehouse_dict:
            warehouse_dict[item.warehouse_id] = []
        warehouse_dict[item.warehouse_id].append(item)
    return warehouse_dict


def _geocode_address(address: str):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return Location(latitude=location['lat'], longitude=location['lng'])
    else:
        raise ValueError(f"Address {address} not found.")


def _calculate_route(order, warehouse_dict):
    global_start_time = datetime.now().replace(microsecond=0)
    global_end_time = (datetime.now() + timedelta(weeks=1)).replace(microsecond=0)

    print("Geocodificando las direcciones...")
    delivery_location = _geocode_address(order.client.location)

    shipments = []
    for warehouse_id, items in warehouse_dict.items():
        item_warehouse_location = _geocode_address(items[0].warehouse_location)
        shipments.append({
            "label": f"Envío para los productos: {', '.join([str(item.product_id) for item in items])}",
            "pickups": [
                {
                    "label": f"Recogida en {items[0].warehouse_location}",
                    "arrival_location": item_warehouse_location.model_dump()
                }
            ],
            "deliveries": [
                {
                    "label": f"Entrega al cliente {order.client.name}",
                    "arrival_location": delivery_location.model_dump()
                }
            ]
        })

    print("Calculando la ruta óptima...")
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


def _update_cache(warehouse_dict, client_id, route_response):
    aggregated_metrics = route_response.metrics.aggregated_route_metrics

    response_schema = RouteOptimizationResponse(
        performed_shipment_count=aggregated_metrics.performed_shipment_count,
        total_duration=aggregated_metrics.total_duration.seconds,
        travel_distance_meters=aggregated_metrics.travel_distance_meters,
        total_cost=route_response.metrics.total_cost
    )

    cache_key = f"{':'.join([str(warehouse_id) for warehouse_id in warehouse_dict])}:{client_id}"
    cache_value = json.dumps(response_schema.model_dump())

    print(f"Cache key: {cache_key}")

    redis_client.set(cache_key, cache_value, ex=300)  # Expira en 5 minutos


@functions_framework.http
def create_route(request):
    """
    Función que simula la generación de la ruta de entrega.

    Args:
      `request` (flask.Request): Petición para generar la ruta de entrega.
      - `oder_id` Id de la orden.
      - `order_items` Lista de items en el pedido.
        - `order_items.product_id` Id del producto.
        - `order_items.quantity` Cantidad del producto.
        - `order_items.warehouse_id` Id del almacén donde se encuentra el producto.
        - `order_items.warehouse_location` Dirección del almacén donde se encuentra el producto.
      - `client` Información del cliente.
        - `client.id` Id del cliente.
        - `client.name` Nombre del cliente.
        - `client.location` Dirección del cliente.
    Returns:
      `HTTP 201` Si se genera la ruta correctamente.
      `HTTP 400` Si campos de la petición faltan o son inválidos.
      `HTTP 500` Si ocurre un error durante la generación de la ruta.
    """
    try:
        try:
            body = RequestBody(**request.get_json(silent=True))
        except Exception as e:
            print("El cuerpo de la petición es inválido o faltan campos")
            return GenericResponse(msg=f"Error de validación: {str(e)}").model_dump(), 400

        order_id = body.order_id

        print("Agrupando productos por almacén...")
        warehouse_dict = _group_products_by_warehouse(body.order_items)

        print(f"Generando la ruta para el pedido {order_id}...")
        route_response = _calculate_route(body, warehouse_dict)
        print(f"Ruta generada: {route_response}")

        print("Guardando información de la ruta en caché...")
        _update_cache(warehouse_dict, body.client.id, route_response)
        print("Caché actualizada correctamente.")

        return GenericResponse(msg=f"La ruta para el pedido {order_id} ha sido creada correctamente.").model_dump(), 201
    except Exception as e:
        print(f"Error al generar la ruta: {str(e)}")
        return {"msg": "Error interno del servidor"}, 500
