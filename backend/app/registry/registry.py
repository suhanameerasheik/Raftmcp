
from copy import deepcopy

from .commands import (
    ADD_TOOL,
    UPDATE_TOOL,
    DELETE_TOOL,
    BOOK_HOTEL,
    validate_command,
)
from .storage import RegistryStorage


class ToolRegistry:
    def __init__(self):
        self.storage = RegistryStorage()
        self._bookings: dict[str, dict] = {}

    def apply_committed_command(self, command: dict) -> None:
        validate_command(command)

        action = command["command"]

        if action == ADD_TOOL:
            self.storage.add_tool(command["tool"])

        elif action == UPDATE_TOOL:
            self.storage.update_tool(command["tool"])

        elif action == DELETE_TOOL:
            self.storage.delete_tool(command["name"])

        elif action == BOOK_HOTEL:
            booking = command["booking"]
            booking_id = booking["booking_id"]

            if booking_id not in self._bookings:
                self._bookings[booking_id] = deepcopy(booking)

    def list_tools(self) -> list[dict]:
        return self.storage.list_tools()

    def get_tool(self, name: str) -> dict | None:
        return self.storage.get_tool(name)

    def list_bookings(self) -> list[dict]:
        return [
            deepcopy(self._bookings[booking_id])
            for booking_id in sorted(self._bookings)
        ]