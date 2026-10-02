import random
import time

from .state import NodeRole, RaftState


class ElectionManager:
    def __init__(self, state: RaftState):
        self.state = state
        self.timeout_min = 3.0
        self.timeout_max = 5.0
        self.last_heartbeat = time.monotonic()
        self.election_timeout = self._new_timeout()

    def _new_timeout(self) -> float:
        return random.uniform(self.timeout_min, self.timeout_max)

    def reset_timeout(self):
        self.last_heartbeat = time.monotonic()
        self.election_timeout = self._new_timeout()

    def timeout_expired(self) -> bool:
        return (
            self.state.role != NodeRole.LEADER
            and time.monotonic() - self.last_heartbeat >= self.election_timeout
        )

    def start_election(self):
        self.state.role = NodeRole.CANDIDATE
        self.state.current_term += 1
        self.state.voted_for = self.state.node_id
        self.state.leader_id = None
        self.state.votes_received = {self.state.node_id}
        self.reset_timeout()

    def record_vote(self, candidate_id: str, term: int) -> bool:
        if term < self.state.current_term:
            return False

        if term > self.state.current_term:
            self.state.current_term = term
            self.state.role = NodeRole.FOLLOWER
            self.state.voted_for = None
            self.state.leader_id = None
            self.state.votes_received.clear()

        if self.state.voted_for is None or self.state.voted_for == candidate_id:
            self.state.voted_for = candidate_id
            self.reset_timeout()
            return True

        return False

    def become_leader(self, cluster_size: int) -> bool:
        if (
            self.state.role == NodeRole.CANDIDATE
            and len(self.state.votes_received) > cluster_size // 2
        ):
            self.state.role = NodeRole.LEADER
            self.state.leader_id = self.state.node_id
            return True

        return False
