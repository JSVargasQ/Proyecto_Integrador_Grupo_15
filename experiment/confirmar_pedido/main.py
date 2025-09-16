import json
import os
from datetime import datetime

import functions_framework
import requests
from google.cloud import tasks_v2

from .schemas.schemas import RequestBody, GenericResponse

client = tasks_v2.CloudTasksClient()

project_id = os.environ.get('PROJECT_ID')
queue_id = os.environ.get('QUEUE_ID')
create_route_url = os.getenv('CREATE_ROUTE_PATH')
get_delivery_date_url = os.getenv('GET_DELIVERY_DATE_PATH')


def _enqueue_create_route_task(order_id):
    # Request simulado para la creación de la ruta de entrega
    create_route_request = {
        "order_id": order_id,
        "order_items": [
            {
                "product_id": "prod-001",
                "quantity": 2,
                "warehouse_id": "wh-001",
                "warehouse_location": "Storage Minibodegas"
            },
            {
                "product_id": "prod-002",
                "quantity": 1,
                "warehouse_id": "wh-002",
                "warehouse_location": "Keep & Go Calle 73"
            },
            {
                "product_id": "prod-003",
                "quantity": 5,
                "warehouse_id": "wh-002",
                "warehouse_location": "Keep & Go Calle 73"
            }
        ],
        "client": {
            "id": "client-123",
            "name": "Farmaceutica Test S.A.",
            "location": "Calle 100 #20-30, Bogotá, Colombia"
        }
    }

    parent = client.queue_path(project_id, 'us-central1', queue_id)
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f'{create_route_url}',
            "headers": {
                "Content-type": "application/json"
            },
            "body": json.dumps(create_route_request).encode(),
        }
    }
    client.create_task(request={"parent": parent, "task": task})


@functions_framework.http
def confirm_order(request):
    """
    Función que simula la confirmación de un pedido.

    Args:
      `request` (flask.Request): Petición para la confirmación de un pedido.
      - `oder_id` Id de la orden.
    Returns:
      `HTTP 200` Si se confirma el pedido correctamente.
      `HTTP 400` Si campos de la petición faltan o son inválidos.
      `HTTP 405` Si la petición no es de tipo POST.
      `HTTP 500` Si ocurre un error durante la confirmación del pedido.
    """
    try:
        if request.method != "POST":
            print(f"El método {request.method} no está permitido")
            return "Método no permitido", 405

        try:
            body = RequestBody(**request.get_json(silent=True))
        except Exception as e:
            print("El cuerpo de la petición es inválido o faltan campos")
            return GenericResponse(msg=f"Error de validación: {str(e)}").model_dump(), 400

        order_id = body.order_id
        print(f"Confirmando el pedido {order_id}...")
        # Lógica para confirmar el pedido
        print(f"Timestamp - Pedido confirmado: {datetime.now()}")

        # Construcción de la ruta de entrega
        print("Construcción de la ruta de entrega en proceso...")
        _enqueue_create_route_task(order_id)

        # Solicitud del tiempo estimado de entrega
        print("Cálculo del tiempo estimado de entrega en proceso...")
        response = requests.get(get_delivery_date_url, params={"order_id": order_id})
        status = response.status_code

        if status == 500:
            print("Error al obtener el tiempo estimado de entrega")

        delivery_date_msg = response.json()["msg"]
        print(f"Timestamp - Tiempo estimado de entrega obtenido: {datetime.now()}")

        return GenericResponse(msg=f"El pedido {order_id} ha sido confirmado. {delivery_date_msg}").model_dump()
    except Exception as e:
        print(f"Error al confirmar el pedido: {str(e)}")
        return {"msg": "Error interno del servidor"}, 500
