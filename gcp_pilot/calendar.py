# More Information: https://developers.google.com/calendar/v3/reference
import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Generator, List, Dict

import pytz

from gcp_pilot.base import GoogleCloudPilotAPI, DiscoveryMixin, ResourceType


@dataclass
class Attendee:
    email: str
    optional: bool = False

    def as_data(self) -> Dict:
        return {
            'email': self.email,
            'optional': self.optional,
        }


class Color(Enum):
    # Predefined colors.
    # For more color, use the endpoint: <https://developers.google.com/calendar/v3/reference/colors>
    light_blue = ('1', '#a4bdfc')
    light_green = ('2', '#7ae7bf')
    light_purple = ('3', '#dbadff')
    light_red = ('4', '#ff887c')
    yellow = ('5', '#fbd75b')
    light_orange = ('6', '#ffb878')
    water_green = ('7', '#46d6db')
    gray = ('8', '#e1e1e1')
    blue = ('9', '#5484ed')
    green = ('10', '#51b749')
    red = ('11', '#dc2127')


class Calendar(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, email: str, timezone: str = 'UTC', **kwargs):
        self.email = email
        self.timezone = pytz.timezone(timezone)

        super().__init__(
            serviceName='calendar',
            version='v3',
            cache_discovery=False,
            subject=email,
            **kwargs,
        )

    def _date_to_str(self, dt: datetime.date, fmt='%Y-%m-%dT%H:%M:%SZ'):
        if isinstance(dt, datetime.datetime):
            if not dt.tzinfo:
                dt = self.timezone.localize(dt)
            dt = dt.astimezone(self.timezone)
        elif isinstance(dt, datetime.date):
            dt = datetime.datetime(year=dt.year, month=dt.month, day=dt.day, tzinfo=self.timezone)

        return dt.strftime(fmt)

    def get_events(
            self,
            calendar_id: str = 'primary',
            starts_at: datetime.date = None,
    ) -> Generator[ResourceType, None, None]:
        min_date = self._date_to_str(starts_at) if starts_at else None

        page_size = 100
        params = dict(
            calendarId=calendar_id,
            timeMin=min_date,
            singleEvents=True,
        )

        yield from self._paginate(
            method=self.client.events().list,
            result_key='items',
            params=params,
            order_by='startTime',
            limit=page_size,
        )

    def get_calendars(self) -> Generator[ResourceType, None, None]:
        params = {}
        yield from self._paginate(
            method=self.client.calendarList().list,
            result_key='items',
            params=params,
        )

    def create_or_update_event(
            self,
            summary: str,
            location: str,
            start_at: datetime.date,
            end_at: datetime.date,
            event_id: str = None,
            description: str = None,
            attendees: List[Attendee] = None,
            recurrence_type: str = None,
            recurrence_amount: str = None,
            calendar_id: str = 'primary',
            color: Color = None,
    ) -> ResourceType:
        def _build_time_field(dt):
            if isinstance(start_at, datetime.datetime):
                return {
                    'dateTime': self._date_to_str(dt),
                }
            else:
                return {
                    'date': self._date_to_str(dt, fmt='%Y-%m-%d'),
                }

        data = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': _build_time_field(dt=start_at),
            'end': _build_time_field(dt=end_at),
        }

        if color:
            data['colorId'] = color[0]

        if recurrence_type and recurrence_amount:
            data['recurrence'] = [
                f'RRULE:FREQ={recurrence_type};COUNT={recurrence_amount}'
            ]

        if attendees:
            data['attendees'] = [attendee.as_data() for attendee in attendees]

        if event_id:
            return self._execute(
                method=self.client.events().update,
                calendarId=calendar_id,
                eventId=event_id,
                body=data,
            )
        else:
            return self._execute(
                method=self.client.events().insert,
                calendarId=calendar_id,
                body=data,
            )

    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> ResourceType:
        return self._execute(
            method=self.client.events().delete,
            calendarId=calendar_id,
            eventId=event_id,
        )
