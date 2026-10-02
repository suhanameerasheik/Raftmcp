
import asyncio

import httpx

from app.raft.node import RaftRuntime
from app.raft.state import NodeRole


def test_follower_replicates_and_applies_entry():
    follower = RaftRuntime("node-2")

    request = {
        "term": 1,
        "leader_id": "node-1",
        "prev_log_index": 0,
        "prev_log_term": 0,
        "entries": [
            {
                "index": 1,
                "term": 1,
                "command": {
                    "command": "ADD_TOOL",
                    "tool": {"name": "search_flights"},
                },
            }
        ],
        "leader_commit": 1,
    }

    from app.raft.messages import AppendEntriesRequest

    response = follower.handle_append_entries(
        AppendEntriesRequest(**request)
    )

    assert response.success is True
    assert len(follower.state.log) == 1
    assert follower.state.commit_index == 1
    assert follower.state.last_applied == 1


def test_leader_commits_with_majority_acknowledgments(monkeypatch):
    leader = RaftRuntime(
        "node-1",
        peers={
            "node-2": "http://node-2",
            "node-3": "http://node-3",
        },
    )
    leader.state.role = NodeRole.LEADER
    leader.state.current_term = 1

    async def fake_replicate_to_peer(
        client, peer_id, peer_url, entry=None
    ):
        if peer_id == "node-2":
            return peer_id, {"term": 1, "success": True}
        return peer_id, None

    async def fake_broadcast_commit():
        return None

    monkeypatch.setattr(
        leader,
        "replicate_to_peer",
        fake_replicate_to_peer,
    )
    monkeypatch.setattr(
        leader,
        "broadcast_commit",
        fake_broadcast_commit,
    )

    result = asyncio.run(
        leader.submit_command(
            {
                "command": "ADD_TOOL",
                "tool": {"name": "search_flights"},
            }
        )
    )

    assert result["success"] is True
    assert result["acknowledgments"] == 2
    assert result["required"] == 2
    assert result["commit_index"] == 1
    assert leader.state.last_applied == 1