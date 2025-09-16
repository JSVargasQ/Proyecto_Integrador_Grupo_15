import json
import os
from datetime import datetime, timedelta

import functions_framework
import redis

from .schemas.schemas import ClientInfo, GenericResponse, Order, ProductOrder, RouteInfo

redis_host = os.environ.get("CACHE_HOST")
redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)


def _group_products_by_warehouse(products):
    warehouse_dict = {}
    for item in products:
        if item.warehouse_location not in warehouse_dict:
            warehouse_dict[item.warehouse_id] = []
        warehouse_dict[item.warehouse_id].append(item)
    return warehouse_dict


def _get_route_in_cache(order):
    warehouse_dict = _group_products_by_warehouse(order.order_items)
    cache_key = f"{':'.join([str(warehouse_id) for warehouse_id in warehouse_dict])}:{order.client.id}"
    cache_value = redis_client.get(cache_key)

    print(f"Cache key: {cache_key}")

    if not cache_value:
        return None

    return RouteInfo(**json.loads(cache_value))


@functions_framework.http
def get_delivery_date(request):
    """
    Función que simula la obtención del tiempo estimado de entrega.

    Args:
      `request` (flask.Request): Petición para obtener el tiempo estimado de entrega.
    Returns:
      `HTTP 200` Si se obtiene el tiempo estimado de entrega correctamente.
      `HTTP 202` Si la caché no tiene la ruta.
      `HTTP 405` Si la petición no es de tipo GET.
      `HTTP 500` Si ocurre un error durante la obtención del tiempo estimado de entrega.
    """
    try:
        if request.method != "GET":
            print(f"El método {request.method} no está permitido")
            return "Método no permitido", 405

        order_id = request.args.get("order_id")

        print("Obteniendo la información de la orden...")
        # Lógica para obtener la información de la orden de la base de datos
        # Simulación de datos
        order = Order(
            order_id=order_id,
            created_at=datetime.now(),
            order_items=[
                ProductOrder(
                    product_id="prod-001",
                    quantity=2,
                    warehouse_id="wh-001",
                    warehouse_location="Storage Minibodegas"
                ),
                ProductOrder(
                    product_id="prod-002",
                    quantity=1,
                    warehouse_id="wh-002",
                    warehouse_location="Keep & Go Calle 73"
                ),
                ProductOrder(
                    product_id="prod-003",
                    quantity=5,
                    warehouse_id="wh-002",
                    warehouse_location="Keep & Go Calle 73"
                )
            ],
            client=ClientInfo(
                id="client-123",
                name="Farmaceutica Test S.A.",
                location="Calle 100 #20-30, Bogotá, Colombia"
            )
        )

        print("Obteniendo información de la ruta en caché...")
        route = _get_route_in_cache(order)

        if not route:
            print(f"No se encontró la ruta en caché para el pedido {order_id}.")
            print(f"Timestamp - Cálculo del tiempo de entrega: {datetime.now()}")
            return GenericResponse(
                msg="La ruta no está disponible aún. Por favor, intente más tarde.").model_dump(), 202
        else:
            print(f"Ruta encontrada en caché para el pedido {order_id}: {route}")
            print(f"Timestamp - Cálculo del tiempo de entrega: {datetime.now()}")
            return GenericResponse(
                msg=f"La fecha estimada de su entrega es: {(order.created_at + timedelta(seconds=route.total_duration)).strftime('%Y-%m-%d %H:%M:%S')}.").model_dump(), 200
    except Exception as e:
        print(f"Error al calcular el tiempo estimado de entrega: {str(e)}")
        return {"msg": "Error interno del servidor"}, 500
