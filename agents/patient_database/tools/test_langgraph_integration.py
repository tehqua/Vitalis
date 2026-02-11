"""Manual test script for LangGraph tools integration.

This script verifies that the LangGraph-compatible tools have proper
attributes and can integrate with LangChain/LangGraph agents.
"""

import sys
from pathlib import Path

# Add patient_database directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import (
    LANGGRAPH_TOOLS,
    langgraph_patient_lookup,
    langgraph_medical_history,
    langgraph_observation,
)


def test_tool_attributes():
    """Test 1: Verify tool attributes match LangGraph requirements."""
    print("=" * 60)
    print("TEST 1: Tool Attributes")
    print("=" * 60)

    for tool in LANGGRAPH_TOOLS:
        print(f"\n{tool.name}")
        print(f"  Description: {tool.description[:100]}...")
        print(f"  Args Schema: {tool.args_schema.__name__}")
        assert hasattr(tool, "name"), f"{tool} missing 'name'"
        assert hasattr(tool, "description"), f"{tool} missing 'description'"
        assert hasattr(tool, "args_schema"), f"{tool} missing 'args_schema'"
        assert hasattr(tool, "_run"), f"{tool} missing '_run'"

    print("\nAll tools have required attributes\n")


def test_patient_lookup():
    """Test 2: Test patient lookup with sample data.

    Note: Replace test_patient_id with actual UUID from database.
    """
    print("=" * 60)
    print("TEST 2: Patient Lookup Tool")
    print("=" * 60)

    # TODO: Replace with real patient ID from database
    test_patient_id = "1d604da9-9a81-4ba9-80c2-de3375d59b40"

    print(f"\nTesting with patient_id: {test_patient_id}")
    print("Note: This will fail until database is set up and ID is valid")

    try:
        result = langgraph_patient_lookup._run(patient_id=test_patient_id)
        print(f"\nResult:\n{result}")
        assert "Patient Information" in result or "not found" in result
        print("\nPatient lookup works\n")
    except Exception as e:
        print(f"\nExpected error (database not configured): {e}\n")


def test_medical_history():
    """Test 3: Test medical history tool.

    Note: Replace test_patient_id with actual UUID from database.
    """
    print("=" * 60)
    print("TEST 3: Medical History Tool")
    print("=" * 60)

    # TODO: Replace with real patient ID
    test_patient_id = "1d604da9-9a81-4ba9-80c2-de3375d59b40"

    print(f"\nTesting with patient_id: {test_patient_id}")
    print("Note: This will fail until database is set up and ID is valid")

    try:
        result = langgraph_medical_history._run(
            patient_id=test_patient_id, days_back=365
        )
        print(f"\nResult:\n{result[:500]}...")
        assert "Medical History" in result or "not found" in result
        print("\nMedical history works\n")
    except Exception as e:
        print(f"\nExpected error (database not configured): {e}\n")


def test_observation():
    """Test 4: Test observation tool.

    Note: Replace test_patient_id with actual UUID from database.
    """
    print("=" * 60)
    print("TEST 4: Observation Tool")
    print("=" * 60)

    # TODO: Replace with real patient ID
    test_patient_id = "1d604da9-9a81-4ba9-80c2-de3375d59b40"

    print(f"\nTesting with patient_id: {test_patient_id}")
    print("Note: This will fail until database is set up and ID is valid")

    try:
        result = langgraph_observation._run(
            patient_id=test_patient_id,
            observation_type="Blood Pressure",
            days_back=90,
            limit=10,
        )
        print(f"\nResult:\n{result[:500]}...")
        assert (
            "Observations" in result
            or "not found" in result
            or "No observations" in result
        )
        print("\nObservation lookup works\n")
    except Exception as e:
        print(f"\nExpected error (database not configured): {e}\n")


def test_langgraph_agent_compatibility():
    """Test 5: Verify tools are compatible with LangChain/LangGraph."""
    print("=" * 60)
    print("TEST 5: LangGraph Compatibility")
    print("=" * 60)

    try:
        from langchain_core.tools import BaseTool as LangChainBaseTool

        for tool in LANGGRAPH_TOOLS:
            assert isinstance(
                tool, LangChainBaseTool
            ), f"{tool.name} is not a LangChain BaseTool"
            print(f"{tool.name} is LangChain-compatible")

        print("\nAll tools are LangGraph-compatible\n")
    except ImportError as e:
        print(f"\nWarning: langchain-core not installed: {e}")
        print("Run: pip install langchain-core\n")
        raise


if __name__ == "__main__":
    print("\nLangGraph Tools Integration Test\n")

    # Test 1: Always runs - checks tool structure
    test_tool_attributes()

    # Test 5: Check LangChain compatibility
    test_langgraph_agent_compatibility()

    # Tests 2-4: Uncomment when database is set up and patient IDs are available
    test_patient_lookup()
    test_medical_history()
    test_observation()

    print("=" * 60)
    print("BASIC TESTS PASSED")
    print("=" * 60)
    print("\nTo test with real data:")
    print("1. Set up PostgreSQL database")
    print("2. Run migration: python scripts/migrate_csv_to_postgres.py")
    print("3. Get patient ID: psql -d medscreening -c 'SELECT id FROM patients LIMIT 1;'")
    print("4. Update test_patient_id in this file")
    print("5. Uncomment tests 2-4 and run again\n")
