# More Information: https://developers.google.com/calendar/v3/reference
import datetime

import pytz

from gcp_pilot.base import GoogleCloudPilotAPI, DiscoveryMixin


class Calendar(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, email, timezone: str = 'UTC', **kwargs):
        self.email = email
        self.timezone = pytz.timezone(timezone)

        super().__init__(
            serviceName='calendar',
            version='v3',
            cache_discovery=False,
            subject=email,
            **kwargs,
        )

    class Color:
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

    def date_to_str(self, dt, fmt='%Y-%m-%dT%H:%M:%SZ'):
        if isinstance(dt, datetime.datetime):
            if not dt.tzinfo:
                dt = self.timezone.localize(dt)
            dt = dt.astimezone(self.timezone)
        elif isinstance(dt, datetime.date):
            dt = datetime.datetime(year=dt.year, month=dt.month, day=dt.day, tzinfo=self.timezone)

        return dt.strftime(fmt)

    def get_events(self, calendar_id='primary', starts_at=None):
        min_date = self.date_to_str(starts_at) if starts_at else None

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

    def get_calendars(self):
        params = {}
        yield from self._paginate(
            method=self.client.calendarList().list,
            result_key='items',
            params=params,
        )

    def create_or_update_event(
            self,
            summary,
            location,
            start_at,
            end_at,
            event_id=None,
            description=None,
            attendees=None,
            recurrence_type=None,
            recurrence_amount=None,
            calendar_id='primary',
            color=None,
    ):
        def _build_time_field(dt):
            if isinstance(start_at, datetime.datetime):
                return {
                    'dateTime': self.date_to_str(dt),
                }
            else:
                return {
                    'date': self.date_to_str(dt, fmt='%Y-%m-%d'),
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
            data['attendees'] = attendees

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

    def delete_event(self, event_id, calendar_id='primary'):
        return self._execute(
            method=self.client.events().delete,
            calendarId=calendar_id,
            eventId=event_id,
        )
