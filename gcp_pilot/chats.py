import json

import requests

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI, DiscoveryMixin


class Text:
    @classmethod
    def build_mention(cls, member_id='all'):
        return f"<users/{member_id}>"

    @classmethod
    def build_link(cls, url, text):
        return f"<{url}|{text}>"


class Section:
    def __init__(self):
        self.header = None
        self.widgets = []

    def add_header(self, text):
        self.header = text

    def add_text(self, content, title='', footer='', click_url=None, icon=None, button=None):
        section = self._build_text_section(
            title=title,
            content=content,
            footer=footer,
            click_url=click_url,
            icon=icon,
            button=button,
        )
        self.widgets.append({'keyValue': section})

    def add_paragraph(self, text):
        section = self._build_paragraph(text=text)
        self.widgets.append({'textParagraph': section})

    def add_buttons(self, buttons):
        self.widgets.append({'buttons': buttons})

    def add_image(self, image_url, click_url=None):
        section = self._build_image(
            image_url=image_url,
            click_url=click_url,
        )
        self.widgets.append({'image': section})

    @classmethod
    def _build_paragraph(cls, text):
        return {'text': text}

    @classmethod
    def _build_image(cls, image_url, click_url=None):
        return {
            "imageUrl": image_url,
            "onClick": {"openLink": {"url": click_url or image_url}}
        }

    @classmethod
    def _build_text_section(
            cls,
            content,
            title='',
            footer='',
            click_url=None,
            icon=None,
            button=None,
    ):
        section = {
            "topLabel": title,
            "content": content,
            "contentMultiline": "true",
            "bottomLabel": footer,
        }

        if click_url:
            section["onClick"] = {
                "openLink": {
                    "url": click_url,
                }
            }

        if icon:
            section['icon'] = icon

        if button:
            section['button'] = button

        return section

    @classmethod
    def format_button(cls, url, text=None, image_url=None, icon=None):
        if text:
            button = {
                "textButton": {
                    "text": text,
                }
            }
        elif image_url:
            button = {
                "imageButton": {
                    "iconUrl": image_url,
                }
            }
        elif icon:
            button = {
                "imageButton": {
                    "icon": icon,
                }
            }
        else:
            raise exceptions.UnsupportedFormatException("A button must have a text, image or icon")

        button["onClick"] = {
            "openLink": {
                "url": url,
            }
        }
        return button

    @classmethod
    def format_color(cls, hex_color, text):
        return f"<font color=\"#{hex_color}\">{text}</font>"

    def as_data(self):
        data = {
            'widgets': self.widgets,
        }
        if self.header:
            data['header'] = self.header
        return data


class Card:
    def __init__(self):
        self.header = None
        self.sections = []

    def add_header(self, title, subtitle='', image_url=None, style='IMAGE'):
        self.header = self._build_header(
            title=title,
            subtitle=subtitle,
            image_url=image_url,
            style=style,
        )

    def add_section(self, section):
        self.sections.append(section)

    @classmethod
    def _build_header(cls, title, subtitle='', image_url=None, style='IMAGE'):
        return {
            "title": title,
            "subtitle": subtitle,
            "imageUrl": image_url,
            "imageStyle": style
        }

    def as_data(self):
        data = {'sections': [section.as_data() for section in self.sections]}
        if self.header:
            data['header'] = self.header
        return data


class ChatsHook:
    def __init__(self, hook_url):
        self.hook_url = hook_url

    def _post(self, body):
        response = requests.post(
            url=self.hook_url,
            headers={'Content-Type': 'application/json; charset=UTF-8'},
            data=json.dumps(body),
        )
        response.raise_for_status()
        return response.json()

    def send_text(self, text):
        body = {'text': text}
        return self._post(body=body)

    def send_card(self, card, additional_text=None):
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

    def _room_path(self, room_id: str):
        prefix = 'spaces/'
        if not room_id.startswith(prefix):
            room_path = f'{prefix}{room_id}'
        else:
            room_path = room_id
        return room_path

    def _member_path(self, room_id: str, member_id: str):
        room_path = self._room_path(room_id=room_id)

        prefix = 'members/'
        if not member_id.startswith(prefix):
            member_path = f'{prefix}{member_id}'
        else:
            member_path = member_id

        return f'{room_path}/{member_path}'

    def get_room(self, room_id: str):
        return self._execute(
            method=self.client.spaces().get,
            name=self._room_path(room_id=room_id),
        )

    def get_rooms(self):
        yield from self._paginate(
            method=self.client.spaces().list,
            result_key='spaces',
        )

    def get_member(self, room_id: str, member_id: str):
        name = self._member_path(room_id=room_id, member_id=member_id)
        return self._execute(
            method=self.client.spaces().members().get,
            name=name,
        )

    def get_members(self, room_id: str):
        yield from self._paginate(
            method=self.client.spaces().members().list,
            result_key='memberships',
            params={'parent': self._room_path(room_id=room_id)}
        )

    def send_text(self, room_id: str, text: str):
        body = {'text': text}

        return self._execute(
            method=self.client.spaces().messages().create,
            parent=self._room_path(room_id=room_id),
            body=body,
        )

    def send_card(self, room_id: str, card: Card, additional_text: str = None):
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
