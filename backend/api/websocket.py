"""WebSocket 实时通信模块

管理与前端之间的 WebSocket 连接，
支持按任务 ID 分组广播，实现调研进度的实时推送。
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# 按任务 ID 分组的 WebSocket 连接池
_connections: dict[int, set[WebSocket]] = {}


async def connect(task_id: int, ws: WebSocket):
    """接受 WebSocket 连接并加入对应任务的连接池"""
    await ws.accept()
    _connections.setdefault(task_id, set()).add(ws)


def disconnect(task_id: int, ws: WebSocket):
    """从连接池中移除 WebSocket 连接，若该任务无连接则清理键"""
    conns = _connections.get(task_id)
    if conns:
        conns.discard(ws)
        if not conns:
            del _connections[task_id]


async def broadcast(task_id: int, message: dict):
    """向指定任务的所有 WebSocket 连接广播消息

    自动清理发送失败的连接（如客户端已断开）。
    """
    conns = _connections.get(task_id, set())
    dead = []
    for ws in conns:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)  # 记录发送失败的连接
    # 清理已断开的连接
    for ws in dead:
        conns.discard(ws)


@router.websocket("/api/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: int):
    """WebSocket 端点：前端通过此路径连接以接收任务进度更新

    保持连接直到客户端断开，期间可接收服务端推送的状态和日志消息。
    """
    await connect(task_id, websocket)
    try:
        while True:
            # 持续监听客户端消息（主要用于保活，服务端主要推送）
            await websocket.receive_text()
    except WebSocketDisconnect:
        disconnect(task_id, websocket)
