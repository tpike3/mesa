"""This method is for dynamically  creating meta-agents that represent groups of agents with interdependent characteristics.

The new meta-agent class is created dynamically using the provided name and
unique attributes and functions.

Currently restricted to one parent agent and one meta-agent per agent.
Goal is to assess usage and expand functionality.

Method has three paths of execution:
1. Add agents to existing meta-agent
2. Create new meta-agent instance of existing meta-agent class
3. Create new meta-agent class

See alliance formation model in basic examples for usage.

"""

from types import MethodType

from mesa.experimental.meta_agents.meta_agent import MetaAgent


def create_multi_levels(
    model,
    new_agent_class: str,
    agents,
    meta_attributes=dict(),  # noqa B006
    meta_functions=dict(),  # noqa B006
    retain_subagent_functions=False,
    retain_subagent_attributes=False,
):
    """Dynamically create a new meta-agent class and instantiate agents in that class.

    Parameters:
    model (Model): The model instance.
    new_agent_class (str): The name of the new meta-agent class.
    agents (Iterable[Agent]): The agents to be included in the meta-agent.
    meta_attributes (dict): Attributes to be added to the meta-agent.
    meta_functions (dict): Functions to be added to the meta-agent.
    retain_subagent_functions (bool): Whether to retain functions from sub-agents.
    retain_subagent_attributes (bool): Whether to retain attributes from sub-agents.

    Returns:
        - None if adding agent(s) to existing class
        - New class instance if created a new instance of a dynamically
        created agent type
        - New class instance if created a new dynamically created agent type
    """
    # Convert agents to set to ensure uniqueness
    agents = set(agents)

    def add_functions(meta_agent_instance, agents, meta_functions):
        """Add functions to the meta-agent instance.

        Parameters:
        meta_agent_instance (MetaAgent): The meta-agent instance.
        agents (Iterable[Agent]): The agents to derive functions from.
        meta_functions (dict): Functions to be added to the meta-agent.
        """
        if retain_subagent_functions:
            agent_classes = {type(agent) for agent in agents}
            for agent_class in agent_classes:
                for name in agent_class.__dict__:
                    if callable(getattr(agent_class, name)) and not name.startswith(
                        "__"
                    ):
                        original_method = getattr(agent_class, name)
                        meta_functions[name] = original_method

        for name, func in meta_functions.items():
            bound_method = MethodType(func, meta_agent_instance)
            setattr(meta_agent_instance, name, bound_method)

    def add_attributes(meta_agent_instance, agents, meta_attributes):
        """Add attributes to the meta-agent instance.

        Parameters:
        meta_agent_instance (MetaAgent): The meta-agent instance.
        agents (Iterable[Agent]): The agents to derive attributes from.
        meta_attributes (dict): Attributes to be added to the meta-agent.
        """
        if retain_subagent_attributes:
            for agent in agents:
                for name, value in agent.__dict__.items():
                    if not callable(value):
                        meta_attributes[name] = value

        for key, value in meta_attributes.items():
            setattr(meta_agent_instance, key, value)

    # Path 1 - Add agents to existing meta-agent
    subagents = [a for a in agents if hasattr(a, "meta_agent")]
    if len(subagents) > 0:
        if len(subagents) == 1:
            add_attributes(subagents[0].meta_agent, agents, meta_attributes)
            add_functions(subagents[0].meta_agent, agents, meta_functions)
            subagents[0].meta_agent.add_subagents(agents)

        else:
            subagent = model.random.choice(subagents)
            agents = set(agents) - set(subagents)
            add_attributes(subagent.meta_agent, agents, meta_attributes)
            add_functions(subagent.meta_agent, agents, meta_functions)
            subagent.meta_agent.add_subagents(agents)
            # TODO: Add way for user to specify how agents join meta-agent instead of random choice
    else:
        # Path 2 - Create a new instance of an existing meta-agent class
        agent_class = next(
            (
                agent_type
                for agent_type in model.agent_types
                if agent_type.__name__ == new_agent_class
            ),
            None,
        )

        if agent_class:
            meta_agent_instance = agent_class(model, agents)
            add_attributes(meta_agent_instance, agents, meta_attributes)
            add_functions(meta_agent_instance, agents, meta_functions)
            model.register_agent(meta_agent_instance)
            return meta_agent_instance
        else:
            # Path 3 - Create a new meta-agent class
            meta_agent_class = type(
                new_agent_class,
                (MetaAgent,),
                {
                    "unique_id": None,
                    "_subset": None,
                },
            )

            meta_agent_instance = meta_agent_class(model, agents)
            add_attributes(meta_agent_instance, agents, meta_attributes)
            add_functions(meta_agent_instance, agents, meta_functions)
            model.register_agent(meta_agent_instance)
            return meta_agent_instance