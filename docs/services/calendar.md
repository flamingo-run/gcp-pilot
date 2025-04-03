# Calendar

Calendar is a service that allows you to manage Google Calendar resources. The `Calendar` class in gcp-pilot provides a high-level interface for interacting with Google Calendar API.

## Installation

To use the Calendar functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.calendar import Calendar

# Initialize with default credentials and a specific email
calendar = Calendar(email="user@example.com")

# Initialize with a specific timezone
calendar = Calendar(email="user@example.com", timezone="America/New_York")

# Initialize with service account impersonation
calendar = Calendar(
    email="user@example.com",
    impersonate_account="service-account@project-id.iam.gserviceaccount.com"
)
```

### Managing Calendars

#### Getting Calendars

```python
# Get all calendars
calendars = calendar.get_calendars()
for cal in calendars:
    print(f"Calendar: {cal['summary']}, ID: {cal['id']}")

# Get a specific calendar
cal = calendar.get_calendar(calendar_id="primary")
print(f"Calendar: {cal['summary']}, ID: {cal['id']}")
```

#### Creating and Updating Calendars

```python
# Create a new calendar
new_calendar = calendar.create_calendar(
    summary="My Calendar",
    description="A calendar for my events",
    timezone="America/New_York"
)
print(f"Created calendar with ID: {new_calendar['id']}")

# Update an existing calendar
updated_calendar = calendar.update_calendar(
    calendar_id="calendar_id_here",
    summary="Updated Calendar Name",
    description="Updated description",
    timezone="Europe/London"
)
print(f"Updated calendar: {updated_calendar['summary']}")

# Create or update a calendar (creates if it doesn't exist, updates if it does)
cal = calendar.create_or_update_calendar(
    summary="My Calendar",
    description="A calendar for my events",
    timezone="America/New_York",
    calendar_id="optional_calendar_id_here"
)
```

#### Deleting and Clearing Calendars

```python
# Delete a calendar
calendar.delete_calendar(calendar_id="calendar_id_here")

# Clear all events from a calendar
calendar.clear_calendar(calendar_id="calendar_id_here")
```

### Managing Events

#### Creating and Updating Events

```python
from datetime import datetime, timedelta
from gcp_pilot.calendar import Attendee, Color, SendUpdates

# Create a simple event
start_time = datetime.now() + timedelta(days=1)
end_time = start_time + timedelta(hours=1)

event = calendar.create_or_update_event(
    summary="Meeting with Team",
    start_at=start_time,
    end_at=end_time,
    calendar_id="primary"
)
print(f"Created event with ID: {event['id']}")

# Create an event with more details
attendees = [
    Attendee(email="colleague@example.com", name="Colleague"),
    Attendee(email="manager@example.com", name="Manager", required=True)
]

event = calendar.create_or_update_event(
    summary="Project Review",
    start_at=start_time,
    end_at=end_time,
    location="Conference Room A",
    description="Quarterly project review meeting",
    attendees=attendees,
    color=Color.BLUE,
    send_updates=SendUpdates.ALL,
    calendar_id="primary"
)

# Create a recurring event
event = calendar.create_or_update_event(
    summary="Weekly Team Meeting",
    start_at=start_time,
    end_at=end_time,
    recurrence_type="WEEKLY",
    recurrence_amount="4",  # Repeat for 4 weeks
    calendar_id="primary"
)

# Update an existing event
event = calendar.create_or_update_event(
    summary="Updated Meeting Title",
    start_at=start_time,
    end_at=end_time,
    event_id="event_id_here",
    calendar_id="primary"
)
```

#### Getting Events

```python
# Get all events from a calendar
events = calendar.get_events(calendar_id="primary")
for event in events:
    print(f"Event: {event['summary']}, Start: {event['start']}")

# Get events within a specific time range
from datetime import datetime, timedelta

start_date = datetime.now()
end_date = start_date + timedelta(days=7)

events = calendar.get_events(
    calendar_id="primary",
    starts_at=start_date,
    ends_at=end_date
)
for event in events:
    print(f"Event: {event['summary']}, Start: {event['start']}")

