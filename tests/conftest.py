# ruff: noqa
import os
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

os.environ["EVENTSOURCING_MAPPER_FACTORY"] = "eventsourcing.sqlite:Factory"
os.environ["EVENTSOURCING_INFRASTRUCTURE_FACTORY"] = "eventsourcing.sqlite:Factory"
os.environ["EVENTSOURCING_SQLITE_DBNAME"] = ":memory:"

from src.main import app
from src.domain.models import Unit, Tenant, Lease
from src.domain.repositories import UnitRepository, TenantRepository, LeaseRepository


# @pytest.fixture(autouse=True)
# def cleanup_database():
#     """Clean up the test database before each test"""
#     if os.path.exists("test.db"):
#         os.remove("test.db")
#     yield
#     if os.path.exists("test.db"):
#         os.remove("test.db")


@pytest.fixture
def client():
    """Returns a TestClient for the FastAPI application"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def unit_repository():
    """Returns a clean UnitRepository for each test"""
    repo = UnitRepository()
    yield repo
    repo.close()


@pytest.fixture
def tenant_repository():
    """Returns a clean TenantRepository for each test"""
    repo = TenantRepository()
    yield repo
    repo.close()


@pytest.fixture
def lease_repository():
    """Returns a clean LeaseRepository for each test"""
    repo = LeaseRepository()
    yield repo
    repo.close()


@pytest.fixture
def sample_unit(unit_repository):
    """Creates and returns a sample unit"""
    unit = Unit.create(
        address="123 Test St, Apt 1, Test City, TC 12345", amenities=["Parking", "Pool"]
    )
    unit_repository.create(unit)
    return unit


@pytest.fixture
def sample_tenant(tenant_repository):
    """Creates and returns a sample tenant"""
    tenant = Tenant.create(
        identification_number="123-45-6789",
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="555-123-4567",
        dob=date(1980, 1, 1),
    )
    tenant.approve()  # Approve the tenant for testing
    tenant_repository.create(tenant)
    return tenant


@pytest.fixture
def sample_lease(lease_repository, sample_unit, sample_tenant):
    """Creates and returns a sample lease with the sample unit and tenant"""
    today = date.today()
    start_date = today - timedelta(days=30)  # Started 30 days ago
    end_date = today + timedelta(days=335)  # Ends in 335 days (1 year - 30 days)

    lease = Lease.create(
        unit_id=sample_unit.id,
        tenant_ids=[sample_tenant.id],
        start_date=start_date,
        end_date=end_date,
    )
    lease_repository.create(lease)
    return lease
