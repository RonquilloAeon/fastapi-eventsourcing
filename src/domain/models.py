from eventsourcing.domain import Aggregate, event
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List


class Unit(Aggregate):
    """Unit aggregate root representing a rental property"""

    @event("Created")
    def __init__(
        self,
        address: str,
        amenities: Optional[List[str]] = None,
        built_in: Optional[int] = None,
    ):
        self.address = address
        self.amenities = amenities or []
        self.is_leasable = True
        self.is_leased = False
        self.built_in = built_in
        self.created_at = datetime.now()

    @classmethod
    def create(
        cls,
        address: str,
        amenities: Optional[List[str]] = None,
        built_in: Optional[int] = None,
    ) -> "Unit":
        return cls(address=address, amenities=amenities, built_in=built_in)

    @event("MarkedAsLeased")
    def mark_as_leased(self) -> None:
        if not self.is_leasable:
            raise ValueError("Unit is not leasable")
        self.is_leased = True

    @event("MarkedAsAvailable")
    def mark_as_available(self) -> None:
        self.is_leased = False

    @event("MarkedAsUnleasable")
    def mark_as_unleasable(self) -> None:
        self.is_leasable = False

    @event("MarkedAsLeasable")
    def mark_as_leasable(self) -> None:
        self.is_leasable = True

    @event("AmenitiesUpdated")
    def update_amenities(self, amenities: List[str]) -> None:
        self.amenities = amenities

    @event("AddressUpdated")
    def update_address(self, address: str) -> None:
        self.address = address

    @event("BuiltInYearUpdated")
    def update_built_in_year(self, year: int) -> None:
        if not (1800 <= year <= datetime.now().year):
            raise ValueError(
                f"Built-in year must be between 1800 and {datetime.now().year}"
            )
        self.built_in = year


class Tenant(Aggregate):
    """Tenant aggregate root representing a potential renter"""

    @event("Created")
    def __init__(
        self,
        identification_number: str,
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str,
        dob: date,
    ):
        self.identification_number = identification_number
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone_number = phone_number
        self.dob = dob
        self.is_approved = False
        self.created_at = datetime.now()

    @classmethod
    def create(
        cls,
        identification_number: str,
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str,
        dob: date,
    ) -> "Tenant":
        return cls(
            identification_number=identification_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            dob=dob,
        )

    @event("Approved")
    def approve(self) -> None:
        self.is_approved = True

    @event("Disapproved")
    def disapprove(self) -> None:
        self.is_approved = False

    @event("ContactInfoUpdated")
    def update_contact_info(
        self, email: Optional[str] = None, phone_number: Optional[str] = None
    ) -> None:
        if email:
            self.email = email
        if phone_number:
            self.phone_number = phone_number


class Lease(Aggregate):
    """Lease aggregate root representing a contract between tenants and a property owner"""

    @event("Created")
    def __init__(
        self, unit_id: UUID, tenant_ids: List[UUID], start_date: date, end_date: date
    ):
        self.unit_id = unit_id
        self.tenant_ids = tenant_ids
        self.start_date = start_date
        self.end_date = end_date
        self.generated_at = datetime.now()
        self.signed_at = None
        self.signed_by_tenant = False

    @classmethod
    def create(
        cls, unit_id: UUID, tenant_ids: List[UUID], start_date: date, end_date: date
    ) -> "Lease":
        if start_date >= end_date:
            raise ValueError("End date must be after start date")

        return cls(
            unit_id=unit_id,
            tenant_ids=tenant_ids,
            start_date=start_date,
            end_date=end_date,
        )

    @event("SignedByTenant")
    def sign_by_tenant(self) -> None:
        self.signed_by_tenant = True
        self.signed_at = datetime.now()

    @event("TenantAdded")
    def add_tenant(self, tenant_id: UUID) -> None:
        if tenant_id not in self.tenant_ids:
            self.tenant_ids.append(tenant_id)

    @event("TenantRemoved")
    def remove_tenant(self, tenant_id: UUID) -> None:
        if tenant_id in self.tenant_ids:
            self.tenant_ids.remove(tenant_id)

    @event("DateUpdated")
    def update_dates(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> None:
        if start_date:
            self.start_date = start_date
        if end_date:
            self.end_date = end_date
        if self.start_date >= self.end_date:
            raise ValueError("End date must be after start date")
