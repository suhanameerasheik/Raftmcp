
ADD_TOOL = "ADD_TOOL"
UPDATE_TOOL = "UPDATE_TOOL"
DELETE_TOOL = "DELETE_TOOL"

SUPPORTED_COMMANDS = {
    ADD_TOOL,
    UPDATE_TOOL,
    DELETE_TOOL,
}


def validate_command(command: dict) -> None:
    if not isinstance(command, dict):
        raise ValueError("Command must be a dictionary.")

    action = command.get("command")

    if action not in SUPPORTED_COMMANDS:
        raise ValueError("Unsupported registry command.")

    if action in {ADD_TOOL, UPDATE_TOOL}:
        tool = command.get("tool")

        if not isinstance(tool, dict) or not tool.get("name"):
            raise ValueError(
                f"{action} requires a tool object with a name."
            )

    if action == DELETE_TOOL:
        name = command.get("name")

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "DELETE_TOOL requires a non-empty tool name."
            )