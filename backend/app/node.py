from dataclasses import dataclass


@dataclass
class RaftNode:
    node_id: str

    def health(self) -> dict:
        return {
            "status": "healthy",
            "node_id": self.node_id,
        }