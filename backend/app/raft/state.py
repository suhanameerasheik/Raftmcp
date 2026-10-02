from dataclasses import dataclass, field
from enum import Enum


class NodeRole(str, Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class RaftState:
    node_id: str
    role: NodeRole = NodeRole.FOLLOWER
    current_term: int = 0
    voted_for: str | None = None
    leader_id: str | None = None
    votes_received: set[str] = field(default_factory=set)
