from src.domain.models import Unit


def test_save_and_get_unit(unit_repository):
    """Test saving and retrieving a unit through repository"""
    unit = Unit.create(
        address="123 Repository Test St", amenities=["Test Amenity 1", "Test Amenity 2"]
    )

    # Save the unit
    unit_repository.save(unit)

    # Retrieve the unit
    retrieved_unit = unit_repository.get(unit.id)

    # Verify attributes
    assert retrieved_unit.id == unit.id
    assert retrieved_unit.address == unit.address
    assert retrieved_unit.amenities == unit.amenities
    assert retrieved_unit.is_leasable == unit.is_leasable
    assert retrieved_unit.is_leased == unit.is_leased


def test_get_all_units(unit_repository):
    """Test retrieving all units through repository"""
    # Create and save some units
    addresses = [
        "123 First St, Test City",
        "456 Second Ave, Test City",
        "789 Third Blvd, Test City",
    ]

    for address in addresses:
        unit = Unit.create(address=address)
        unit_repository.save(unit)

    # Retrieve all units
    units = unit_repository.get_all()

    # Verify count
    assert len(units) == len(addresses)

    # Verify addresses are in the retrieved units
    retrieved_addresses = [unit.address for unit in units]
    for address in addresses:
        assert address in retrieved_addresses


def test_get_available_units(unit_repository):
    """Test retrieving available units through repository"""
    # Create some units with different states
    available_address = "123 Available St"
    leased_address = "456 Leased St"
    unleasable_address = "789 Unleasable St"

    # Available unit (leasable and not leased)
    available_unit = Unit.create(address=available_address)
    unit_repository.save(available_unit)

    # Leased unit (leasable but leased)
    leased_unit = Unit.create(address=leased_address)
    leased_unit.mark_as_leased()
    unit_repository.save(leased_unit)

    # Unleasable unit
    unleasable_unit = Unit.create(address=unleasable_address)
    unleasable_unit.mark_as_unleasable()
    unit_repository.save(unleasable_unit)

    # Retrieve available units
    available_units = unit_repository.get_available_units()

    # Verify only the available unit is returned
    assert len(available_units) == 1
    assert available_units[0].address == available_address


def test_delete_unit(unit_repository):
    """Test deleting a unit through repository"""
    # Create and save a unit
    unit = Unit.create(address="Delete Test Address")
    unit_repository.save(unit)

    # Verify unit exists
    assert unit_repository.get(unit.id) is not None

    # Delete the unit
    unit_repository.delete(unit)

    # Verify unit no longer exists
    assert unit_repository.get(unit.id) is None
