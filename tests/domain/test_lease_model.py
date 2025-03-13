import pytest
from uuid import UUID
from datetime import date, timedelta
from src.domain.models import Lease


def test_lease_creation(sample_unit, sample_tenant):
    """Test that a lease can be created with proper attributes"""
    start_date = date.today()
    end_date = start_date + timedelta(days=365)  # 1 year lease

    lease = Lease.create(
        unit_id=sample_unit.id,
        tenant_ids=[sample_tenant.id],
        start_date=start_date,
        end_date=end_date,
    )

    assert isinstance(lease.id, UUID)
    assert lease.unit_id == sample_unit.id
    assert sample_tenant.id in lease.tenant_ids
    assert lease.start_date == start_date
    assert lease.end_date == end_date
    assert lease.signed_at is None
    assert lease.signed_by_tenant is False


def test_lease_sign_by_tenant(sample_lease):
    """Test that a lease can be signed by tenant"""
    assert sample_lease.signed_by_tenant is False
    assert sample_lease.signed_at is None

    sample_lease.sign_by_tenant()

    assert sample_lease.signed_by_tenant is True
    assert sample_lease.signed_at is not None


def test_lease_add_tenant(sample_lease, tenant_repository):
    """Test that a tenant can be added to a lease"""
    from datetime import date

    # Create a second tenant
    tenant2 = tenant_repository._repository.create_originator(
        OriginatorID=UUID,
        OriginatorVersion=int,
        identification_number="444-55-6666",
        first_name="Additional",
        last_name="Tenant",
        email="additional@example.com",
        phone_number="555-444-3333",
        dob=date(1990, 6, 15),
        is_approved=True,
        created_at=date.today(),
    )

    initial_tenant_count = len(sample_lease.tenant_ids)

    sample_lease.add_tenant(tenant2.id)

    assert len(sample_lease.tenant_ids) == initial_tenant_count + 1
    assert tenant2.id in sample_lease.tenant_ids


def test_lease_remove_tenant(sample_lease, sample_tenant):
    """Test that a tenant can be removed from a lease"""
    assert sample_tenant.id in sample_lease.tenant_ids

    sample_lease.remove_tenant(sample_tenant.id)

    assert sample_tenant.id not in sample_lease.tenant_ids
    assert len(sample_lease.tenant_ids) == 0


def test_lease_update_dates(sample_lease):
    """Test that lease dates can be updated"""
    new_start = sample_lease.start_date + timedelta(days=15)
    new_end = sample_lease.end_date + timedelta(days=30)

    sample_lease.update_dates(start_date=new_start, end_date=new_end)

    assert sample_lease.start_date == new_start
    assert sample_lease.end_date == new_end


def test_lease_invalid_dates():
    """Test that lease creation fails with invalid dates"""
    from src.domain.models import Unit, Tenant

    unit = Unit.create(address="Test Address")

    tenant = Tenant.create(
        identification_number="111-22-3333",
        first_name="Test",
        last_name="Person",
        email="test@example.com",
        phone_number="555-123-4567",
        dob=date(1980, 1, 1),
    )

    today = date.today()

    # End date before start date
    with pytest.raises(ValueError):
        Lease.create(
            unit_id=unit.id,
            tenant_ids=[tenant.id],
            start_date=today,
            end_date=today - timedelta(days=1),
        )

    # Same start and end date
    with pytest.raises(ValueError):
        Lease.create(
            unit_id=unit.id, tenant_ids=[tenant.id], start_date=today, end_date=today
        )
