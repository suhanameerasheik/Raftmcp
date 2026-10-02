import asyncio

import httpx

from .election import ElectionManager
from .messages import HeartbeatRequest, HeartbeatResponse
from .state import NodeRole, RaftState


class HeartbeatManager:
    def __init__(
        self,
        state: RaftState,
        election: ElectionManager,
        peers: dict | None = None,
    ):
        self.state = state
        self.election = election
        self.peers = peers or {}
        self.heartbeat_interval = 1.0

    def receive_heartbeat(
        self, request: HeartbeatRequest
    ) -> HeartbeatResponse:
        if request.term < self.state.current_term:
            return HeartbeatResponse(
                term=self.state.current_term,
                success=False,
            )

        if request.term > self.state.current_term:
            self.state.current_term = request.term
            self.state.voted_for = None

        self.state.role = NodeRole.FOLLOWER
        self.state.leader_id = request.leader_id
        self.state.votes_received.clear()
        self.election.reset_timeout()

        return HeartbeatResponse(
            term=self.state.current_term,
            success=True,
        )

    async def send_heartbeat(
        self,
        client: httpx.AsyncClient,
        peer_id: str,
        peer_url: str,
    ):
        if self.state.role != NodeRole.LEADER:
            return

        request = HeartbeatRequest(
            term=self.state.current_term,
            leader_id=self.state.node_id,
        )

        try:
            response = await client.post(
                f"{peer_url}/raft/heartbeat",
                json=request.model_dump(),
            )
            response.raise_for_status()
            result = response.json()

            if result.get("term", 0) > self.state.current_term:
                self.state.current_term = result["term"]
                self.state.role = NodeRole.FOLLOWER
                self.state.voted_for = None
                self.state.leader_id = None
                self.state.votes_received.clear()

        except (httpx.HTTPError, ValueError):
            pass

    async def run_heartbeat_loop(self):
        async with httpx.AsyncClient(timeout=1.0) as client:
            while True:
                if self.state.role == NodeRole.LEADER:
                    tasks = [
                        self.send_heartbeat(client, peer_id, peer_url)
                        for peer_id, peer_url in self.peers.items()
                    ]
                    await asyncio.gather(*tasks)

                await asyncio.sleep(self.heartbeat_interval)