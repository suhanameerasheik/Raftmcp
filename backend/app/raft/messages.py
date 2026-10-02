from pydantic import BaseModel, Field


class RequestVoteRequest(BaseModel):
    term: int
    candidate_id: str


class RequestVoteResponse(BaseModel):
    term: int
    vote_granted: bool


class HeartbeatRequest(BaseModel):
    term: int
    leader_id: str


class HeartbeatResponse(BaseModel):
    term: int
    success: bool


class AppendEntriesRequest(BaseModel):
    term: int
    leader_id: str
    prev_log_index: int = 0
    prev_log_term: int = 0
    entries: list[dict] = Field(default_factory=list)
    leader_commit: int = 0


class AppendEntriesResponse(BaseModel):
    term: int
    success: bool
    match_index: int = 0
