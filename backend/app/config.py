import os


NODE_ID = os.getenv("NODE_ID", "node-1")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8001"))