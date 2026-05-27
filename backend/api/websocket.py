from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

_connections: dict[int, set[WebSocket]] = {}


async def connect(task_id: int, ws: WebSocket):
    await ws.accept()
    _connections.setdefault(task_id, set()).add(ws)


def disconnect(task_id: int, ws: WebSocket):
    conns = _connections.get(task_id)
    if conns:
        conns.discard(ws)
        if not conns:
            del _connections[task_id]


async def broadcast(task_id: int, message: dict):
    conns = _connections.get(task_id, set())
    dead = []
    for ws in conns:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        conns.discard(ws)


@router.websocket("/api/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: int):
    await connect(task_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        disconnect(task_id, websocket)
