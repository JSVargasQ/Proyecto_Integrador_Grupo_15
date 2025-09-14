import logging
import functions_framework

from .schemas.schemas import RequestBody, GenericResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.http
def confirm_order(request):
    """
    Función que simula la confirmación de un pedido.

    Args:
      `request` (flask.Request): Petición confirmación de un pedido.
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

        request_json = request.get_json(silent=True)

        try:
            data = RequestBody(**request_json)
        except Exception as e:
            logger.error("El cuerpo de la petición es inválido o faltan campos")
            return {"msg": f"Error de validación: {str(e)}"}, 400

        order_id = data.order_id
        logger.info(f"Confirmando el pedido {order_id}...")
        # Lógica para confirmar el pedido
        logger.info("Pedido confirmado.")

        # Simular la construcción de la ruta de entrega
        logger.info("Construcción de la ruta de entrega en proceso...")

        return GenericResponse(msg=f"El pedido {order_id} ha sido confirmado.").model_dump()
    except Exception as e:
        logger.error(f"Error al confirmar el pedido: {str(e)}")
        return {"msg": "Error interno del servidor"}, 500
