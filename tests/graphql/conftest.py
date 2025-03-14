from datetime import date, timedelta

import pytest


@pytest.fixture
def tenant(client) -> dict:
    create_tenant = """
    mutation {
      createTenant(input: {
        identificationNumber: "123-45-6789",
        firstName: "Original",
        lastName: "Person",
        email: "original@example.com",
        phoneNumber: "555-123-4567",
        dob: "1980-01-01"
      }) {
        id
        identificationNumber
        firstName
      }
    }
    """
    response = client.post("/graphql", json={"query": create_tenant})
    assert response.status_code == 200
    return response.json()["data"]["createTenant"]


@pytest.fixture
def approved_tenant(client, tenant) -> dict:
    approve_query = f"""
    mutation {{
      approveTenant(id: "{tenant['id']}") {{
        id
        isApproved
      }}
    }}
    """
    response = client.post("/graphql", json={"query": approve_query})
    assert response.status_code == 200

    return tenant


@pytest.fixture
def unit(client) -> dict:
    create_query = """
    mutation {
      createUnit(input: {
        address: "Some Unit",
        amenities: []
      }) {
        id
        address
      }
    }
    """
    response = client.post("/graphql", json={"query": create_query})
    assert response.status_code == 200
    return response.json()["data"]["createUnit"]


@pytest.fixture
def lease(client, approved_tenant, unit) -> dict:
    today = date.today()

    create_active_lease_query = f"""
    mutation {{
      createLease(input: {{
        unitId: "{unit['id']}",
        tenantIds: ["{approved_tenant['id']}"],
        startDate: "{(today - timedelta(days=30)).isoformat()}",
        endDate: "{(today + timedelta(days=335)).isoformat()}"
      }}) {{
        id
      }}
    }}
    """
    response = client.post("/graphql", json={"query": create_active_lease_query})
    assert response.status_code == 200
    return response.json()["data"]["createLease"]
