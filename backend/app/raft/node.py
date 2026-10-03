
import asyncio

import httpx

from .election import ElectionManager
from .messages import (
    AppendEntriesRequest,
    AppendEntriesResponse,
    RequestVoteRequest,
    RequestVoteResponse,
)
from .state import LogEntry, NodeRole, RaftState
from ..registry.commands import validate_command


class RaftRuntime:
    def __init__(self, node_id: str, peers: dict | None = None):
        self.state = RaftState(node_id=node_id)
        self.election = ElectionManager(self.state)
        self.peers = peers or {}
        self.election_lock = asyncio.Lock()
        self.write_lock = asyncio.Lock()

    def status(self) -> dict:
        return {
            "node_id": self.state.node_id,
            "role": self.state.role.value,
            "term": self.state.current_term,
            "voted_for": self.state.voted_for,
            "leader_id": self.state.leader_id,
            "is_active": self.state.is_active,
        }

    def log_status(self) -> dict:
        return {
            "node_id": self.state.node_id,
            "term": self.state.current_term,
            "entries": [entry.to_dict() for entry in self.state.log],
            "commit_index": self.state.commit_index,
            "last_applied": self.state.last_applied,
            "applied_commands": self.state.applied_commands,
        }

    def start_election(self):
        if not self.state.is_active:
            return
        self.election.start_election()

    def handle_request_vote(
        self, request: RequestVoteRequest
    ) -> RequestVoteResponse:
        if not self.state.is_active:
            return RequestVoteResponse(
                term=self.state.current_term,
                vote_granted=False,
            )

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

    def handle_append_entries(
        self, request: AppendEntriesRequest
    ) -> AppendEntriesResponse:
        if not self.state.is_active:
            return AppendEntriesResponse(
                term=self.state.current_term,
                success=False,
                match_index=len(self.state.log),
            )

        if request.term < self.state.current_term:
            return AppendEntriesResponse(
                term=self.state.current_term,
                success=False,
                match_index=len(self.state.log),
            )

        if request.term > self.state.current_term:
            self.state.current_term = request.term
            self.state.voted_for = None
            self.state.votes_received.clear()

        self.state.role = NodeRole.FOLLOWER
        self.state.leader_id = request.leader_id
        self.election.reset_timeout()

        if request.prev_log_index > len(self.state.log):
            return AppendEntriesResponse(
                term=self.state.current_term,
                success=False,
                match_index=len(self.state.log),
            )

        if request.prev_log_index > 0:
            previous_entry = self.state.log[request.prev_log_index - 1]

            if previous_entry.term != request.prev_log_term:
                return AppendEntriesResponse(
                    term=self.state.current_term,
                    success=False,
                    match_index=len(self.state.log),
                )

        for incoming in request.entries:
            entry = LogEntry(
                index=incoming["index"],
                term=incoming["term"],
                command=incoming["command"],
            )
            position = entry.index - 1

            if position < len(self.state.log):
                existing = self.state.log[position]

                if existing.term != entry.term:
                    if existing.index <= self.state.commit_index:
                        return AppendEntriesResponse(
                            term=self.state.current_term,
                            success=False,
                            match_index=len(self.state.log),
                        )

                    self.state.log = self.state.log[:position]
                    self.state.log.append(entry)

                elif existing.command != entry.command:
                    return AppendEntriesResponse(
                        term=self.state.current_term,
                        success=False,
                        match_index=len(self.state.log),
                    )

            elif position == len(self.state.log):
                self.state.log.append(entry)

            else:
                return AppendEntriesResponse(
                    term=self.state.current_term,
                    success=False,
                    match_index=len(self.state.log),
                )

        if request.leader_commit > self.state.commit_index:
            self.state.commit_index = min(
                request.leader_commit,
                len(self.state.log),
            )
            self.state.apply_committed_entries()

        return AppendEntriesResponse(
            term=self.state.current_term,
            success=True,
            match_index=len(self.state.log),
        )

    async def replicate_to_peer(
        self,
        client: httpx.AsyncClient,
        peer_id: str,
        peer_url: str,
        entry: LogEntry | None = None,
    ) -> tuple[str, dict | None]:
        if (
            not self.state.is_active
            or self.state.role != NodeRole.LEADER
        ):
            return peer_id, None

        next_index = (
            len(self.state.log)
            if entry is None
            else entry.index - 1
        )

        for _ in range(len(self.state.log) + 1):
            if (
                not self.state.is_active
                or self.state.role != NodeRole.LEADER
            ):
                return peer_id, None

            previous_index = next_index
            previous_term = (
                self.state.log[previous_index - 1].term
                if previous_index > 0
                else 0
            )

            missing_entries = [
                item.to_dict()
                for item in self.state.log[previous_index:]
            ]

            request = AppendEntriesRequest(
                term=self.state.current_term,
                leader_id=self.state.node_id,
                prev_log_index=previous_index,
                prev_log_term=previous_term,
                entries=missing_entries,
                leader_commit=self.state.commit_index,
            )

            try:
                response = await client.post(
                    f"{peer_url}/raft/append-entries",
                    json=request.model_dump(),
                )
                response.raise_for_status()
                result = response.json()

                if result.get("term", 0) > self.state.current_term:
                    return peer_id, result

                if result.get("success", False):
                    return peer_id, result

                follower_match = result.get("match_index", 0)
                next_index = min(
                    previous_index - 1,
                    follower_match,
                )
                next_index = max(0, next_index)

            except (httpx.HTTPError, ValueError):
                return peer_id, None

        return peer_id, None

    async def submit_command(self, command: dict) -> dict:
        validate_command(command)

        async with self.write_lock:
            if not self.state.is_active:
                raise RuntimeError("This node is inactive.")

            if self.state.role != NodeRole.LEADER:
                raise RuntimeError("This node is not the leader.")

            entry = self.state.append_entry(
                self.state.current_term,
                command,
            )
            entry_term = self.state.current_term

            async with httpx.AsyncClient(timeout=2.0) as client:
                tasks = [
                    self.replicate_to_peer(
                        client,
                        peer_id,
                        peer_url,
                        entry,
                    )
                    for peer_id, peer_url in self.peers.items()
                ]
                results = await asyncio.gather(*tasks)

            if (
                not self.state.is_active
                or self.state.role != NodeRole.LEADER
                or self.state.current_term != entry_term
            ):
                return {
                    "success": False,
                    "message": "Leadership changed during replication.",
                    "entry": entry.to_dict(),
                }

            acknowledgments = 1

            for _, result in results:
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

                    return {
                        "success": False,
                        "message": "A higher term was discovered.",
                        "entry": entry.to_dict(),
                    }

                if result.get("success", False):
                    acknowledgments += 1

            cluster_size = len(self.peers) + 1
            majority = cluster_size // 2 + 1

            if acknowledgments < majority:
                return {
                    "success": False,
                    "message": "Majority not reached. Entry remains uncommitted.",
                    "acknowledgments": acknowledgments,
                    "required": majority,
                    "entry": entry.to_dict(),
                }

            self.state.commit_index = entry.index
            self.state.apply_committed_entries()

            await self.broadcast_commit()

            return {
                "success": True,
                "message": "Entry committed and applied.",
                "acknowledgments": acknowledgments,
                "required": majority,
                "entry": entry.to_dict(),
                "commit_index": self.state.commit_index,
            }

    async def broadcast_commit(self):
        if not self.state.is_active:
            return

        async with httpx.AsyncClient(timeout=2.0) as client:
            tasks = [
                self.replicate_to_peer(
                    client,
                    peer_id,
                    peer_url,
                )
                for peer_id, peer_url in self.peers.items()
            ]
            await asyncio.gather(*tasks)

    async def request_peer_vote(
        self,
        client: httpx.AsyncClient,
        peer_id: str,
        peer_url: str,
        term: int,
    ) -> tuple[str, dict | None]:
        if not self.state.is_active:
            return peer_id, None

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
            if (
                not self.state.is_active
                or self.state.role == NodeRole.LEADER
            ):
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
                not self.state.is_active
                or self.state.role != NodeRole.CANDIDATE
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

            if (
                self.state.is_active
                and self.state.current_term == election_term
            ):
                self.election.become_leader(
                    cluster_size=len(self.peers) + 1
                )

    async def run_election_loop(self):
        while True:
            if (
                self.state.is_active
                and self.state.role != NodeRole.LEADER
                and self.election.timeout_expired()
            ):
                await self.run_election_round()

            await asyncio.sleep(0.1)