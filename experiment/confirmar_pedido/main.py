import csv
import json
import os
import random
from datetime import datetime

import functions_framework
import requests
from google.cloud import tasks_v2, storage

from .schemas.schemas import RequestBody, GenericResponse

project_id = os.environ.get('PROJECT_ID')
queue_id = os.environ.get('QUEUE_ID')
bucket_name = os.environ.get('BUCKET')
create_route_url = os.getenv('CREATE_ROUTE_PATH')
get_delivery_date_url = os.getenv('GET_DELIVERY_DATE_PATH')

# Diccionario de ubicaciones de almacenes (warehouse_id: warehouse_location)
WAREHOUSE_LOCATIONS = {
    "wh-001": "Cra. 7 #32-16, Bogota, Colombia",
    "wh-002": "Av. Suba #123-45, Bogota, Colombia",
    "wh-003": "Calle 80 #20-30, Bogota, Colombia",
    "wh-004": "Cra. 15 #100-20, Bogota, Colombia",
    "wh-005": "Av. Caracas #45-67, Bogota, Colombia"
}

# Diccionario de ubicaciones de clientes (id: location)
CLIENT_LOCATIONS = {
    "client-101": "Calle 26 #85D-55, Bogota, Colombia",
    "client-102": "Cra. 50 #20-10, Bogota, Colombia",
    "client-103": "Av. Boyaca #45-12, Bogota, Colombia",
    "client-104": "Calle 53 #30-25, Bogota, Colombia",
    "client-105": "Cra. 24 #60-15, Bogota, Colombia"
}

tasks_client = tasks_v2.CloudTasksClient()
storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)


def generate_random_create_route_request(order_id):
    num_items = random.randint(3, 10)
    warehouse_ids = list(WAREHOUSE_LOCATIONS.keys())
    order_items = []
    for i in range(num_items):
        wid = random.choice(warehouse_ids)
        item = {
            "product_id": f"prod-{str(i + 1)}",
            "quantity": random.randint(1, 10),
            "warehouse_id": wid,
            "warehouse_location": WAREHOUSE_LOCATIONS[wid]
        }
        order_items.append(item)
    client_id = random.choice(list(CLIENT_LOCATIONS.keys()))
    client = {
        "id": client_id,
        "name": f"Cliente {client_id}",
        "location": CLIENT_LOCATIONS[client_id]
    }
    return {
        "order_id": order_id,
        "created_at": datetime.now().isoformat(),
        "order_items": order_items,
        "client": client
    }


def _save_in_storage(order_id, create_route_request):
    # Guardar el request en Cloud Storage
    try:
        blob = bucket.blob(f"{order_id}.txt")
        blob.upload_from_string(json.dumps(create_route_request, ensure_ascii=False, indent=2).encode("utf-8"),
                                content_type='text/plain')
    except Exception as e:
        print(f"Error al guardar en Cloud Storage: {str(e)}")


def _enqueue_create_route_task(order_id):
    create_route_request = generate_random_create_route_request(order_id)
    print(f"Ruta generada: {create_route_request}")
    parent = tasks_client.queue_path(project_id, 'us-central1', queue_id)
    _save_in_storage(order_id, create_route_request)
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
    tasks_client.create_task(request={"parent": parent, "task": task})


def _append_row_to_csv(new_row):
    try:
        blob = bucket.blob("data.csv")

        # Descarga el archivo CSV
        csv_data = blob.download_as_text(encoding="utf-8")
        rows = list(csv.reader(csv_data.splitlines()))

        # Añade la nueva fila
        rows.append([str(item) for item in new_row])

        # Guarda el archivo actualizado
        updated_csv = "\n".join([",".join(row) for row in rows])
        blob.upload_from_string(updated_csv, content_type="text/csv")
    except Exception as e:
        print(f"Error al actualizar el archivo CSV en Cloud Storage: {str(e)}")


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
        confirm_order_time = datetime.now()
        print(f"Timestamp - Pedido confirmado: {confirm_order_time}")

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
        get_delivery_date_time = datetime.now()
        print(f"Timestamp - Tiempo estimado de entrega obtenido: {get_delivery_date_time}")

        # Guardar en CSV
        _append_row_to_csv([order_id, confirm_order_time.isoformat(), get_delivery_date_time.isoformat(),
                            (get_delivery_date_time - confirm_order_time).total_seconds(), delivery_date_msg])

        return GenericResponse(msg=f"El pedido {order_id} ha sido confirmado. {delivery_date_msg}").model_dump()
    except Exception as e:
        print(f"Error al confirmar el pedido: {str(e)}")
        return {"msg": "Error interno del servidor"}, 500
