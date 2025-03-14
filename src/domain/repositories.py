from typing import List, Optional, Union, Iterator, Tuple
from uuid import UUID, uuid5, NAMESPACE_URL
from datetime import date

from eventsourcing.application import Application, AggregateNotFoundError
from eventsourcing.domain import DomainEvent
from eventsourcing.persistence import Transcoding
from eventsourcing.application import EventSourcedLog

from .models import Unit, Tenant, Lease


# Custom transcoding for date objects
class DateTranscoding(Transcoding):
    """Custom transcoding for datetime.date objects"""

    type = date
    name = "date"

    def encode(self, obj: date) -> str:
        """Convert date to ISO format string"""
        return obj.isoformat()

    def decode(self, data: str) -> date:
        """Convert ISO format string to date object"""
        return date.fromisoformat(data)


class EventSourcingApplication(Application):
    """Base application class for our event-sourced system"""

    def register_transcodings(self, transcoder):
        """Register custom transcodings"""
        super().register_transcodings(transcoder)
        transcoder.register(DateTranscoding())


# Domain event for logging unit operations
class UnitLogged(DomainEvent):
    unit_id: UUID


# Domain event for logging tenant operations
class TenantLogged(DomainEvent):
    tenant_id: UUID


# Domain event for logging lease operations
class LeaseLogged(DomainEvent):
    lease_id: UUID


class UnitRepository(EventSourcingApplication):
    """Repository for Unit aggregates"""

    name = "unit"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit_log: EventSourcedLog[UnitLogged] = EventSourcedLog(
            self.events, uuid5(NAMESPACE_URL, "/unit_log"), UnitLogged
        )

    def create(self, unit: Unit) -> None:
        logged = self.unit_log.trigger_event(unit_id=unit.id)
        self.save(unit, logged)

    def save(self, unit: Unit, *args, **kwargs) -> None:
        # Use save() method from the Application class to save the aggregate
        super().save(unit, *args, **kwargs)

    def get(self, unit_id: UUID) -> Optional[Unit]:
        try:
            return self.repository.get(unit_id)
        except AggregateNotFoundError:
            return None

    def get_all(self) -> List[Unit]:
        units = []
        for notification in self.unit_log.get():
            unit = self.repository.get(notification.unit_id)
            if isinstance(unit, Unit):
                units.append(unit)
        return units

    def get_units(
        self,
        *,
        gt: int | None = None,
        lte: int | None = None,
        desc: bool = True,
        limit: int | None = None,
    ) -> Iterator[Tuple[int, Unit]]:
        """Get units with their notification positions for cursor-based pagination."""
        for notification in self.unit_log.get(gt=gt, lte=lte, desc=desc, limit=limit):
            try:
                unit = self.repository.get(notification.unit_id)
                yield notification.originator_version, unit
            except KeyError:
                continue

    def get_available_units(self) -> List[Unit]:
        """Get all units that are leasable and not currently leased"""
        units = self.get_all()
        return [unit for unit in units if unit.is_leasable and not unit.is_leased]


class TenantRepository(EventSourcingApplication):
    """Repository for Tenant aggregates"""

    name = "tenant"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant_log: EventSourcedLog[TenantLogged] = EventSourcedLog(
            self.events, uuid5(NAMESPACE_URL, "/tenant_log"), TenantLogged
        )

    def create(self, tenant: Tenant) -> None:
        logged = self.tenant_log.trigger_event(tenant_id=tenant.id)
        self.save(tenant, logged)

    def get(self, tenant_id: UUID) -> Optional[Tenant]:
        try:
            return self.repository.get(tenant_id)
        except AggregateNotFoundError:
            return None

    def get_all(self) -> List[Tenant]:
        tenants = []
        for notification in self.tenant_log.get():
            tenant = self.repository.get(notification.tenant_id)
            if isinstance(tenant, Tenant):
                tenants.append(tenant)
        return tenants

    def get_tenants(
        self,
        *,
        gt: int | None = None,
        lte: int | None = None,
        desc: bool = True,
        limit: int | None = None,
    ) -> Iterator[Tuple[int, Tenant]]:
        """Get tenants with their notification positions for cursor-based pagination."""
        for notification in self.tenant_log.get(gt=gt, lte=lte, desc=desc, limit=limit):
            try:
                tenant = self.repository.get(notification.tenant_id)
                yield notification.originator_version, tenant
            except KeyError:
                continue

    def get_by_identification_number(
        self, identification_number: str
    ) -> Optional[Tenant]:
        """Find a tenant by their unique identification number"""
        tenants = self.get_all()
        for tenant in tenants:
            if tenant.identification_number == identification_number:
                return tenant
        return None

    def get_approved_tenants(self) -> List[Tenant]:
        """Get all tenants that have been approved"""
        tenants = self.get_all()
        return [tenant for tenant in tenants if tenant.is_approved]


class LeaseRepository(EventSourcingApplication):
    """Repository for Lease aggregates"""

    name = "lease"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lease_log: EventSourcedLog[LeaseLogged] = EventSourcedLog(
            self.events, uuid5(NAMESPACE_URL, "/lease_log"), LeaseLogged
        )

    def create(self, lease: Lease) -> None:
        logged = self.lease_log.trigger_event(lease_id=lease.id)
        self.save(lease, logged)

    def save(self, lease: Lease, *args, **kwargs) -> None:
        # Use save() method from the Application class to save the aggregate
        super().save(lease, *args, **kwargs)

    def get(self, lease_id: Union[str, UUID]) -> Optional[Lease]:
        try:
            return self.repository.get(lease_id)
        except AggregateNotFoundError:
            return None

    def get_all(self) -> List[Lease]:
        leases = []
        for notification in self.lease_log.get():
            lease = self.repository.get(notification.lease_id)
            if isinstance(lease, Lease):
                leases.append(lease)
        return leases

    def get_leases(
        self,
        *,
        gt: int | None = None,
        lte: int | None = None,
        desc: bool = True,
        limit: int | None = None,
    ) -> Iterator[Tuple[int, Lease]]:
        """Get leases with their notification positions for cursor-based pagination."""
        for notification in self.lease_log.get(gt=gt, lte=lte, desc=desc, limit=limit):
            try:
                lease = self.repository.get(notification.lease_id)
                yield notification.originator_version, lease
            except KeyError:
                continue

    def get_by_unit_id(self, unit_id: UUID) -> List[Lease]:
        """Find all leases for a specific unit"""
        leases = self.get_all()
        return [lease for lease in leases if str(lease.unit_id) == str(unit_id)]

    def get_by_tenant_id(self, tenant_id: UUID) -> List[Lease]:
        """Find all leases for a specific tenant"""
        leases = self.get_all()
        return [
            lease
            for lease in leases
            if str(tenant_id) in [str(tid) for tid in lease.tenant_ids]
        ]

    def get_active_leases(self) -> List[Lease]:
        """Get all leases that are currently active (signed and within date range)"""
        from datetime import date

        today = date.today()
        leases = self.get_all()
        return [
            lease
            for lease in leases
            if lease.signed_by_tenant and lease.start_date <= today <= lease.end_date
        ]
