"""Tests for membership storage."""

from mesa import Agent, Model
from mesa.meta_agents import MetaAgents
from mesa.meta_agents.backend import MembershipBackend


def test_add_and_query():
    """Add edges and verify basic query behavior."""
    backend = MembershipBackend()
    backend.add_membership("a1", "g1", "member")
    backend.add_membership("a2", "g1", "member")
    backend.add_membership("a1", "g2", "leader")

    assert backend.groups_of("a1") == {"g1", "g2"}
    assert backend.groups_of("a1", relation="member") == {"g1"}
    assert backend.agents_of("g1") == {"a1", "a2"}
    assert backend.relations_between("a1", "g1") == {"member"}
    backend.assert_invariants()


def test_multiple_relations_same_pair():
    """Allow multiple relation labels on the same agent-group pair."""
    backend = MembershipBackend()
    backend.add_membership("a1", "g1", "member")
    backend.add_membership("a1", "g1", "mentor")

    assert backend.relations_between("a1", "g1") == {"member", "mentor"}
    assert backend.groups_of("a1", relation="mentor") == {"g1"}
    backend.assert_invariants()


def test_idempotent_add_and_remove():
    """Repeated add/remove call should remain safe and deterministic."""
    backend = MembershipBackend()
    backend.add_membership("a1", "g1", "member")
    backend.add_membership("a1", "g1", "member")

    assert backend.as_triplets() == {("a1", "g1", "member")}

    backend.remove_membership("a1", "g1", "member")
    backend.remove_membership("a1", "g1", "member")
    assert backend.as_triplets() == set()
    backend.assert_invariants()


def test_replace_relation():
    """Replace an existing relation label for one edge."""
    backend = MembershipBackend()
    backend.add_membership("a1", "g1", "member")
    backend.replace_relation("a1", "g1", "member", "leader")

    assert backend.relations_between("a1", "g1") == {"leader"}
    assert backend.groups_of("a1", relation="member") == set()
    backend.assert_invariants()


def test_remove_agent_cascades_edges():
    """Removing an agent should clear all its incident edges."""
    backend = MembershipBackend()
    backend.bulk_add(
        [("a1", "g1", "member"), ("a1", "g2", "leader"), ("a2", "g1", "member")]
    )

    backend.remove_agent("a1")

    assert backend.groups_of("a1") == set()
    assert backend.agents_of("g1") == {"a2"}
    assert backend.agents_of("g2") == set()
    backend.assert_invariants()


def test_remove_group_cascades_edges():
    """Removing a group should clear all incident edges."""
    backend = MembershipBackend()
    backend.bulk_add(
        [("a1", "g1", "member"), ("a1", "g2", "leader"), ("a2", "g1", "member")]
    )

    backend.remove_group("g1")

    assert backend.agents_of("g1") == set()
    assert backend.groups_of("a1") == {"g2"}
    assert backend.groups_of("a2") == set()
    backend.assert_invariants()


def test_non_string_relation_key():
    """Allow non-string hashable relation keys."""
    backend = MembershipBackend()
    rel = ("role", 1)
    backend.add_membership("a1", "g1", rel)

    assert backend.relations_between("a1", "g1") == {rel}
    backend.assert_invariants()


def test_backend_uses_unique_ids_for_mesa_agents():
    """Membership bookkeeping should use unique_id values."""
    model = Model()
    meta_agents = MetaAgents(model)
    agent = Agent(model)
    group = meta_agents.create("Group", [agent])

    assert meta_agents.backend.as_triplets() == {
        (agent.unique_id, group.unique_id, "member")
    }
    assert meta_agents.backend.groups_of(agent) == {group.unique_id}
    assert meta_agents.backend.agents_of(group) == {agent.unique_id}
    meta_agents.backend.assert_invariants()


def test_triplets_for_entity_as_agent():
    """triplets_for returns edges where the entity is the agent (member)."""
    backend = MembershipBackend()
    backend.add_membership("a1", "g1", "member")
    backend.add_membership("a1", "g2", "leader")
    backend.add_membership("a2", "g1", "member")

    result = backend.triplets_for("a1")
    assert result == {("a1", "g1", "member"), ("a1", "g2", "leader")}


def test_triplets_for_entity_as_group():
    """triplets_for returns edges where the entity is the group."""
    backend = MembershipBackend()
    backend.add_membership("a1", "g1", "member")
    backend.add_membership("a2", "g1", "leader")

    result = backend.triplets_for("g1")
    assert result == {("a1", "g1", "member"), ("a2", "g1", "leader")}


def test_triplets_for_entity_as_both_agent_and_group():
    """triplets_for returns edges from both sides when entity is agent AND group."""
    backend = MembershipBackend()
    backend.add_membership("a1", "mid", "member")
    backend.add_membership("mid", "g1", "member")

    result = backend.triplets_for("mid")
    # mid is an agent of g1 and a group containing a1
    assert result == {("mid", "g1", "member"), ("a1", "mid", "member")}


def test_triplets_for_with_relation_filter():
    """triplets_for filters by relation when specified."""
    backend = MembershipBackend()
    backend.add_membership("a1", "g1", "member")
    backend.add_membership("a1", "g1", "leader")
    backend.add_membership("a2", "g1", "member")

    result = backend.triplets_for("a1", relation="leader")
    assert result == {("a1", "g1", "leader")}

    result_group = backend.triplets_for("g1", relation="member")
    assert result_group == {("a1", "g1", "member"), ("a2", "g1", "member")}


def test_triplets_for_unknown_entity():
    """triplets_for returns an empty set for an entity with no edges."""
    backend = MembershipBackend()
    backend.add_membership("a1", "g1", "member")

    assert backend.triplets_for("unknown") == set()


def test_all_entity_ids_populated():
    """all_entity_ids returns every agent and group id in the backend."""
    backend = MembershipBackend()
    backend.add_membership("a1", "g1", "member")
    backend.add_membership("a2", "g2", "leader")

    assert backend.all_entity_ids() == {"a1", "a2", "g1", "g2"}


def test_all_entity_ids_empty():
    """all_entity_ids returns an empty set when backend has no edges."""
    backend = MembershipBackend()
    assert backend.all_entity_ids() == set()


def test_all_entity_ids_after_removal():
    """all_entity_ids shrinks when agents/groups are removed."""
    backend = MembershipBackend()
    backend.add_membership("a1", "g1", "member")
    backend.add_membership("a2", "g1", "leader")

    backend.remove_agent("a1")
    ids = backend.all_entity_ids()
    assert "a1" not in ids
    assert "a2" in ids
    assert "g1" in ids

    backend.remove_group("g1")
    ids = backend.all_entity_ids()
    assert "g1" not in ids
    # a2 was only linked to g1, so after removing g1 its entry is also gone
    assert "a2" not in ids
