# More Information: https://developers.google.com/calendar/v3/reference
import datetime
from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

import pytz

from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI, ResourceType


class ResponseStatus(Enum):
    # Predefined options to attendee response status
    # Refs: <https://developers.google.com/calendar/api/v3/reference/events/update#attendees.responseStatus>

    needs_action = "needsAction"
    declined = "declined"
    tentative = "tentative"
    accepted = "accepted"


@dataclass
class Attendee:
    email: str
    optional: bool = False
    response_status: ResponseStatus | None = None

    def as_data(self) -> dict:
        return {
            "email": self.email,
            "optional": self.optional,
            "responseStatus": self.response_status,
        }


class Color(Enum):
    # Predefined colors.
    # For more color, use the endpoint: <https://developers.google.com/calendar/v3/reference/colors>

    light_blue = ("1", "#a4bdfc")
    light_green = ("2", "#7ae7bf")
    light_purple = ("3", "#dbadff")
    light_red = ("4", "#ff887c")
    yellow = ("5", "#fbd75b")
    light_orange = ("6", "#ffb878")
    water_green = ("7", "#46d6db")
    gray = ("8", "#e1e1e1")
    blue = ("9", "#5484ed")
    green = ("10", "#51b749")
    red = ("11", "#dc2127")


class SendUpdates(Enum):
    # Predefined options to send updates on events.
    # Refs: <https://developers.google.com/calendar/api/v3/reference/events/update#sendUpdates>

    all = "all"
    external_only = "externalOnly"
    none = "none"


