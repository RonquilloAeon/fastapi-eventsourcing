import json


def test_create_unit_mutation(client):
    """Test creating a unit through the GraphQL API"""
    query = """
    mutation {
      createUnit(input: {
        address: "123 GraphQL Test St, Apt 1, Test City, TC 12345",
        amenities: ["Parking", "Pool", "Gym"]
      }) {
        id
        address
        amenities
        isLeasable
        isLeased
      }
    }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    unit_data = data["data"]["createUnit"]
    assert unit_data["address"] == "123 GraphQL Test St, Apt 1, Test City, TC 12345"
    assert len(unit_data["amenities"]) == 3
    assert "Parking" in unit_data["amenities"]
    assert unit_data["isLeasable"] is True
    assert unit_data["isLeased"] is False
    assert "id" in unit_data


def test_create_unit_with_built_in_year(client):
    """Test creating a unit with built_in year through the GraphQL API"""
    query = """
    mutation {
      createUnit(input: {
        address: "123 Built In Test St",
        amenities: [],
        builtIn: 1985
      }) {
        id
        address
        builtIn
      }
    }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    unit_data = data["data"]["createUnit"]
    assert unit_data["builtIn"] == 1985


def test_get_units_query(client):
    """Test retrieving units through the GraphQL API"""
    # Create some units through the API
    addresses = ["456 GraphQL First St, Test City", "789 GraphQL Second Ave, Test City"]

    for address in addresses:
        query = f"""
        mutation {{
            createUnit(input: {{
                address: "{address}",
                amenities: []
            }}) {{
                id
                address
            }}
        }}
        """
        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        assert "errors" not in response.json()

    # Query the units through the API
    query = """
    query {
      units {
        id
        address
      }
    }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    # We should get at least the number of units we created
    units_data = data["data"]["units"]
    assert len(units_data) >= len(addresses)

    # Check that our addresses are in the results
    api_addresses = [unit["address"] for unit in units_data]
    for address in addresses:
        assert address in api_addresses


def test_update_unit_amenities_mutation(client):
    """Test updating a unit's amenities through the GraphQL API"""
    # Create a unit
    create_query = """
    mutation {
      createUnit(input: {
        address: "Some Unit",
        amenities: []
      }) {
        id
      }
    }
    """
    response = client.post("/graphql", json={"query": create_query})
    assert response.status_code == 200
    unit_id = response.json()["data"]["createUnit"]["id"]

    # Now update the unit
    new_amenities = ["Updated Amenity 1", "Updated Amenity 2", "Updated Amenity 3"]

    query = f"""
    mutation {{
      updateUnitAmenities(
        id: "{unit_id}",
        amenities: {json.dumps(new_amenities)}
      ) {{
        id
        address
        amenities
      }}
    }}
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    unit_data = data["data"]["updateUnitAmenities"]
    assert unit_data["id"] == unit_id
    assert unit_data["amenities"] == new_amenities


def test_update_unit_built_in_mutation(client):
    """Test updating a unit's built_in year through the GraphQL API"""
    # Create a unit
    create_query = """
    mutation {
      createUnit(input: {
        address: "123 Update Built In Test St",
        amenities: []
      }) {
        id
      }
    }
    """
    response = client.post("/graphql", json={"query": create_query})
    assert response.status_code == 200
    unit_id = response.json()["data"]["createUnit"]["id"]

    # Update the built_in year
    update_query = f"""
    mutation {{
      updateUnitBuiltIn(
        id: "{unit_id}",
        year: 1990
      ) {{
        id
        address
        builtIn
      }}
    }}
    """

    response = client.post("/graphql", json={"query": update_query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    unit_data = data["data"]["updateUnitBuiltIn"]
    assert unit_data["id"] == unit_id
    assert unit_data["builtIn"] == 1990


def test_update_unit_built_in_validation(client):
    """Test that updating unit built_in year validates the input"""
    # Create a unit
    create_query = """
    mutation {
      createUnit(input: {
        address: "123 Built In Validation Test St",
        amenities: []
      }) {
        id
      }
    }
    """
    response = client.post("/graphql", json={"query": create_query})
    assert response.status_code == 200
    unit_id = response.json()["data"]["createUnit"]["id"]

    # Try to update with an invalid year (too early)
    update_query = f"""
    mutation {{
      updateUnitBuiltIn(
        id: "{unit_id}",
        year: 1799
      ) {{
        id
      }}
    }}
    """

    response = client.post("/graphql", json={"query": update_query})
    data = response.json()
    assert "errors" in data


def test_mark_unit_as_leased_mutation(client):
    """Test marking a unit as leased through the GraphQL API"""
    # Create a unit that will be marked as leased
    create_leased_query = """
    mutation {
      createUnit(input: {
        address: "Some Unit",
        amenities: []
      }) {
        id
      }
    }
    """
    response = client.post("/graphql", json={"query": create_leased_query})
    assert response.status_code == 200
    leased_unit_id = response.json()["data"]["createUnit"]["id"]

    # Mark the unit as leased
    query = f"""
    mutation {{
      markUnitAsLeased(id: "{leased_unit_id}") {{
        id
        address
        isLeased
      }}
    }}
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    unit_data = data["data"]["markUnitAsLeased"]
    assert unit_data["id"] == leased_unit_id
    assert unit_data["isLeased"] is True


def test_available_units_query(client):
    """Test retrieving available units through the GraphQL API"""
    # Create an available unit
    create_available_query = """
    mutation {
      createUnit(input: {
        address: "Available Unit",
        amenities: []
      }) {
        id
      }
    }
    """
    response = client.post("/graphql", json={"query": create_available_query})
    assert response.status_code == 200

    # Create a unit that will be leased
    create_leased_query = """
    mutation {
      createUnit(input: {
        address: "Leased Unit",
        amenities: []
      }) {
        id
      }
    }
    """
    response = client.post("/graphql", json={"query": create_leased_query})
    assert response.status_code == 200
    leased_unit_id = response.json()["data"]["createUnit"]["id"]

    # Mark the unit as leased
    mark_leased_query = f"""
    mutation {{
      markUnitAsLeased(id: "{leased_unit_id}") {{
        id
      }}
    }}
    """
    response = client.post("/graphql", json={"query": mark_leased_query})
    assert response.status_code == 200

    # Create an unleasable unit and mark it as unleasable
    create_unleasable_query = """
    mutation {
      createUnit(input: {
        address: "Unleasable Unit",
        amenities: []
      }) {
        id
      }
    }
    """
    response = client.post("/graphql", json={"query": create_unleasable_query})
    assert response.status_code == 200

    # Note: We don't have a direct GraphQL mutation to mark a unit as unleasable in the schema.
    # In a real application, you would add this mutation. For now, we'll skip marking it unleasable
    # and just verify the available units don't include leased units.

    # Query available units
    query = """
    query {
      availableUnits {
        id
        address
        isLeasable
        isLeased
      }
    }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    units_data = data["data"]["availableUnits"]

    # Check that units with correct criteria are returned
    for unit in units_data:
        assert unit["isLeasable"] is True
        assert unit["isLeased"] is False

    # Check for our specific available unit
    found_available = False
    for unit in units_data:
        if unit["address"] == "Available Unit":
            found_available = True
            break
    assert found_available

    # Leased unit should not be in results
    addresses = [unit["address"] for unit in units_data]
    assert "Leased Unit" not in addresses
