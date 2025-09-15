import json
import logging
import os

import functions_framework
from google.cloud import tasks_v2

from .schemas.schemas import RequestBody, GenericResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = tasks_v2.CloudTasksClient()

project_id = os.environ.get('PROJECT_ID')
queue_id = os.environ.get('QUEUE_ID')
create_route_url = os.getenv('CREATE_ROUTE_PATH')


def _enqueue_create_route_task(order_id):
    # Request simulado para la creación de la ruta de entrega
    create_route_request = {
        "order_id": order_id,
        "order_items": [
            {
                "product_id": "prod-001",
                "quantity": 2,
                "warehouse_location": "Storage Minibodegas"
            },
            {
                "product_id": "prod-002",
                "quantity": 1,
                "warehouse_location": "Keep & Go Calle 73"
            }
        ],
        "client": "Farmaceutica Test S.A.",
        "client_location": "MiniBodegas - MB"
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
      `HTTP 405` Si la petición no es de tipo POST.
      `HTTP 400` Si campos de la petición faltan o son inválidos.
      `HTTP 200` Si se confirma el pedido correctamente.
      `HTTP 500` Si ocurre un error durante la confirmación del pedido.
    """
    try:
        if request.method != "POST":
            logger.error(f"El método {request.method} no está permitido")
            return "Método no permitido", 405

        try:
            body = RequestBody(**request.get_json(silent=True))
        except Exception as e:
            logger.error("El cuerpo de la petición es inválido o faltan campos")
            return {"msg": f"Error de validación: {str(e)}"}, 400

        order_id = body.order_id
        logger.info(f"Confirmando el pedido {order_id}...")
        # Lógica para confirmar el pedido
        logger.info("Pedido confirmado.")

        # Simular la construcción de la ruta de entrega
        logger.info("Construcción de la ruta de entrega en proceso...")
        _enqueue_create_route_task(order_id)

        return GenericResponse(msg=f"El pedido {order_id} ha sido confirmado.").model_dump()
    except Exception as e:
        logger.error(f"Error al confirmar el pedido: {str(e)}")
        return {"msg": "Error interno del servidor"}, 500
