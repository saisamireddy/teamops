from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

def broadcast_task_event(project_id: int, payload: dict):
    """
        Fire-and-forget realtime event.
        MUST be called only inside transaction.on_commit().
        """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("Channel layer unavailable")
            return

        async_to_sync(channel_layer.group_send)(
            f"project_{project_id}",
            payload,
        )
    except Exception as e:
        logger.exception("Realtime broadcast failed: %s", e)
