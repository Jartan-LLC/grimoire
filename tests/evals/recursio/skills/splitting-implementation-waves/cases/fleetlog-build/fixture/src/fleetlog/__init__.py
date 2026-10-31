"""Company fleet records: fuel economy, servicing, trip logs and running costs."""

from .model import FillUp, FleetError, FuelKind, ServiceRecord, Trip, Vehicle

__all__ = ["FillUp", "FleetError", "FuelKind", "ServiceRecord", "Trip", "Vehicle"]
