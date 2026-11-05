"""metrolen: convert, format, and parse lengths (standard library only)."""

__version__ = "2.0.0"

#: Supported unit names, from smallest to largest.
UNITS = ("mm", "cm", "m", "km", "mi")

_METERS_PER_UNIT = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "km": 1000.0,
    "mi": 1609.344,
}

_METRIC = frozenset({"mm", "cm", "m", "km"})


def _check_unit(unit: str) -> None:
    """Raise ValueError if a unit name is not supported."""
    if unit not in _METERS_PER_UNIT:
        raise ValueError(f"unknown unit: {unit!r}")


def supported_units() -> list:
    """Return the supported unit names as a list, from smallest to largest."""
    return list(UNITS)


def is_metric(unit: str) -> bool:
    """Report whether a unit belongs to the metric system.

    :param unit: A unit name.
    :returns: True for metric units.
    :raises ValueError: If the unit is unknown.
    """
    _check_unit(unit)
    return unit in _METRIC


def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a length from one unit to another.

    :param value: The length to convert.
    :param from_unit: The unit of ``value``.
    :param to_unit: The unit to convert to.
    :returns: The converted length.
    :raises ValueError: If either unit is unknown.
    """
    _check_unit(from_unit)
    _check_unit(to_unit)
    return value * _METERS_PER_UNIT[from_unit] / _METERS_PER_UNIT[to_unit]


def format_quantity(value: float, unit: str, precision: int = 3) -> str:
    """Format a length for display.

    :param value: The length.
    :param unit: Its unit.
    :param precision: Number of decimal places.
    :returns: Text such as ``"2.500 m"``.
    :raises ValueError: If the unit is unknown.
    """
    _check_unit(unit)
    return f"{value:.{precision}f} {unit}"


def parse_quantity(text: str) -> tuple:
    """Parse text such as ``"12 cm"`` into a value and a unit.

    :param text: A number, a space, and a unit name.
    :returns: A ``(value, unit)`` tuple.
    :raises ValueError: If the text is malformed or the unit is unknown.
    """
    parts = text.split()
    if len(parts) != 2:
        raise ValueError(f"expected '<number> <unit>', got {text!r}")
    value, unit = float(parts[0]), parts[1]
    _check_unit(unit)
    return (value, unit)