# Get a specific event
event = calendar.get_event(
    event_id="event_id_here",
    calendar_id="primary"
)
print(f"Event: {event['summary']}")

# Get instances of a recurring event
recurring_events = calendar.get_recurrent_events(
    event_id="recurring_event_id_here",
    calendar_id="primary"
)
for event in recurring_events:
    print(f"Event instance: {event['summary']}, Start: {event['start']}")
```

#### Deleting Events

```python
# Delete an event
calendar.delete_event(
    event_id="event_id_here",
    calendar_id="primary"
)
```

### Checking Availability

```python
from datetime import datetime, timedelta

start_time = datetime.now() + timedelta(days=1)
end_time = start_time + timedelta(hours=2)

# Check availability for the primary calendar
availability = calendar.check_availability(
    starts_at=start_time,
    ends_at=end_time
)
print(f"Available: {availability}")

# Check availability for multiple calendars
availability = calendar.check_availability(
    starts_at=start_time,
    ends_at=end_time,
    calendar_ids=["calendar_id_1", "calendar_id_2"],
    timezone="America/New_York"
)
print(f"Available: {availability}")
```

### Watching for Changes

#### Watching Calendars

```python
# Set up a webhook to be notified of calendar changes
watch_response = calendar.watch_calendars(
    hook_url="https://example.com/webhook",
    hook_token="my_secret_token"
)
print(f"Channel ID: {watch_response['id']}")
print(f"Resource ID: {watch_response['resourceId']}")

# Stop watching calendars
calendar.unwatch(
    uuid="channel_id_from_watch_response",
    resource_id="resource_id_from_watch_response"
)
```

#### Watching Events

```python
# Set up a webhook to be notified of event changes in a calendar
watch_response = calendar.watch_events(
    hook_url="https://example.com/webhook",
    calendar_id="primary",
    hook_token="my_secret_token"
)
print(f"Channel ID: {watch_response['id']}")
print(f"Resource ID: {watch_response['resourceId']}")

# Stop watching events
calendar.unwatch(
    uuid="channel_id_from_watch_response",
    resource_id="resource_id_from_watch_response"
)
```

## Enums and Helper Classes

### ResponseStatus

The `ResponseStatus` enum represents the response status of an attendee:

```python
from gcp_pilot.calendar import ResponseStatus

# Available values
ResponseStatus.NEEDS_ACTION  # The attendee has not responded to the invitation
ResponseStatus.DECLINED      # The attendee has declined the invitation
ResponseStatus.TENTATIVE     # The attendee has tentatively accepted the invitation
ResponseStatus.ACCEPTED      # The attendee has accepted the invitation
```

### Attendee

The `Attendee` class represents an event attendee:

```python
from gcp_pilot.calendar import Attendee, ResponseStatus

# Create an attendee
attendee = Attendee(
    email="user@example.com",
    name="User Name",
    required=True,  # Optional: if True, the attendee is required
    status=ResponseStatus.ACCEPTED  # Optional: the attendee's response status
)

# Convert to a dictionary for API calls
attendee_data = attendee.as_data()
```

### Color

The `Color` enum represents event colors:

```python
from gcp_pilot.calendar import Color

# Available colors
Color.BLUE
Color.GREEN
Color.PURPLE
Color.RED
Color.YELLOW
Color.ORANGE
Color.TURQUOISE
Color.GRAY
Color.BOLD_BLUE
Color.BOLD_GREEN
Color.BOLD_RED
```

### SendUpdates

The `SendUpdates` enum controls how updates are sent to attendees:

```python
from gcp_pilot.calendar import SendUpdates

# Available options
SendUpdates.ALL        # Send updates to all attendees
SendUpdates.EXTERNAL   # Send updates only to non-Google Calendar attendees
SendUpdates.NONE       # Don't send updates
```

## Error Handling

The Calendar class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    calendar.get_event(event_id="non_existent_event", calendar_id="primary")
except exceptions.NotFound:
    print("Event not found")

try:
    calendar.delete_calendar(calendar_id="non_existent_calendar")
except exceptions.NotFound:
    print("Calendar not found")
```