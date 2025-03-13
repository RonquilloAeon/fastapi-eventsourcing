from datetime import date


def test_create_tenant_mutation(client):
    """Test creating a tenant through the GraphQL API"""
    query = """
    mutation {
      createTenant(input: {
        identificationNumber: "111-22-3333",
        firstName: "Jane",
        lastName: "Smith",
        email: "jane.smith@example.com",
        phoneNumber: "555-987-6543",
        dob: "1985-05-15"
      }) {
        id
        identificationNumber
        firstName
        lastName
        email
        isApproved
      }
    }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    tenant_data = data["data"]["createTenant"]
    assert tenant_data["identificationNumber"] == "111-22-3333"
    assert tenant_data["firstName"] == "Jane"
    assert tenant_data["lastName"] == "Smith"
    assert tenant_data["email"] == "jane.smith@example.com"
    assert tenant_data["isApproved"] is False
    assert "id" in tenant_data


def test_duplicate_identification_tenant(client, sample_tenant, tenant_repository):
    """Test that creating a tenant with duplicate identification number fails"""
    query = f"""
    mutation {{
      createTenant(input: {{
        identificationNumber: "{sample_tenant.identification_number}",
        firstName: "Duplicate",
        lastName: "Person",
        email: "duplicate@example.com",
        phoneNumber: "555-111-2222",
        dob: "1990-06-15"
      }}) {{
        id
      }}
    }}
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    # Should have errors due to duplicate identification number
    assert "errors" in data


def test_approve_tenant_mutation(client, tenant_repository):
    """Test approving a tenant through the GraphQL API"""
    # Create an unapproved tenant
    tenant = tenant_repository._repository.create_originator(
        identification_number="444-55-6666",
        first_name="Pending",
        last_name="Approval",
        email="pending@example.com",
        phone_number="555-333-4444",
        dob=date(1995, 10, 10),
        is_approved=False,
    )
    tenant_repository.save(tenant)

    query = f"""
    mutation {{
      approveTenant(id: "{tenant.id}") {{
        id
        firstName
        lastName
        isApproved
      }}
    }}
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    tenant_data = data["data"]["approveTenant"]
    assert tenant_data["id"] == str(tenant.id)
    assert tenant_data["isApproved"] is True


def test_update_tenant_contact_mutation(client, sample_tenant):
    """Test updating a tenant's contact information through the GraphQL API"""
    new_email = "new.email@example.com"
    new_phone = "555-999-8888"

    query = f"""
    mutation {{
      updateTenantContact(
        id: "{sample_tenant.id}",
        email: "{new_email}",
        phoneNumber: "{new_phone}"
      ) {{
        id
        email
        phoneNumber
      }}
    }}
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    tenant_data = data["data"]["updateTenantContact"]
    assert tenant_data["id"] == str(sample_tenant.id)
    assert tenant_data["email"] == new_email
    assert tenant_data["phoneNumber"] == new_phone


def test_approved_tenants_query(client, tenant_repository):
    """Test retrieving approved tenants through the GraphQL API"""
    # Create tenants with different approval statuses
    approved = tenant_repository._repository.create_originator(
        identification_number="approved-123",
        first_name="Approved",
        last_name="Person",
        email="approved@example.com",
        phone_number="555-123-4567",
        dob=date(1980, 1, 1),
        is_approved=True,
    )

    unapproved = tenant_repository._repository.create_originator(
        identification_number="unapproved-123",
        first_name="Unapproved",
        last_name="Person",
        email="unapproved@example.com",
        phone_number="555-123-4567",
        dob=date(1980, 1, 1),
        is_approved=False,
    )

    for tenant in [approved, unapproved]:
        tenant_repository.save(tenant)

    # Query approved tenants
    query = """
    query {
      approvedTenants {
        firstName
        lastName
        isApproved
      }
    }
    """

    response = client.post("/graphql", json={"query": query})

    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data

    tenants_data = data["data"]["approvedTenants"]

    # All returned tenants should be approved
    for tenant in tenants_data:
        assert tenant["isApproved"] is True

    # Check that we can find our approved tenant in the results
    found_approved = False
    for tenant in tenants_data:
        if tenant["firstName"] == "Approved" and tenant["lastName"] == "Person":
            found_approved = True
            break

    assert found_approved is True
