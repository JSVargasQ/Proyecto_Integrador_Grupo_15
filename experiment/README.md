# Experimento de arquitectura

A continuación se describen los pasos para ejecutar y desplegar los componentes que hacen parte del experimento.

## Cola de mensajes de Cloud Tasks

Cola de mensajes para gestionar asíncronamente la generación de rutas de entrega.

### Despliegue

Para crear la cola de mensajes en Cloud Tasks, ejecute el siguiente comando:

```bash
  gcloud tasks queues create route-task-queue `
  --location=us-central1 `
  --max-attempts=2 `
  --min-backoff=5s
```

## Caché de Memorystore - Redis

Caché para almacenar temporalmente las rutas de entrega generadas.

### Despliegue

Para crear la instancia de Redis en Memorystore, ejecute el siguiente comando:

```bash
  gcloud redis instances create route-cache `
  --size=1 `
  --region=us-central1 `
  --tier=BASIC `
  --redis-version=redis_7_2
```

## Bucket en Cloud Storage

Bucket para almacenar los datos de los resultados para el análisis. Es necesario que exista un archivo vacío llamado `data.csv` en el bucket.

### Despliegue

Para crear la cola de mensajes en Cloud Tasks, ejecute el siguiente comando:

```bash
  gcloud storage buckets create gs://g15-experiment --location=us-central1
```

## Componente Generar ruta de entrega

Función que simula la generación de una ruta de entrega utilizando la API route optimization de google.

### Despliegue

Para desplegar la función en Google Cloud Functions, ejecute el siguiente comando en la carpeta `generar_ruta`:

```bash
    gcloud functions deploy create_route `
      --runtime python313 `
      --trigger-http `
      --entry-point create_route `
      --source . `
      --region us-central1 `
      --allow-unauthenticated `
      --set-env-vars PROJECT_ID={ID del proyecto de GCloud} `
      --set-env-vars API_KEY={API Key de Maps} `
      --set-env-vars CACHE_HOST={Ip de la instancia de Redis} `
      --set-env-vars BUCKET=g15-experiment
```

## Componente Calcular tiempo de entrega

Función que cálcula el tiempo de entrega tomando los datos de la ruta generada de la memoria caché.

### Despliegue

Para desplegar la función en Google Cloud Functions, ejecute el siguiente comando en la carpeta `calcular_tiempo_entrega`:

```bash
    gcloud functions deploy get_delivery_date `
      --runtime python313 `
      --trigger-http `
      --entry-point get_delivery_date `
      --source . `
      --region us-central1 `
      --allow-unauthenticated `
      --set-env-vars CACHE_HOST={Ip de la instancia de Redis} `
      --set-env-vars BUCKET=g15-experiment
```

## Componente Confirmar Pedido

Función que simula la confirmación de un pedido.

### Ejecución

Ejecute los siguientes comandos en la carpeta `confirmar_pedido` para probar la función localmente.

```bash
  pip install -r requirements.txt
  functions-framework --target=confirm_order --port=8080 --debug
```

### Uso

| Función     | `confirm_order`                        |
| ----------- | -------------------------------------- |
| Método      | POST                                   |
| Ruta        | `/confirm_order`                       |
| Parámetros  | N/A                                    |
| Encabezados | N/A                                    |

Cuerpo:

```json
{
    "order_id": "{{$guid}}"
}
```

### Despliegue

Para desplegar la función en Google Cloud Functions, ejecute el siguiente comando en la carpeta `confirmar_pedido`:

```bash
    gcloud functions deploy confirm_order `
      --runtime python313 `
      --trigger-http `
      --entry-point confirm_order `
      --source . `
      --region us-central1 `
      --allow-unauthenticated `
      --set-env-vars PROJECT_ID={ID del proyecto de GCloud} `
      --set-env-vars QUEUE_ID=route-task-queue `
      --set-env-vars CREATE_ROUTE_PATH={Path de la función Generar ruta de entrega} `
      --set-env-vars GET_DELIVERY_DATE_PATH={Path de la función Calcular tiempo de entrega} `
      --set-env-vars BUCKET=g15-experiment
```