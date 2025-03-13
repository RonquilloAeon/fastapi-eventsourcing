from eventsourcing.application import Application
from typing import List, Optional, Union
from uuid import UUID
import os

from .models import Unit, Tenant, Lease


class EventSourcingApplication(Application):
    """Base application class for our event-sourced system"""

    def __init__(self, env_vars=None, **kwargs):
        # Read PostgreSQL connection from environment vars if not provided
        if env_vars is None:
            env_vars = {}

        if "EVENTSOURCING_POSTGRES_DBNAME" not in env_vars:
            database_url = os.environ.get(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/fastapi_eventsourcing",
            )
            # Parse database URL into components for eventsourcing library
            if database_url.startswith("postgresql://"):
                parts = database_url.replace("postgresql://", "").split("@")
                user_pass = parts[0].split(":")
                host_port_db = parts[1].split("/")
                host_port = host_port_db[0].split(":")

                env_vars["EVENTSOURCING_POSTGRES_DBNAME"] = host_port_db[1]
                env_vars["EVENTSOURCING_POSTGRES_HOST"] = host_port[0]
                env_vars["EVENTSOURCING_POSTGRES_PORT"] = (
                    host_port[1] if len(host_port) > 1 else "5432"
                )
                env_vars["EVENTSOURCING_POSTGRES_USER"] = user_pass[0]
                env_vars["EVENTSOURCING_POSTGRES_PASSWORD"] = user_pass[1]

        super().__init__(env_vars=env_vars, **kwargs)


class UnitRepository(EventSourcingApplication):
    """Repository for Unit aggregates"""

    def save(self, unit: Unit) -> None:
        self.save_aggregate(unit)

    def get(self, unit_id: Union[str, UUID]) -> Optional[Unit]:
        try:
            return self.repository.get(unit_id)
        except KeyError:
            return None

    def get_all(self) -> List[Unit]:
        return [
            self.repository.get(unit_id)
            for unit_id in self.repository.get_all_notifications()
            if isinstance(self.repository.get(unit_id), Unit)
        ]

    def get_available_units(self) -> List[Unit]:
        """Get all units that are leasable and not currently leased"""
        units = self.get_all()
        return [unit for unit in units if unit.is_leasable and not unit.is_leased]

    def delete(self, unit: Unit) -> None:
        self.repository.delete(unit.id)


class TenantRepository(EventSourcingApplication):
    """Repository for Tenant aggregates"""

    def save(self, tenant: Tenant) -> None:
        self.save_aggregate(tenant)

    def get(self, tenant_id: Union[str, UUID]) -> Optional[Tenant]:
        try:
            return self.repository.get(tenant_id)
        except KeyError:
            return None

    def get_all(self) -> List[Tenant]:
        return [
            self.repository.get(tenant_id)
            for tenant_id in self.repository.get_all_notifications()
            if isinstance(self.repository.get(tenant_id), Tenant)
        ]

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

    def delete(self, tenant: Tenant) -> None:
        self.repository.delete(tenant.id)


class LeaseRepository(EventSourcingApplication):
    """Repository for Lease aggregates"""

    def save(self, lease: Lease) -> None:
        self.save_aggregate(lease)

    def get(self, lease_id: Union[str, UUID]) -> Optional[Lease]:
        try:
            return self.repository.get(lease_id)
        except KeyError:
            return None

    def get_all(self) -> List[Lease]:
        return [
            self.repository.get(lease_id)
            for lease_id in self.repository.get_all_notifications()
            if isinstance(self.repository.get(lease_id), Lease)
        ]

    def get_by_unit_id(self, unit_id: Union[str, UUID]) -> List[Lease]:
        """Find all leases for a specific unit"""
        leases = self.get_all()
        return [lease for lease in leases if str(lease.unit_id) == str(unit_id)]

    def get_by_tenant_id(self, tenant_id: Union[str, UUID]) -> List[Lease]:
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

    def delete(self, lease: Lease) -> None:
        self.repository.delete(lease.id)
