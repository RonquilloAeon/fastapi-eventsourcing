import strawberry
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID

# Import our domain models and repositories
from ..domain.models import Unit, Tenant, Lease
from strawberry.types import Info


# GraphQL Types - Rental Management
@strawberry.type
class UnitType:
    id: strawberry.ID
    address: str
    amenities: List[str]
    is_leasable: bool
    is_leased: bool
    created_at: datetime

    @strawberry.field
    def leases(self, info: Info) -> List["LeaseType"]:
        repo = info.context["lease_repo"]
        return repo.get_by_unit_id(UUID(self.id))

    @strawberry.field
    def active_lease(self, info: Info) -> Optional["LeaseType"]:
        repo = info.context["lease_repo"]
        leases = repo.get_by_unit_id(UUID(self.id))
        today = date.today()
        active_leases = [
            lease
            for lease in leases
            if lease.signed_by_tenant and lease.start_date <= today <= lease.end_date
        ]
        return active_leases[0] if active_leases else None


@strawberry.type
class TenantType:
    id: strawberry.ID
    identification_number: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    dob: date
    is_approved: bool
    created_at: datetime

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @strawberry.field
    def leases(self, info: Info) -> List["LeaseType"]:
        repo = info.context["lease_repo"]
        return repo.get_by_tenant_id(UUID(self.id))

    @strawberry.field
    def active_leases(self, info: Info) -> List["LeaseType"]:
        repo = info.context["lease_repo"]
        all_tenant_leases = repo.get_by_tenant_id(UUID(self.id))
        today = date.today()
        return [
            lease
            for lease in all_tenant_leases
            if lease.signed_by_tenant and lease.start_date <= today <= lease.end_date
        ]


@strawberry.type
class LeaseType:
    id: strawberry.ID
    generated_at: datetime
    signed_at: Optional[datetime]
    signed_by_tenant: bool
    start_date: date
    end_date: date
    unit_id: strawberry.ID
    tenant_ids: List[strawberry.ID]

    @strawberry.field
    def unit(self, info: Info) -> Optional[UnitType]:
        repo = info.context["unit_repo"]
        return repo.get(UUID(self.unit_id))

    @strawberry.field
    def tenants(self, info: Info) -> List[TenantType]:
        repo = info.context["tenant_repo"]
        return [
            repo.get(UUID(tenant_id))
            for tenant_id in self.tenant_ids
            if repo.get(UUID(tenant_id))
        ]

    @strawberry.field
    def is_active(self) -> bool:
        today = date.today()
        return self.signed_by_tenant and self.start_date <= today <= self.end_date


# Input types for mutations - Rental Management
@strawberry.input
class UnitInput:
    address: str
    amenities: List[str] = strawberry.field(default_factory=list)


@strawberry.input
class TenantInput:
    identification_number: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    dob: date


@strawberry.input
class LeaseInput:
    unit_id: strawberry.ID
    tenant_ids: List[strawberry.ID]
    start_date: date
    end_date: date


# Query resolvers
@strawberry.type
class Query:
    # Rental Management Queries
    @strawberry.field
    def unit(self, info: Info, id: strawberry.ID) -> Optional[UnitType]:
        repo = info.context["unit_repo"]
        return repo.get(UUID(id))

    @strawberry.field
    def units(self, info: Info) -> List[UnitType]:
        repo = info.context["unit_repo"]
        return repo.get_all()

    @strawberry.field
    def available_units(self, info: Info) -> List[UnitType]:
        repo = info.context["unit_repo"]
        return repo.get_available_units()

    @strawberry.field
    def tenant(self, info: Info, id: strawberry.ID) -> Optional[TenantType]:
        repo = info.context["tenant_repo"]
        return repo.get(UUID(id))

    @strawberry.field
    def tenant_by_identification(
        self, info: Info, identification_number: str
    ) -> Optional[TenantType]:
        repo = info.context["tenant_repo"]
        return repo.get_by_identification_number(identification_number)

    @strawberry.field
    def tenants(self, info: Info) -> List[TenantType]:
        repo = info.context["tenant_repo"]
        return repo.get_all()

    @strawberry.field
    def approved_tenants(self, info: Info) -> List[TenantType]:
        repo = info.context["tenant_repo"]
        return repo.get_approved_tenants()

    @strawberry.field
    def lease(self, info: Info, id: strawberry.ID) -> Optional[LeaseType]:
        repo = info.context["lease_repo"]
        return repo.get(UUID(id))

    @strawberry.field
    def leases(self, info: Info) -> List[LeaseType]:
        repo = info.context["lease_repo"]
        return repo.get_all()

    @strawberry.field
    def active_leases(self, info: Info) -> List[LeaseType]:
        repo = info.context["lease_repo"]
        return repo.get_active_leases()


