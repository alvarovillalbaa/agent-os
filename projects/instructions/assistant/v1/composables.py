# Assistant Agent Composables
# Composition logic and helper functions for the assistant instruction

from .values import (
    OPERATING_PRINCIPLES,
    AGENT_CAPABILITIES,
    HR_KNOWLEDGE,
    BASE_FORMATTING,
    CONVERSATIONAL_GUARDRAIL
)


def compose_full_instruction(
    system_blocks=None,
    agent_skills=None,
    agents_as_tools=None,
    handoffs=None,
    tool_calls=None,
    mcp_servers=None,
    dynamic_run_context=None,
    instructions_append=None
):
    """Compose the full assistant instruction with optional components."""

    # Start with core components
    components = [
        OPERATING_PRINCIPLES,
        AGENT_CAPABILITIES,
        HR_KNOWLEDGE,
        BASE_FORMATTING,
        CONVERSATIONAL_GUARDRAIL
    ]

    # Add optional components if provided
    if system_blocks:
        components.insert(0, system_blocks)

    if agent_skills:
        components.insert(3, agent_skills)

    if agents_as_tools:
        components.append(agents_as_tools)

    if handoffs:
        components.append(handoffs)

    if tool_calls:
        components.append(tool_calls)

    if mcp_servers:
        components.append(mcp_servers)

    if dynamic_run_context:
        components.append(dynamic_run_context)

    if instructions_append:
        components.append(instructions_append)

    return "\n\n".join(components)