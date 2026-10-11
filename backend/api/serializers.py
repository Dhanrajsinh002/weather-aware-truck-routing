"""DRF serializers for request validation and response mapping."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from rest_framework import serializers


class LocationSerializer(serializers.Serializer):
    lat = serializers.FloatField(required=True, min_value=-90.0, max_value=90.0)
    lng = serializers.FloatField(required=True, min_value=-180.0, max_value=180.0)
    label = serializers.CharField(required=False, default="", allow_blank=True)


class AnalyzeRequestSerializer(serializers.Serializer):
    origin = LocationSerializer(required=True)
    destination = LocationSerializer(required=True)
    departure_time = serializers.DateTimeField(required=True)
    load_weight_lb = serializers.FloatField(required=True, min_value=1.0, max_value=100000.0)
    checkpoint_interval_miles = serializers.ChoiceField(
        choices=["auto", 10, 25, 50, "10", "25", "50"],
        default="auto",
    )

    def validate_departure_time(self, value: datetime) -> datetime:
        # Convert naive to UTC if needed
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)

        now = datetime.now(timezone.utc)
        if value < (now - timedelta(hours=1, minutes=5)):
            raise serializers.ValidationError("Departure time cannot be more than 1 hour in the past.")
        if value > (now + timedelta(days=14)):
            raise serializers.ValidationError("Departure time cannot be more than 14 days ahead.")

        return value

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        interval = ret.get("checkpoint_interval_miles")
        if interval in ("10", 10):
            ret["checkpoint_interval_miles"] = 10
        elif interval in ("25", 25):
            ret["checkpoint_interval_miles"] = 25
        elif interval in ("50", 50):
            ret["checkpoint_interval_miles"] = 50
        else:
            ret["checkpoint_interval_miles"] = "auto"
        return ret
