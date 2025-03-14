from datetime import date, timedelta


def test_create_lease_mutation(client, unit, approved_tenant):
    """Test creating a lease through the GraphQL API"""
    start_date = date.today()
    end_date = start_date + timedelta(days=365)  # 1 year lease

    query = f"""
    mutation {{
      createLease(input: {{
        unitId: "{unit['id']}",
        tenantIds: ["{approved_tenant['id']}"],
        startDate: "{start_date.isoformat()}",
        endDate: "{end_date.isoformat()}"
      }}) {{
        id
        startDate
        endDate
        signedByTenant
        unit {{
          address
        }}
        tenants {{
          fullName
        }}
      }}
    }}
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    lease_data = data["data"]["createLease"]
    assert lease_data["startDate"] == start_date.isoformat()
    assert lease_data["endDate"] == end_date.isoformat()
    assert lease_data["signedByTenant"] is False
    assert lease_data["unit"]["address"] == unit["address"]
    assert len(lease_data["tenants"]) == 1
    assert approved_tenant["firstName"] in lease_data["tenants"][0]["fullName"]


def test_sign_lease_mutation(client, lease):
    """Test signing a lease through the GraphQL API"""
    query = f"""
    mutation {{
      signLease(id: "{lease['id']}") {{
        id
        signedByTenant
        signedAt
      }}
    }}
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    lease_data = data["data"]["signLease"]
    assert lease_data["id"] == lease["id"]
    assert lease_data["signedByTenant"] is True
    assert lease_data["signedAt"] is not None


def test_active_leases_query(client):
    """Test retrieving active leases through the GraphQL API"""
    # Create a unit via API
    create_unit_query = """
    mutation {
      createUnit(input: {
        address: "Active Lease Unit",
        amenities: []
      }) {
        id
        address
      }
    }
    """
    response = client.post("/graphql", json={"query": create_unit_query})
    assert response.status_code == 200
    unit_data = response.json()["data"]["createUnit"]
    unit_id = unit_data["id"]

    # Create a tenant via API
    create_tenant_query = """
    mutation {
      createTenant(input: {
        identificationNumber: "active-lease-tenant",
        firstName: "Active",
        lastName: "Tenant",
        email: "active@example.com",
        phoneNumber: "555-123-7890",
        dob: "1985-05-15"
      }) {
        id
      }
    }
    """
    response = client.post("/graphql", json={"query": create_tenant_query})
    assert response.status_code == 200
    tenant_data = response.json()["data"]["createTenant"]
    tenant_id = tenant_data["id"]

    # Approve the tenant
    approve_tenant_query = f"""
    mutation {{
      approveTenant(id: "{tenant_id}") {{
        id
        isApproved
      }}
    }}
    """
    response = client.post("/graphql", json={"query": approve_tenant_query})
    assert response.status_code == 200

    today = date.today()

    # Create an active lease (will be signed later)
    create_active_lease_query = f"""
    mutation {{
      createLease(input: {{
        unitId: "{unit_id}",
        tenantIds: ["{tenant_id}"],
        startDate: "{(today - timedelta(days=30)).isoformat()}",
        endDate: "{(today + timedelta(days=335)).isoformat()}"
      }}) {{
        id
      }}
    }}
    """
    response = client.post("/graphql", json={"query": create_active_lease_query})
    assert response.status_code == 200
    active_lease_id = response.json()["data"]["createLease"]["id"]

    # Sign the active lease
    sign_lease_query = f"""
    mutation {{
      signLease(id: "{active_lease_id}") {{
        id
        signedByTenant
      }}
    }}
    """
    response = client.post("/graphql", json={"query": sign_lease_query})
    assert response.status_code == 200

    # Create an inactive lease (won't be signed)
    create_inactive_lease_query = f"""
    mutation {{
      createLease(input: {{
        unitId: "{unit_id}",
        tenantIds: ["{tenant_id}"],
        startDate: "{(today + timedelta(days=30)).isoformat()}",
        endDate: "{(today + timedelta(days=395)).isoformat()}"
      }}) {{
        id
      }}
    }}
    """
    response = client.post("/graphql", json={"query": create_inactive_lease_query})
    assert response.status_code == 200

    # Create an expired lease and sign it
    create_expired_lease_query = f"""
    mutation {{
      createLease(input: {{
        unitId: "{unit_id}",
        tenantIds: ["{tenant_id}"],
        startDate: "{(today - timedelta(days=400)).isoformat()}",
        endDate: "{(today - timedelta(days=35)).isoformat()}"
      }}) {{
        id
      }}
    }}
    """
    response = client.post("/graphql", json={"query": create_expired_lease_query})
    assert response.status_code == 200
    expired_lease_id = response.json()["data"]["createLease"]["id"]

    # Sign the expired lease
    sign_expired_lease_query = f"""
    mutation {{
      signLease(id: "{expired_lease_id}") {{
        id
        signedByTenant
      }}
    }}
    """
    response = client.post("/graphql", json={"query": sign_expired_lease_query})
    assert response.status_code == 200

    # Query active leases
    query = """
    query {
      activeLeases {
        id
        startDate
        endDate
        signedByTenant
        isActive
        unit {
          address
        }
      }
    }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    leases_data = data["data"]["activeLeases"]

    # All returned leases should be active (signed & within date range)
    for lease in leases_data:
        assert lease["signedByTenant"] is True
        assert lease["isActive"] is True

    # There should be at least our active lease
    assert len(leases_data) >= 1

    # Find our specific lease and check its attributes
    found_active_lease = False
    for lease in leases_data:
        if lease["unit"]["address"] == "Active Lease Unit":
            found_active_lease = True
            break

    assert found_active_lease is True


def test_create_lease_validation(client):
    """Test that lease creation fails with unapproved tenants"""
    # Create a unit via API
    create_unit_query = """
    mutation {
      createUnit(input: {
        address: "Validation Test Unit",
        amenities: []
      }) {
        id
      }
    }
    """
    response = client.post("/graphql", json={"query": create_unit_query})
    assert response.status_code == 200
    unit_id = response.json()["data"]["createUnit"]["id"]

    # Create an unapproved tenant
    create_tenant_query = """
    mutation {
      createTenant(input: {
        identificationNumber: "unapproved-lease-tenant",
        firstName: "Unapproved",
        lastName: "TenantLease",
        email: "unapproved_lease@example.com",
        phoneNumber: "555-777-8888",
        dob: "1982-03-20"
      }) {
        id
      }
    }
    """
    response = client.post("/graphql", json={"query": create_tenant_query})
    assert response.status_code == 200
    tenant_id = response.json()["data"]["createTenant"]["id"]

    # Attempt to create a lease with the unapproved tenant
    start_date = date.today()
    end_date = start_date + timedelta(days=365)

    query = f"""
    mutation {{
      createLease(input: {{
        unitId: "{unit_id}",
        tenantIds: ["{tenant_id}"],
        startDate: "{start_date.isoformat()}",
        endDate: "{end_date.isoformat()}"
      }}) {{
        id
      }}
    }}
    """

    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    # Should have errors due to unapproved tenant
    assert "errors" in data
