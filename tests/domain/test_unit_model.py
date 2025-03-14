import pytest
from uuid import UUID
from src.domain.models import Unit
from datetime import datetime


def test_unit_creation():
    """Test that a unit can be created with proper attributes"""
    address = "456 Test Ave, Test City"
    amenities = ["Parking", "Gym"]
    built_in = 1985

    unit = Unit.create(address=address, amenities=amenities, built_in=built_in)

    assert isinstance(unit.id, UUID)
    assert unit.address == address
    assert unit.amenities == amenities
    assert unit.built_in == built_in
    assert unit.is_leasable is True
    assert unit.is_leased is False


def test_unit_mark_as_leased(sample_unit):
    """Test that a unit can be marked as leased"""
    assert sample_unit.is_leased is False

    sample_unit.mark_as_leased()

    assert sample_unit.is_leased is True


def test_unit_mark_as_available(sample_unit):
    """Test that a unit can be marked as available"""
    sample_unit.mark_as_leased()
    assert sample_unit.is_leased is True

    sample_unit.mark_as_available()

    assert sample_unit.is_leased is False


def test_unit_mark_as_unleasable(sample_unit):
    """Test that a unit can be marked as unleasable"""
    assert sample_unit.is_leasable is True

    sample_unit.mark_as_unleasable()

    assert sample_unit.is_leasable is False


def test_unit_mark_as_leasable(sample_unit):
    """Test that a unit can be marked as leasable"""
    sample_unit.mark_as_unleasable()
    assert sample_unit.is_leasable is False

    sample_unit.mark_as_leasable()

    assert sample_unit.is_leasable is True


def test_unit_cannot_be_leased_if_unleasable(sample_unit):
    """Test that a unit cannot be marked as leased if it's not leasable"""
    sample_unit.mark_as_unleasable()

    with pytest.raises(ValueError):
        sample_unit.mark_as_leased()


def test_unit_update_amenities(sample_unit):
    """Test that unit amenities can be updated"""
    new_amenities = ["Dishwasher", "Washer/Dryer", "Balcony"]

    sample_unit.update_amenities(new_amenities)

    assert sample_unit.amenities == new_amenities


def test_unit_update_address(sample_unit):
    """Test that unit address can be updated"""
    new_address = "789 New Address St, New City"

    sample_unit.update_address(new_address)

    assert sample_unit.address == new_address


def test_unit_update_built_in_year(sample_unit):
    """Test that unit built_in year can be updated"""
    new_year = 1990

    sample_unit.update_built_in_year(new_year)

    assert sample_unit.built_in == new_year


def test_unit_built_in_year_validation():
    """Test that built_in year validation works correctly"""
    unit = Unit.create(address="Test Address")
    current_year = datetime.now().year

    with pytest.raises(ValueError):
        unit.update_built_in_year(1799)  # Too early

    with pytest.raises(ValueError):
        unit.update_built_in_year(current_year + 1)  # Future year
