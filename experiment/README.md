# Componente Confirmar Pedido

Función que simula la confirmación de un pedido.

## Ejecución

Ejecute los siguientes comandos en la raíz del proyecto para probar la función localmente.

```bash
  pip install -r requirements.txt
  functions-framework --target=confirm_order --port=8080
```

## Uso

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

## Despliegue

Para desplegar la función en Google Cloud Functions, ejecute el siguiente comando en la raíz del proyecto:

```bash
    gcloud functions deploy confirm_order `
      --runtime python313 `
      --trigger-http `
      --entry-point confirm_order `
      --source . `
      --region us-central1 `
      --allow-unauthenticated `
```