# Mutation resolvers
@strawberry.type
class Mutation:
    # Rental Management Mutations
    @strawberry.mutation
    def create_unit(self, info: Info, input: UnitInput) -> UnitType:
        repo = info.context["unit_repo"]
        unit = Unit.create(address=input.address, amenities=input.amenities)
        repo.create(unit)
        return unit

    @strawberry.mutation
    def update_unit_amenities(
        self, info: Info, id: strawberry.ID, amenities: List[str]
    ) -> UnitType:
        repo = info.context["unit_repo"]
        unit = repo.get(UUID(id))
        if not unit:
            raise ValueError(f"Unit with ID {id} not found")

        unit.update_amenities(amenities)
        repo.save(unit)
        return unit

    @strawberry.mutation
    def mark_unit_as_leased(self, info: Info, id: strawberry.ID) -> UnitType:
        repo = info.context["unit_repo"]
        unit = repo.get(UUID(id))
        if not unit:
            raise ValueError(f"Unit with ID {id} not found")

        unit.mark_as_leased()
        repo.save(unit)
        return unit

    @strawberry.mutation
    def mark_unit_as_available(self, info: Info, id: strawberry.ID) -> UnitType:
        repo = info.context["unit_repo"]
        unit = repo.get(UUID(id))
        if not unit:
            raise ValueError(f"Unit with ID {id} not found")

        unit.mark_as_available()
        repo.save(unit)
        return unit

    @strawberry.mutation
    def create_tenant(self, info: Info, input: TenantInput) -> TenantType:
        repo = info.context["tenant_repo"]

        # Check if tenant with same identification number already exists
        existing_tenant = repo.get_by_identification_number(input.identification_number)
        if existing_tenant:
            raise ValueError(
                f"Tenant with identification number {input.identification_number} already exists"
            )

        tenant = Tenant.create(
            identification_number=input.identification_number,
            first_name=input.first_name,
            last_name=input.last_name,
            email=input.email,
            phone_number=input.phone_number,
            dob=input.dob,
        )
        repo.create(tenant)
        return tenant

    @strawberry.mutation
    def approve_tenant(self, info: Info, id: strawberry.ID) -> TenantType:
        repo = info.context["tenant_repo"]
        tenant = repo.get(UUID(id))
        if not tenant:
            raise ValueError(f"Tenant with ID {id} not found")

        tenant.approve()
        repo.save(tenant)
        return tenant

    @strawberry.mutation
    def disapprove_tenant(self, info: Info, id: strawberry.ID) -> TenantType:
        repo = info.context["tenant_repo"]
        tenant = repo.get(UUID(id))
        if not tenant:
            raise ValueError(f"Tenant with ID {id} not found")

        tenant.disapprove()
        repo.save(tenant)
        return tenant

    @strawberry.mutation
    def update_tenant_contact(
        self,
        info: Info,
        id: strawberry.ID,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> TenantType:
        repo = info.context["tenant_repo"]
        tenant = repo.get(UUID(id))
        if not tenant:
            raise ValueError(f"Tenant with ID {id} not found")

        tenant.update_contact_info(email=email, phone_number=phone_number)
        repo.save(tenant)
        return tenant

    @strawberry.mutation
    def create_lease(self, info: Info, input: LeaseInput) -> LeaseType:
        # Validate unit exists
        unit_repo = info.context["unit_repo"]
        unit = unit_repo.get(UUID(input.unit_id))
        if not unit:
            raise ValueError(f"Unit with ID {input.unit_id} not found")

        if not unit.is_leasable:
            raise ValueError(f"Unit with ID {input.unit_id} is not leasable")

        # Validate all tenants exist and are approved
        tenant_repo = info.context["tenant_repo"]
        for tenant_id in input.tenant_ids:
            tenant = tenant_repo.get(UUID(tenant_id))
            if not tenant:
                raise ValueError(f"Tenant with ID {tenant_id} not found")
            if not tenant.is_approved:
                raise ValueError(f"Tenant with ID {tenant_id} is not approved")

        # Create the lease
        lease_repo = info.context["lease_repo"]
        lease = Lease.create(
            unit_id=input.unit_id,
            tenant_ids=input.tenant_ids,
            start_date=input.start_date,
            end_date=input.end_date,
        )
        lease_repo.create(lease)
        return lease

    @strawberry.mutation
    def sign_lease(self, info: Info, id: strawberry.ID) -> LeaseType:
        lease_repo = info.context["lease_repo"]
        lease = lease_repo.get(UUID(id))
        if not lease:
            raise ValueError(f"Lease with ID {id} not found")

        lease.sign_by_tenant()
        lease_repo.save(lease)

        # When lease is signed, mark the unit as leased
        unit_repo = info.context["unit_repo"]
        unit = unit_repo.get(UUID(lease.unit_id))
        if unit:
            unit.mark_as_leased()
            unit_repo.save(unit)

        return lease
