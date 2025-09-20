import json
import uuid
import random
from precargar_rutas.schemas.schemas import RequestBody, OrderItem, ClientInfo

from google.cloud import tasks_v2

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

project_id = 'cloud-native-miso-450004'
queue_id = 'route-task-queue'
create_route_url = 'https://us-central1-cloud-native-miso-450004.cloudfunctions.net/create_route'
tasks_client = tasks_v2.CloudTasksClient()


def _generate_all_combinations():
    requests = []
    for wh_id, wh_loc in WAREHOUSE_LOCATIONS.items():
        for client_id, client_loc in CLIENT_LOCATIONS.items():
            for n_items in range(3, 11):
                order_items = []
                for i in range(n_items):
                    # Para cada item, se puede variar el almacén
                    item_wh_id = random.choice(list(WAREHOUSE_LOCATIONS.keys()))
                    item = OrderItem(
                        product_id=f"prod-{str(i + 1).zfill(3)}",
                        quantity=random.randint(1, 10),
                        warehouse_id=item_wh_id,
                        warehouse_location=WAREHOUSE_LOCATIONS[item_wh_id]
                    )
                    order_items.append(item)
                client = ClientInfo(
                    id=client_id,
                    name=f"Cliente {client_id}",
                    location=client_loc
                )
                request = RequestBody(
                    order_id=str(uuid.uuid4()),
                    order_items=order_items,
                    client=client
                )
                requests.append(request)
    return requests


def preload_routes():
    """
    Función que simula la precarga de rutas en caché.
    """

    # Logica para obtener el historial de pedido de los clientes
    # Por simplicidad, se generan combinaciones aleatorias de pedidos
    all_requests = _generate_all_combinations()

    print(f"Generando y precargando las rutas en caché...")

    for request in all_requests:
        # Se envía la petición a la función que genera la ruta y la guarda en caché
        parent = tasks_client.queue_path(project_id, 'us-central1', queue_id)
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f'{create_route_url}',
                "headers": {
                    "Content-type": "application/json"
                },
                "body": json.dumps(request.model_dump()).encode(),
            }
        }
        tasks_client.create_task(request={"parent": parent, "task": task})

if __name__ == '__main__':
    preload_routes()