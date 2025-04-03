# Google Chats

Google Chats is a messaging platform built for teams. The `chats` module in gcp-pilot provides classes for interacting with Google Chats, both as a webhook and as a bot.

## Installation

To use the Google Chats functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

The `chats` module provides two main ways to interact with Google Chats:

1. `ChatsHook`: For sending messages to Google Chat via webhooks
2. `ChatsBot`: For interacting with Google Chat as a bot

### Using ChatsHook

The `ChatsHook` class allows you to send messages to Google Chat via webhooks. This is useful for sending notifications from your application to a Google Chat room.

```python
from gcp_pilot.chats import ChatsHook, Card, Section, Text

# Initialize with the webhook URL
hook = ChatsHook(hook_url="https://chat.googleapis.com/v1/spaces/SPACE_ID/messages?key=KEY&token=TOKEN")

# Send a simple text message
hook.send_text("Hello, world!")

# Send a message to a specific thread
hook.send_text("Hello, thread!", thread_key="thread_key_here")

# Create a card with a section
card = Card()
section = Section()
section.add_header("Card Header")
section.add_paragraph("This is a paragraph of text.")
section.add_button(url="https://example.com", text="Visit Example")
card.add_section(section)

# Send the card
hook.send_card(card)

# Send the card with additional text
hook.send_card(card, additional_text="Check out this card!")

# Send the card to a specific thread
hook.send_card(card, thread_key="thread_key_here")
```

### Using ChatsBot

The `ChatsBot` class allows you to interact with Google Chat as a bot. This requires a service account with the appropriate permissions.

```python
from gcp_pilot.chats import ChatsBot, Card, Section

# Initialize with default credentials
bot = ChatsBot()

# Initialize with service account impersonation
bot = ChatsBot(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Get information about a room
room = bot.get_room(room_id="room_id_here")
print(f"Room name: {room['displayName']}")

# List all rooms the bot is a member of
rooms = bot.get_rooms()
for room in rooms:
    print(f"Room: {room['displayName']}")

# Get information about a member in a room
member = bot.get_member(room_id="room_id_here", member_id="member_id_here")
print(f"Member name: {member['displayName']}")

# List all members in a room
members = bot.get_members(room_id="room_id_here")
for member in members:
    print(f"Member: {member['displayName']}")

# Send a text message to a room
bot.send_text(room_id="room_id_here", text="Hello from the bot!")

# Create a card with a section
card = Card()
section = Section()
section.add_header("Bot Card")
section.add_paragraph("This is a message from the bot.")
section.add_button(url="https://example.com", text="Visit Example")
card.add_section(section)

# Send the card to a room
bot.send_card(room_id="room_id_here", card=card)

# Send the card with additional text
bot.send_card(room_id="room_id_here", card=card, additional_text="Check out this card!")
```

## Building Rich Messages

The `chats` module provides several classes for building rich messages with cards, sections, and widgets.

### Text Utilities

The `Text` class provides static methods for formatting text:

```python
from gcp_pilot.chats import Text

# Create a mention
mention_all = Text.build_mention()  # Mentions @all
mention_user = Text.build_mention(member_id="user_id_here")  # Mentions a specific user

# Create a link
link = Text.build_link(url="https://example.com", text="Visit Example")

# Format text with color
colored_text = Text.format_color(hex_color="#ff0000", text="This text is red")
```

### Creating Cards

A card is the main container for rich content in Google Chat:

```python
from gcp_pilot.chats import Card, Section

# Create a card
card = Card()

# Add a header to the card
card.add_header(
    title="Card Title",
    subtitle="Card Subtitle",
    image_url="https://example.com/image.png",
    style="IMAGE"  # or "AVATAR"
)

# Create a section
section = Section()

# Add the section to the card
card.add_section(section)

# Get the card data for API calls
card_data = card.as_data()
```

### Creating Sections

Sections are containers for widgets within a card:

```python
from gcp_pilot.chats import Section, ButtonWidget, OnClickWidget

# Create a section
section = Section()

# Add a header to the section
section.add_header("Section Header")

# Add a paragraph of text
section.add_paragraph("This is a paragraph of text.")

# Add text with more formatting options
section.add_text(
    content="Main content",
    title="Title",
    footer="Footer",
    click_url="https://example.com",
    icon="STAR",
    button="Visit"
)

# Add a button
section.add_button(
    url="https://example.com",
    text="Visit Example",
    image_url="https://example.com/button.png",
    icon="STAR"
)

# Add an image
section.add_image(
    image_url="https://example.com/image.png",
    click_url="https://example.com"
)

# Get the section data for API calls
section_data = section.as_data()
```

### Creating Widgets

Widgets are the individual UI elements within a section:

```python
from gcp_pilot.chats import (
    ButtonWidget, ButtonGroupWidget, OnClickWidget,
    KeyValueWidget, TextWidget, ImageWidget
)

# Create a button widget
button = ButtonWidget(
    url="https://example.com",
    text="Visit Example",
    image_url="https://example.com/button.png",
    icon="STAR"
)

# Create a button group widget
button_group = ButtonGroupWidget(
    buttons=[
        ButtonWidget(url="https://example.com", text="Button 1"),
        ButtonWidget(url="https://example.org", text="Button 2")
    ]
)

# Create an on-click widget
on_click = OnClickWidget(url="https://example.com")

# Create a key-value widget
key_value = KeyValueWidget(
    content="Content",
    top="Top Label",
    bottom="Bottom Label",
    break_lines=True,
    on_click=on_click,
    icon="STAR",
    button=button
)

# Create a text widget
text = TextWidget(text="This is a text widget")

# Create an image widget
image = ImageWidget(
    image_url="https://example.com/image.png",
    on_click=on_click
)

# Get widget data for API calls
button_data = button.as_data()
```

## Error Handling

The Chats classes handle common errors and convert them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    bot.get_room(room_id="non_existent_room")
except exceptions.NotFound:
    print("Room not found")

try:
    hook.send_text("Message")
except exceptions.HttpError as e:
    print(f"Error sending message: {e}")
```