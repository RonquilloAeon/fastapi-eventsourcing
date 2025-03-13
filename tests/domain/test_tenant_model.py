from uuid import UUID
from datetime import date
from src.domain.models import Tenant


def test_tenant_creation():
    """Test that a tenant can be created with proper attributes"""
    identification = "111-22-3333"
    first_name = "Jane"
    last_name = "Smith"
    email = "jane.smith@example.com"
    phone = "555-987-6543"
    dob = date(1985, 5, 15)

    tenant = Tenant.create(
        identification_number=identification,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone,
        dob=dob,
    )

    assert isinstance(tenant.id, UUID)
    assert tenant.identification_number == identification
    assert tenant.first_name == first_name
    assert tenant.last_name == last_name
    assert tenant.email == email
    assert tenant.phone_number == phone
    assert tenant.dob == dob
    assert tenant.is_approved is False


def test_tenant_approval(sample_tenant):
    """Test that a tenant can be marked as approved and disapproved"""
    # Sample tenant is approved by default in fixture
    assert sample_tenant.is_approved is True

    sample_tenant.disapprove()
    assert sample_tenant.is_approved is False

    sample_tenant.approve()
    assert sample_tenant.is_approved is True


def test_tenant_contact_info_update(sample_tenant):
    """Test that tenant contact info can be updated"""
    new_email = "newemail@example.com"
    new_phone = "555-111-2222"

    # Update just email
    sample_tenant.update_contact_info(email=new_email)
    assert sample_tenant.email == new_email
    assert sample_tenant.phone_number == "555-123-4567"  # Original value from fixture

    # Update just phone
    sample_tenant.update_contact_info(phone_number=new_phone)
    assert sample_tenant.email == new_email
    assert sample_tenant.phone_number == new_phone

    # Update both
    newer_email = "evennewermail@example.com"
    newer_phone = "555-333-4444"
    sample_tenant.update_contact_info(email=newer_email, phone_number=newer_phone)
    assert sample_tenant.email == newer_email
    assert sample_tenant.phone_number == newer_phone
