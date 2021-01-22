import json
from dataclasses import field, dataclass
from typing import List, Dict, Generator

import requests

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI, DiscoveryMixin, ResourceType


class Text:
    @classmethod
    def build_mention(cls, member_id: str = 'all') -> str:
        return f"<users/{member_id}>"

    @classmethod
    def build_link(cls, url: str, text: str) -> str:
        return f"<{url}|{text}>"

    @classmethod
    def format_color(cls, hex_color: str, text: str) -> str:
        return f"<font color=\"#{hex_color}\">{text}</font>"


class Widget(dict):
    _key = None

    def as_data(self):
        if self._key:
            return {
                self._key: dict(self)
            }
        else:
            return dict(self)


class KeyValueWidget(Widget):
    _key = 'keyValue'


class TextWidget(Widget):
    _key = 'textParagraph'


class ImageWidget(Widget):
    _key = 'image'


class ButtonWidget(Widget):
    def __init__(self, url, text=None, image_url=None, icon=None):
        super().__init__()
        if text:
            self._key = 'textButton'
            self['text'] = text
        elif image_url:
            self._key = "imageButton"
            self['iconUrl'] = image_url
        elif icon:
            self._key = 'imageButton'
            self['icon'] = icon
        else:
            raise exceptions.UnsupportedFormatException("A button must have a text, image or icon")

        self["onClick"] = {
            "openLink": {
                "url": url,
            }
        }


@dataclass
class Section:
    header: str = None
    widgets: List[Widget] = field(default_factory=list)

    def add_header(self, text: str):
        self.header = text

    def add_text(
            self,
            content: str,
            title: str = '',
            footer: str = '',
            click_url: str = None,
            icon: str = None,
            button: str = None,
    ):
        widget = KeyValueWidget(
            topLabel=title,
            content=content,
            contentMultiline="true",
            bottomLabel=footer,
        )

        if click_url:
            widget["onClick"] = {
                "openLink": {
                    "url": click_url,
                }
            }

        if icon:
            widget['icon'] = icon

        if button:
            widget['button'] = button

        self.widgets.append(KeyValueWidget(keyValue=widget))

    def add_paragraph(self, text: str):
        self.widgets.append(TextWidget(text=text))

    def add_buttons(self, buttons: List[str]):
        self.widgets.append(Widget(buttons=buttons))

    def add_image(self, image_url: str, click_url: str = None):
        widget = ImageWidget(
            imageUrl=image_url,
            onClick={"openLink": {"url": click_url or image_url}},
        )
        self.widgets.append(widget)

    def as_data(self):
        data = {
            'widgets': [widget.as_data() for widget in self.widgets],
        }
        if self.header:
            data['header'] = self.header
        return data

    def __bool__(self):
        return self.header is not None or self.widgets


@dataclass
class Card:
    header: Widget = None
    sections: List[Section] = field(default_factory=list)

    def add_header(self, title: str, subtitle: str = '', image_url: str = None, style: str = 'IMAGE'):
        self.header = Widget(
            title=title,
            subtitle=subtitle,
            imageUrl=image_url,
            imageStyle=style,
        )

    def add_section(self, section: Section):
        if bool(section):
            self.sections.append(section)

    def as_data(self) -> Dict:
        data = {'sections': [section.as_data() for section in self.sections]}
        if self.header:
            data['header'] = self.header.as_data()
        return data


class ChatsHook:
    def __init__(self, hook_url: str):
        self.hook_url = hook_url

    def _post(self, body: Dict) -> Dict:
        response = requests.post(
            url=self.hook_url,
            headers={'Content-Type': 'application/json; charset=UTF-8'},
            data=json.dumps(body),
        )
        response.raise_for_status()
        return response.json()

    def send_text(self, text: str) -> Dict:
        body = {'text': text}
        return self._post(body=body)

    def send_card(self, card: Card, additional_text: str = None) -> Dict:
        body = {
            'cards': [card.as_data()],
        }

        if additional_text:
            body['text'] = additional_text

        return self._post(body=body)


class ChatsBot(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = ['https://www.googleapis.com/auth/chat.bot']

    def __init__(self, **kwargs):
        super().__init__(
            serviceName='chat',
            version='v1',
            cache_discovery=False,
            **kwargs,
        )

    def _room_path(self, room_id: str) -> str:
        prefix = 'spaces/'
        if not room_id.startswith(prefix):
            room_path = f'{prefix}{room_id}'
        else:
            room_path = room_id
        return room_path

    def _member_path(self, room_id: str, member_id: str) -> str:
        room_path = self._room_path(room_id=room_id)

        prefix = 'members/'
        if not member_id.startswith(prefix):
            member_path = f'{prefix}{member_id}'
        else:
            member_path = member_id

        return f'{room_path}/{member_path}'

    def get_room(self, room_id: str) -> ResourceType:
        return self._execute(
            method=self.client.spaces().get,
            name=self._room_path(room_id=room_id),
        )

    def get_rooms(self) -> Generator[ResourceType, None, None]:
        yield from self._paginate(
            method=self.client.spaces().list,
            result_key='spaces',
        )

    def get_member(self, room_id: str, member_id: str) -> ResourceType:
        name = self._member_path(room_id=room_id, member_id=member_id)
        return self._execute(
            method=self.client.spaces().members().get,
            name=name,
        )

    def get_members(self, room_id: str) -> Generator[ResourceType, None, None]:
        yield from self._paginate(
            method=self.client.spaces().members().list,
            result_key='memberships',
            params={'parent': self._room_path(room_id=room_id)}
        )

    def send_text(self, room_id: str, text: str) -> ResourceType:
        body = {'text': text}

        return self._execute(
            method=self.client.spaces().messages().create,
            parent=self._room_path(room_id=room_id),
            body=body,
        )

    def send_card(self, room_id: str, card: Card, additional_text: str = None) -> ResourceType:
        body = {
            'cards': [card.as_data()],
        }

        if additional_text:
            body['text'] = additional_text

        return self._execute(
            method=self.client.spaces().messages().create,
            parent=self._room_path(room_id=room_id),
            body=body,
        )
