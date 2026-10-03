
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..registry.registry import ToolRegistry


class NodeRole(str, Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class LogEntry:
    index: int
    term: int
    command: dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "term": self.term,
            "command": self.command,
        }


@dataclass
class RaftState:
    node_id: str
    role: NodeRole = NodeRole.FOLLOWER
    current_term: int = 0
    voted_for: str | None = None
    leader_id: str | None = None
    votes_received: set[str] = field(default_factory=set)

    log: list[LogEntry] = field(default_factory=list)
    commit_index: int = 0
    last_applied: int = 0
    applied_commands: list[dict[str, Any]] = field(default_factory=list)
    registry: ToolRegistry = field(default_factory=ToolRegistry)

    # Day 7: simulated availability for failure and recovery demos.
    is_active: bool = True

    def append_entry(self, term: int, command: dict[str, Any]) -> LogEntry:
        entry = LogEntry(
            index=len(self.log) + 1,
            term=term,
            command=command,
        )
        self.log.append(entry)
        return entry

    def apply_committed_entries(self):
        while self.last_applied < self.commit_index:
            entry = self.log[self.last_applied]

            self.registry.apply_committed_command(entry.command)
            self.applied_commands.append(entry.command)
            self.last_applied += 1