
from .commands import (
    ADD_TOOL,
    UPDATE_TOOL,
    DELETE_TOOL,
    validate_command,
)
from .storage import RegistryStorage


class ToolRegistry:
    def __init__(self):
        self.storage = RegistryStorage()

    def apply_committed_command(self, command: dict) -> None:
        validate_command(command)

        action = command["command"]

        if action == ADD_TOOL:
            self.storage.add_tool(command["tool"])

        elif action == UPDATE_TOOL:
            self.storage.update_tool(command["tool"])

        elif action == DELETE_TOOL:
            self.storage.delete_tool(command["name"])

    def list_tools(self) -> list[dict]:
        return self.storage.list_tools()

    def get_tool(self, name: str) -> dict | None:
        return self.storage.get_tool(name)