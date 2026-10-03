
from copy import deepcopy


class RegistryStorage:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def add_tool(self, tool: dict) -> None:
        name = tool["name"]

        if name in self._tools:
            raise ValueError(f"Tool already exists: {name}")

        self._tools[name] = deepcopy(tool)

    def update_tool(self, tool: dict) -> None:
        name = tool["name"]

        if name not in self._tools:
            raise ValueError(f"Tool does not exist: {name}")

        self._tools[name] = deepcopy(tool)

    def delete_tool(self, name: str) -> None:
        if name not in self._tools:
            raise ValueError(f"Tool does not exist: {name}")

        del self._tools[name]

    def get_tool(self, name: str) -> dict | None:
        tool = self._tools.get(name)
        return deepcopy(tool) if tool is not None else None

    def list_tools(self) -> list[dict]:
        return [
            deepcopy(self._tools[name])
            for name in sorted(self._tools)
        ]