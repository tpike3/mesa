"""Tests for the meta_agents module."""

import pytest

from mesa import Agent, Model
from mesa.experimental.meta_agents.meta_agent import (
    MetaAgent,
    evaluate_combination,
    find_combinations,
)
from mesa.experimental.meta_agents.multi_levels import multi_level_agents


class CustomAgent(Agent):
    """A custom agent with additional attributes and methods."""

    def __init__(self, model):
        """A custom agent constructor."""
        super().__init__(model)
        self.custom_attribute = "custom_value"

    def custom_method(self):
        """A custom agent method."""
        return "custom_method_value"


@pytest.fixture
def setup_agents():
    """Set up the model and agents for testing.

    Returns:
        tuple: A tuple containing the model and a list of agents.
    """
    model = Model()
    agent1 = Agent(model)
    agent2 = Agent(model)
    agent3 = Agent(model)
    agent4 = Agent(model)
    agent4.custom_attribute = "custom_value"
    agents = [agent1, agent2, agent3, agent4]
    return model, agents


def test_create_meta_agent_new_class(setup_agents):
    """Test creating a new meta-agent class and test inclusion of attributes and functions.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents
    meta_agent = create_meta_agent(
        model,
        "MetaAgentClass",
        agents,
        meta_attributes={"attribute1": "value1"},
        meta_functions={"function1": lambda self: "function1"},
        retain_subagent_attributes=True,
    )
    assert meta_agent is not None
    assert meta_agent.attribute1 == "value1"
    assert meta_agent.function1() == "function1"
    assert meta_agent.agents == set(agents)
    assert hasattr(meta_agent, "custom_attribute")
    assert meta_agent.custom_attribute == "custom_value"


def test_create_meta_agent_existing_class(setup_agents):
    """Test creating new meta-agent instance with an existing meta-agent class.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents

    # Create Met Agent Class
    meta_agent = create_meta_agent(
        model,
        "MetaAgentClass",
        [agents[0], agents[2]],
        meta_attributes={"attribute1": "value1"},
        meta_functions={"function1": lambda self: "function1"},
    )

    # Create new meta-agent instance with existing class
    meta_agent2 = create_meta_agent(
        model,
        "MetaAgentClass",
        [agents[1], agents[3]],
        meta_attributes={"attribute2": "value2"},
        meta_functions={"function2": lambda self: "function2"},
        retain_subagent_attributes=True,
    )
    assert meta_agent is not None
    assert meta_agent2.attribute2 == "value2"
    assert meta_agent.function1() == "function1"
    assert meta_agent.agents == {agents[2], agents[0]}
    assert meta_agent2.function2() == "function2"
    assert meta_agent2.agents == {agents[1], agents[3]}
    assert hasattr(meta_agent2, "custom_attribute")
    assert meta_agent2.custom_attribute == "custom_value"


def test_add_agents_to_existing_meta_agent(setup_agents):
    """Test adding agents to an existing meta-agent instance.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents

    meta_agent1 = create_meta_agent(
        model,
        "MetaAgentClass",
        [agents[0], agents[3]],
        meta_attributes={"attribute1": "value1"},
        meta_functions={"function1": lambda self: "function1"},
        retain_subagent_attributes=True,
    )

    create_meta_agent(
        model,
        "MetaAgentClass",
        [agents[1], agents[0], agents[2]],
        retain_subagent_attributes=True,
    )
    assert meta_agent1.agents == {agents[0], agents[1], agents[2], agents[3]}
    assert meta_agent1.function1() == "function1"
    assert meta_agent1.attribute1 == "value1"
    assert hasattr(meta_agent1, "custom_attribute")
    assert meta_agent1.custom_attribute == "custom_value"
    assert hasattr(meta_agent1, "custom_method")
    assert meta_agent1.custom_method() == "custom_method_value"


def test_meta_agent_integration(setup_agents):
    """Test the integration of MetaAgent with the model.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents

    meta_agent = multi_level_agents(
        model,
        "MetaAgentClass",
        agents,
        meta_attributes={"attribute1": "value1"},
        meta_methods={"function1": lambda self: "function1"},
        retain_subagent_attributes=True,
        retain_subagent_methods=True,
    )

    model.step()

    assert meta_agent in model.agents
    assert meta_agent.function1() == "function1"
    assert meta_agent.attribute1 == "value1"
    assert hasattr(meta_agent, "custom_attribute")
    assert meta_agent.custom_attribute == "custom_value"
    assert hasattr(meta_agent, "custom_method")
    assert meta_agent.custom_method() == "custom_method_value"


def test_evaluate_combination(setup_agents):
    """Test the evaluate_combination function.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents

    def evaluation_func(agent_set):
        return len(agent_set)

    result = evaluate_combination(tuple(agents), model, evaluation_func)
    assert result is not None
    assert result[1] == len(agents)


def test_find_combinations(setup_agents):
    """Test the find_combinations function.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents
    agent_set = set(agents)

    def evaluation_func(agent_set):
        return len(agent_set)

    def filter_func(combinations):
        return [combo for combo in combinations if combo[1] > 2]

    combinations = find_combinations(
        model,
        agent_set,
        size=(2, 4),
        evaluation_func=evaluation_func,
        filter_func=filter_func,
    )
    assert len(combinations) > 0
    for combo in combinations:
        assert combo[1] > 2


def test_meta_agent_len(setup_agents):
    """Test the __len__ method of MetaAgent.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents
    meta_agent = MetaAgent(model, set(agents))
    assert len(meta_agent) == len(agents)


def test_meta_agent_iter(setup_agents):
    """Test the __iter__ method of MetaAgent.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents
    meta_agent = MetaAgent(model, set(agents))
    assert list(iter(meta_agent)) == list(meta_agent._subset)


def test_meta_agent_contains(setup_agents):
    """Test the __contains__ method of MetaAgent.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents
    meta_agent = MetaAgent(model, set(agents))
    for agent in agents:
        assert agent in meta_agent


def test_meta_agent_add_subagents(setup_agents):
    """Test the add_subagents method of MetaAgent.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents
    meta_agent = MetaAgent(model, {agents[0], agents[1]})
    meta_agent.add_subagents({agents[2], agents[3]})
    assert meta_agent._subset == set(agents)


def test_meta_agent_remove_subagents(setup_agents):
    """Test the remove_subagents method of MetaAgent.

    Args:
        setup_agents (tuple): The model and agents fixture.
    """
    model, agents = setup_agents
    meta_agent = MetaAgent(model, set(agents))
    meta_agent.remove_subagents({agents[2], agents[3]})
    assert meta_agent._subset == {agents[0], agents[1]}
