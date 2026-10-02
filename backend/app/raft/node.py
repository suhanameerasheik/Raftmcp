import asyncio

import httpx

from .election import ElectionManager
from .messages import RequestVoteRequest, RequestVoteResponse
from .state import NodeRole, RaftState


class RaftRuntime:
    def __init__(self, node_id: str, peers: dict | None = None):
        self.state = RaftState(node_id=node_id)
        self.election = ElectionManager(self.state)
        self.peers = peers or {}
        self.election_lock = asyncio.Lock()

    def status(self) -> dict:
        return {
            "node_id": self.state.node_id,
            "role": self.state.role.value,
            "term": self.state.current_term,
            "voted_for": self.state.voted_for,
            "leader_id": self.state.leader_id,
        }

    def start_election(self):
        self.election.start_election()

    def handle_request_vote(
        self, request: RequestVoteRequest
    ) -> RequestVoteResponse:
        if request.term < self.state.current_term:
            return RequestVoteResponse(
                term=self.state.current_term,
                vote_granted=False,
            )

        if request.term > self.state.current_term:
            self.state.current_term = request.term
            self.state.role = NodeRole.FOLLOWER
            self.state.voted_for = None
            self.state.leader_id = None
            self.state.votes_received.clear()

        can_vote = (
            self.state.voted_for is None
            or self.state.voted_for == request.candidate_id
        )

        if can_vote:
            self.state.voted_for = request.candidate_id
            self.election.reset_timeout()

        return RequestVoteResponse(
            term=self.state.current_term,
            vote_granted=can_vote,
        )

    async def request_peer_vote(
        self,
        client: httpx.AsyncClient,
        peer_id: str,
        peer_url: str,
        term: int,
    ) -> tuple[str, dict | None]:
        request = RequestVoteRequest(
            term=term,
            candidate_id=self.state.node_id,
        )

        try:
            response = await client.post(
                f"{peer_url}/raft/request-vote",
                json=request.model_dump(),
            )
            response.raise_for_status()
            return peer_id, response.json()
        except (httpx.HTTPError, ValueError):
            return peer_id, None

    async def run_election_round(self):
        async with self.election_lock:
            if self.state.role == NodeRole.LEADER:
                return

            self.start_election()
            election_term = self.state.current_term

            async with httpx.AsyncClient(timeout=1.0) as client:
                tasks = [
                    self.request_peer_vote(
                        client,
                        peer_id,
                        peer_url,
                        election_term,
                    )
                    for peer_id, peer_url in self.peers.items()
                ]
                results = await asyncio.gather(*tasks)

            if (
                self.state.role != NodeRole.CANDIDATE
                or self.state.current_term != election_term
            ):
                return

            for peer_id, result in results:
                if result is None:
                    continue

                peer_term = result.get("term", 0)

                if peer_term > self.state.current_term:
                    self.state.current_term = peer_term
                    self.state.role = NodeRole.FOLLOWER
                    self.state.voted_for = None
                    self.state.leader_id = None
                    self.state.votes_received.clear()
                    self.election.reset_timeout()
                    return

                if result.get("vote_granted", False):
                    self.state.votes_received.add(peer_id)

            if self.state.current_term == election_term:
                self.election.become_leader(
                    cluster_size=len(self.peers) + 1
                )

    async def run_election_loop(self):
        while True:
            if (
                self.state.role != NodeRole.LEADER
                and self.election.timeout_expired()
            ):
                await self.run_election_round()

            await asyncio.sleep(0.1)
