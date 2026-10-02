from dataclasses import dataclass, field

from .raft.state import RaftState, NodeRole


@dataclass
class RaftNode:
    node_id: str
    state: RaftState = field(init=False)

    def __post_init__(self):
        self.state = RaftState(node_id=self.node_id)

    def health(self) -> dict:
        return {
            "status": "healthy",
            "node_id": self.node_id,
        }

    def status(self) -> dict:
        return {
            "node_id": self.state.node_id,
            "role": self.state.role.value,
            "term": self.state.current_term,
            "voted_for": self.state.voted_for,
            "leader_id": self.state.leader_id,
        }

    def become_follower(
        self,
        term: int,
        leader_id: str | None = None,
    ):
        if term > self.state.current_term:
            self.state.current_term = term
            self.state.voted_for = None

        self.state.role = NodeRole.FOLLOWER
        self.state.leader_id = leader_id
        self.state.votes_received.clear()
