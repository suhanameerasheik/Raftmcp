import os

NODE_ID = os.getenv("NODE_ID", "node-1")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8001"))

CLUSTER_NODES = {
    "node-1": "http://127.0.0.1:8001",
    "node-2": "http://127.0.0.1:8002",
    "node-3": "http://127.0.0.1:8003",
}

PEERS = {
    node_id: url
    for node_id, url in CLUSTER_NODES.items()
    if node_id != NODE_ID
}