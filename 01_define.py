"""Step 1: define the drift agent and the sandbox it runs in.

TASK CARD (what the agent has to do)
  - Run Python files from a small library's docs, and read files.
  - Write two report files.
  - It needs nothing from the internet, and it must not install anything:
    the library uses only the Python standard library.

The defaults are permissive. The full toolset includes web search and web fetch,
and an environment created through the API gets unrestricted networking unless
you say otherwise. Give the agent only what the task card needs.

Run:  uv run 01_define.py      Check:  uv run check.py 1
Running it again updates the same agent (a new version) instead of creating another.
"""

from __future__ import annotations

import secrets
from typing import Any

import anthropic

import lab_state
from lab_common import MODEL, make_client, run_step

SYSTEM_PROMPT = (
    "You check whether a library's documentation still matches its code. "
    "You prove every finding by running code in the sandbox, never by reading alone, "
    "and you report exactly what you observed."
)


def choose_permissions() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Choose the agent's tools and the sandbox's network access.

    :returns: ``(tools, networking)``. ``tools`` is the agent's tool list (one
        ``agent_toolset_20260401`` entry, with ``default_config`` and per-tool
        ``configs``). ``networking`` is the environment's networking block.
    """
    # TODO: return (tools, networking).
    # TODO: tools is a list with one {"type": "agent_toolset_20260401", ...} entry. Decide which
    #       built-in tools the task card needs, and turn the rest off (see the README's links).
    # TODO: networking is the environment's networking block. Decide how much internet the
    #       sandbox should reach.
    raise NotImplementedError("YOUR TURN (step 1): choose the agent's tools and the sandbox's network access in choose_permissions().")


def define_agent(client: anthropic.Anthropic, tools: list[dict[str, Any]]) -> Any:
    """Create the agent, or update the saved one so it gets a new version.

    :param client: An API client.
    :param tools: The tool list from :func:`choose_permissions`.
    :returns: The agent.
    """
    agent_id = lab_state.load().get("agent_id")
    if agent_id:
        current = client.beta.agents.retrieve(agent_id)
        if current.archived_at is None:
            agent = client.beta.agents.update(agent_id, version=current.version, model=MODEL,
                                              system=SYSTEM_PROMPT, tools=tools)
            if agent.version == current.version:
                print(f"Agent {agent.id} unchanged (version {agent.version}): same configuration, so no new version")
            else:
                print(f"Updated agent {agent.id}: version {current.version} -> {agent.version}")
            return agent
        print("The saved agent is archived, so a new one will be created.")
    agent = client.beta.agents.create(name="drift-lab-agent", model=MODEL, system=SYSTEM_PROMPT, tools=tools)
    print(f"Created agent {agent.id} (version {agent.version}, model {MODEL})")
    return agent


def define_environment(client: anthropic.Anthropic, networking: dict[str, Any]) -> Any:
    """Create the environment, or update the saved one if its networking changed.

    :param client: An API client.
    :param networking: The networking block from :func:`choose_permissions`.
    :returns: The environment.
    """
    config = {"type": "cloud", "networking": networking}
    environment_id = lab_state.load().get("environment_id")
    if environment_id:
        current = client.beta.environments.retrieve(environment_id)
        if current.archived_at is None:
            saved = current.config.networking.to_dict()
            if any(saved.get(key) != value for key, value in networking.items()):
                current = client.beta.environments.update(environment_id, config=config)
                print(f"Updated environment {current.id} (applies to new sessions)")
            else:
                print(f"Reusing environment {current.id}")
            return current
    environment = client.beta.environments.create(name=f"drift-lab-{secrets.token_hex(4)}", config=config)
    print(f"Created environment {environment.id}")
    return environment


def main() -> None:
    """Define the agent and environment and save their IDs."""
    client = make_client()
    tools, networking = choose_permissions()
    agent = define_agent(client, tools)
    lab_state.update(agent_id=agent.id, agent_version=agent.version, model=MODEL)
    environment = define_environment(client, networking)
    lab_state.update(environment_id=environment.id)
    print("\nSaved both IDs to .lab-state.json. Next: uv run check.py 1")


if __name__ == "__main__":
    run_step(main)