class Calendar(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, email: str, timezone: str = "UTC", **kwargs):
        self.email = email
        self.timezone = pytz.timezone(timezone)

        super().__init__(
            serviceName="calendar",
            version="v3",
            cache_discovery=False,
            subject=email,
            **kwargs,
        )

    def _date_to_str(self, dt: datetime.date, fmt="%Y-%m-%dT%H:%M:%SZ"):
        if isinstance(dt, datetime.datetime):
            if not dt.tzinfo:
                dt = self.timezone.localize(dt)
            dt = dt.astimezone(self.timezone)
        elif isinstance(dt, datetime.date):
            dt = datetime.datetime(year=dt.year, month=dt.month, day=dt.day, tzinfo=self.timezone)

        return dt.strftime(fmt)

    def get_calendars(self) -> Generator[ResourceType, None, None]:
        params = {}
        yield from self._paginate(
            method=self.client.calendarList().list,
            result_key="items",
            params=params,
        )

    def get_calendar(self, calendar_id: str = "primary") -> ResourceType:
        return self._execute(
            method=self.client.calendars().get,
            calendarId=calendar_id,
        )

    def clear_calendar(self, calendar_id: str = "primary") -> ResourceType:
        params = {}
        return self._execute(
            method=self.client.calendars().clear,
            calendarId=calendar_id,
            params=params,
        )

    def delete_calendar(self, calendar_id: str = "primary") -> ResourceType:
        params = {}
        return self._execute(
            method=self.client.calendars().delete,
            calendarId=calendar_id,
            params=params,
        )

    def create_or_update_calendar(
        self,
        summary: str,
        description: str = "",
        timezone: str | None = None,
        calendar_id: str | None = None,
    ) -> ResourceType:
        if not calendar_id:
            return self.create_calendar(summary=summary, description=description, timezone=timezone)
        return self.update_calendar(
            calendar_id=calendar_id,
            summary=summary,
            description=description,
            timezone=timezone,
        )

    def create_calendar(self, summary: str, description: str = "", timezone: str | None = None) -> ResourceType:
        data = {
            "summary": summary,
            "description": description,
            "timeZone": timezone or self.timezone,
        }
        return self._execute(
            method=self.client.calendars().insert,
            body=data,
        )

    def update_calendar(
        self,
        calendar_id: str,
        summary: str | None = None,
        description: str | None = None,
        timezone: str | None = None,
    ) -> ResourceType:
        data = {}
        if summary:
            data["summary"] = summary
        if description:
            data["description"] = description
        if timezone:
            data["timeZone"] = timezone or self.timezone

        return self._execute(
            method=self.client.calendars().update,
            calendarId=calendar_id,
            body=data,
        )

    def watch_calendars(self, hook_url: str, hook_token: str | None = None, uuid: str | None = None) -> ResourceType:
        data = {
            "id": uuid or uuid4().hex,
            "type": "webhook",
            "address": hook_url,
        }
        if hook_token:
            data["token"] = hook_token

        return self._execute(
            method=self.client.calendarList().watch,
            body=data,
        )

    def unwatch(self, uuid: str, resource_id: str) -> ResourceType:
        data = {
            "id": uuid,
            "resource_id": resource_id,
        }
        return self._execute(
            method=self.client.channels().stop,
            body=data,
        )

    def create_or_update_event(
        self,
        summary: str,
        start_at: datetime.date,
        end_at: datetime.date,
        location: str | None = None,
        event_id: str | None = None,
        description: str | None = None,
        attendees: list[Attendee] | None = None,
        recurrence_type: str | None = None,
        recurrence_amount: str | None = None,
        calendar_id: str | None = "primary",
        color: Color | None = None,
        send_updates: SendUpdates | None = None,
    ) -> ResourceType:
        def _build_time_field(dt):
            if isinstance(start_at, datetime.datetime):
                return {
                    "dateTime": self._date_to_str(dt),
                }

            return {
                "date": self._date_to_str(dt, fmt="%Y-%m-%d"),
            }

        data = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": _build_time_field(dt=start_at),
            "end": _build_time_field(dt=end_at),
            "sendUpdates": send_updates,
        }

        if color:
            data["colorId"] = color[0]

        if recurrence_type and recurrence_amount:
            data["recurrence"] = [f"RRULE:FREQ={recurrence_type};COUNT={recurrence_amount}"]

        if attendees:
            data["attendees"] = [attendee.as_data() for attendee in attendees]

        if event_id:
            return self._execute(
                method=self.client.events().update,
                calendarId=calendar_id,
                eventId=event_id,
                body=data,
            )

        return self._execute(
            method=self.client.events().insert,
            calendarId=calendar_id,
            body=data,
        )

    def get_events(
        self,
        calendar_id: str = "primary",
        starts_at: datetime.date | None = None,
        ends_at: datetime.date | None = None,
    ) -> Generator[ResourceType, None, None]:
        min_date = self._date_to_str(starts_at) if starts_at else None
        max_date = self._date_to_str(ends_at) if ends_at else None

        page_size = 100
        params = dict(
            calendarId=calendar_id,
            timeMin=min_date,
            timeMax=max_date,
            singleEvents=True,
        )

        yield from self._paginate(
            method=self.client.events().list,
            result_key="items",
            params=params,
            order_by="startTime",
            limit=page_size,
        )

    def get_event(self, event_id: str, calendar_id: str = "primary") -> ResourceType:
        return self._execute(
            method=self.client.events().get,
            calendarId=calendar_id,
            eventId=event_id,
        )

    def delete_event(self, event_id: str, calendar_id: str = "primary") -> ResourceType:
        return self._execute(
            method=self.client.events().delete,
            calendarId=calendar_id,
            eventId=event_id,
        )

    def get_recurrent_events(self, event_id: str, calendar_id: str = "primary") -> Generator[ResourceType, None, None]:
        page_size = 100
        params = dict(
            calendarId=calendar_id,
            eventId=event_id,
        )

        yield from self._paginate(
            method=self.client.events().instances,
            result_key="items",
            params=params,
            limit=page_size,
        )

    def watch_events(
        self,
        hook_url: str,
        calendar_id: str = "primary",
        hook_token: str | None = None,
        uuid: str | None = None,
    ) -> ResourceType:
        data = {
            "id": uuid or uuid4().hex,
            "type": "webhook",
            "address": hook_url,
        }
        if hook_token:
            data["token"] = hook_token

        return self._execute(
            method=self.client.events().watch,
            calendarId=calendar_id,
            body=data,
        )

    def check_availability(
        self,
        starts_at: datetime,
        ends_at: datetime,
        timezone: str | None = None,
        calendar_ids: list[str] | None = None,
        calendar_id: str = "primary",
    ) -> ResourceType:
        data = {
            "timeMin": self._date_to_str(starts_at),
            "timeMax": self._date_to_str(ends_at),
            "timeZone": timezone or self.timezone,
            "groupExpansionMax": 100,  # max value
            "calendarExpansionMax": 50,  # max value
            "items": [{"id": calendar_id} for calendar_id in (calendar_ids or ["primary"])],
        }

        return self._execute(
            method=self.client.freeBusy().watch,
            calendarId=calendar_id,
            body=data,
        )["calendars"]


__all__ = (
    "Calendar",
    "Attendee",
    "Color",
    "ResponseStatus",
    "SendUpdates",
)
