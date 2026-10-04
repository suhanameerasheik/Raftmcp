
import httpx

from ..config import CLUSTER_NODES


class TravelAgent:
    """Routes travel tool requests through the current Raft leader."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    async def _get_leader(self) -> tuple[str, str]:
        """Find the active leader by checking the cluster nodes."""

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for node_id, node_url in CLUSTER_NODES.items():
                try:
                    response = await client.get(
                        f"{node_url}/raft/status"
                    )
                    response.raise_for_status()
                    status = response.json()

                    if (
                        status.get("is_active")
                        and status.get("role") == "leader"
                    ):
                        return node_id, node_url

                except (httpx.HTTPError, ValueError):
                    continue

        raise RuntimeError(
            "No active Raft leader is currently available."
        )

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ) -> dict:
        """Verify registry availability and call a tool through the leader."""

        if tool_name not in {
            "search_flights",
            "check_flight_status",
            "search_hotels",
        }:
            raise ValueError(f"Unsupported travel tool: {tool_name}")

        leader_id, leader_url = await self._get_leader()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Confirm that the current leader has the requested tool.
            registry_response = await client.get(
                f"{leader_url}/registry/tools"
            )
            registry_response.raise_for_status()
            registry_data = registry_response.json()

            registered_names = {
                tool.get("name")
                for tool in registry_data.get("tools", [])
            }

            if tool_name not in registered_names:
                raise ValueError(
                    f"Tool '{tool_name}' is not registered "
                    f"on leader '{leader_id}'."
                )

            # Invoke the tool on the current leader.
            tool_response = await client.post(
                f"{leader_url}/tools/{tool_name}",
                json=arguments,
            )
            tool_response.raise_for_status()

            return {
                "success": True,
                "leader_id": leader_id,
                "tool": tool_name,
                "result": tool_response.json(),
            }