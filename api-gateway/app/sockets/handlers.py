import jwt
import logging
from flask import request
from flask_socketio import emit, join_room, disconnect
from app.sockets import socketio
from config.settings import Config

logger = logging.getLogger(__name__)


@socketio.on('connect')
def on_connect():
    """
    El cliente envía el JWT en el query param ?token=<jwt>.
    Se valida y se une a la sala user_{id} para recibir alertas personalizadas.
    """
    token = request.args.get('token')
    if not token:
        logger.warning("Socket connection rejected: no token provided")
        disconnect()
        return

    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('sub') or payload.get('user_id')
        room = f"user_{user_id}"
        join_room(room)
        logger.info(f"Socket connected: user {user_id} joined room {room}")
        emit('connected', {'room': room, 'user_id': user_id})
    except jwt.ExpiredSignatureError:
        logger.warning("Socket connection rejected: expired token")
        disconnect()
    except jwt.InvalidTokenError as e:
        logger.warning(f"Socket connection rejected: invalid token — {e}")
        disconnect()


@socketio.on('disconnect')
def on_disconnect():
    logger.info("Socket client disconnected")
