from pydantic import BaseModel


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
