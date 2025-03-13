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
        is_leasable
        is_leased
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
    assert unit_data["is_leasable"] is True
    assert unit_data["is_leased"] is False
    assert "id" in unit_data


def test_get_units_query(client, unit_repository):
    """Test retrieving units through the GraphQL API"""
    # Create some units through the repository
    addresses = ["456 GraphQL First St, Test City", "789 GraphQL Second Ave, Test City"]

    for address in addresses:
        unit = unit_repository._repository.create_originator(
            address=address, amenities=[], is_leasable=True, is_leased=False
        )
        unit_repository.create(unit)

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


def test_update_unit_amenities_mutation(client, sample_unit):
    """Test updating a unit's amenities through the GraphQL API"""
    new_amenities = ["Updated Amenity 1", "Updated Amenity 2", "Updated Amenity 3"]

    query = f"""
    mutation {{
      updateUnitAmenities(
        id: "{sample_unit.id}",
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
    assert unit_data["id"] == str(sample_unit.id)
    assert unit_data["amenities"] == new_amenities


def test_mark_unit_as_leased_mutation(client, sample_unit):
    """Test marking a unit as leased through the GraphQL API"""
    query = f"""
    mutation {{
      markUnitAsLeased(id: "{sample_unit.id}") {{
        id
        address
        is_leased
      }}
    }}
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    unit_data = data["data"]["markUnitAsLeased"]
    assert unit_data["id"] == str(sample_unit.id)
    assert unit_data["is_leased"] is True


def test_available_units_query(client, unit_repository):
    """Test retrieving available units through the GraphQL API"""
    # Create units with different availability
    unit_repository._repository.create_originator(
        address="Available Unit", is_leasable=True, is_leased=False, amenities=[]
    )

    leased_unit = unit_repository._repository.create_originator(
        address="Leased Unit", is_leasable=True, is_leased=True, amenities=[]
    )

    unleasable_unit = unit_repository._repository.create_originator(
        address="Unleasable Unit", is_leasable=False, is_leased=False, amenities=[]
    )

    for unit in [leased_unit, unleasable_unit]:
        unit_repository.create(unit)

    # Query available units
    query = """
    query {
      availableUnits {
        address
        is_leasable
        is_leased
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
        assert unit["is_leasable"] is True
        assert unit["is_leased"] is False

    # None of the unavailable units should be included
    addresses = [unit["address"] for unit in units_data]
    assert "Leased Unit" not in addresses
    assert "Unleasable Unit" not in addresses
