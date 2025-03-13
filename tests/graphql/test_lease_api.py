from datetime import date, timedelta


def test_create_lease_mutation(client, sample_unit, sample_tenant):
    """Test creating a lease through the GraphQL API"""
    start_date = date.today()
    end_date = start_date + timedelta(days=365)  # 1 year lease

    query = f"""
    mutation {{
      createLease(input: {{
        unitId: "{sample_unit.id}",
        tenantIds: ["{sample_tenant.id}"],
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
    assert lease_data["unit"]["address"] == sample_unit.address
    assert len(lease_data["tenants"]) == 1
    assert sample_tenant.first_name in lease_data["tenants"][0]["fullName"]


def test_sign_lease_mutation(client, sample_lease):
    """Test signing a lease through the GraphQL API"""
    query = f"""
    mutation {{
      signLease(id: "{sample_lease.id}") {{
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
    assert lease_data["id"] == str(sample_lease.id)
    assert lease_data["signedByTenant"] is True
    assert lease_data["signedAt"] is not None


def test_active_leases_query(
    client, lease_repository, unit_repository, tenant_repository
):
    """Test retrieving active leases through the GraphQL API"""
    # Create units and tenants for leases
    unit1 = unit_repository._repository.create_originator(
        address="Active Lease Unit", is_leasable=True, is_leased=False, amenities=[]
    )
    unit_repository.save(unit1)

    tenant1 = tenant_repository._repository.create_originator(
        identification_number="active-lease-tenant",
        first_name="Active",
        last_name="Tenant",
        email="active@example.com",
        phone_number="555-123-7890",
        dob=date(1985, 5, 15),
        is_approved=True,
    )
    tenant_repository.save(tenant1)

    # Create an active lease (signed and within date range)
    today = date.today()
    active_lease = lease_repository._repository.create_originator(
        unit_id=unit1.id,
        tenant_ids=[tenant1.id],
        start_date=today - timedelta(days=30),  # Started 30 days ago
        end_date=today + timedelta(days=335),  # Ends in 335 days
        generated_at=today - timedelta(days=45),
        signed_at=today - timedelta(days=29),
        signed_by_tenant=True,
    )

    # Create an inactive lease (not signed)
    inactive_lease = lease_repository._repository.create_originator(
        unit_id=unit1.id,
        tenant_ids=[tenant1.id],
        start_date=today + timedelta(days=30),  # Starts in 30 days
        end_date=today + timedelta(days=395),  # Ends in 395 days
        generated_at=today - timedelta(days=5),
        signed_at=None,
        signed_by_tenant=False,
    )

    # Create an expired lease (signed but outside date range)
    expired_lease = lease_repository._repository.create_originator(
        unit_id=unit1.id,
        tenant_ids=[tenant1.id],
        start_date=today - timedelta(days=400),  # Started 400 days ago
        end_date=today - timedelta(days=35),  # Ended 35 days ago
        generated_at=today - timedelta(days=450),
        signed_at=today - timedelta(days=399),
        signed_by_tenant=True,
    )

    for lease in [active_lease, inactive_lease, expired_lease]:
        lease_repository.save(lease)

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


def test_create_lease_validation(client, sample_unit, tenant_repository):
    """Test that lease creation fails with unapproved tenants"""
    # Create unapproved tenant
    unapproved_tenant = tenant_repository._repository.create_originator(
        identification_number="unapproved-lease-tenant",
        first_name="Unapproved",
        last_name="TenantLease",
        email="unapproved_lease@example.com",
        phone_number="555-777-8888",
        dob=date(1982, 3, 20),
        is_approved=False,
    )
    tenant_repository.save(unapproved_tenant)

    start_date = date.today()
    end_date = start_date + timedelta(days=365)

    query = f"""
    mutation {{
      createLease(input: {{
        unitId: "{sample_unit.id}",
        tenantIds: ["{unapproved_tenant.id}"],
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
