import json
from collections.abc import Generator
from dataclasses import dataclass, field

import requests

from gcp_pilot import exceptions
from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI, ResourceType


class Text:
    @classmethod
    def build_mention(cls, member_id: str = "all") -> str:
        return f"<users/{member_id}>"

    @classmethod
    def build_link(cls, url: str, text: str) -> str:
        return f"<{url}|{text}>"

    @classmethod
    def format_color(cls, hex_color: str, text: str) -> str:
        return f'<font color="#{hex_color}">{text}</font>'


class Widget(dict):
    _key: str | None = None

    def as_data(self):
        if self._key:
            return {self._key: dict(self)}

        return dict(self)


class ButtonWidget(Widget):
    def __init__(self, url, text: str | None = None, image_url: str | None = None, icon: str | None = None):
        super().__init__()
        if text:
            self._key = "textButton"
            self["text"] = text
        elif image_url:
            self._key = "imageButton"
            self["iconUrl"] = image_url
        elif icon:
            self._key = "imageButton"
            self["icon"] = icon
        else:
            raise exceptions.UnsupportedFormatException("A button must have a text, image or icon")

        self["onClick"] = {
            "openLink": {
                "url": url,
            },
        }


class ButtonGroupWidget(Widget):
    _key = "buttons"

    def __init__(self, buttons):
        data = dict(
            buttons=buttons,
        )
        super().__init__(data)

    def as_data(self):
        return {self._key: [button.as_data() for button in self["buttons"]]}


class OnClickWidget(Widget):
    _key = "onClick"

    def __init__(self, url):
        data = dict(openLink=dict(url=url))
        super().__init__(data)


class KeyValueWidget(Widget):
    _key = "keyValue"

    def __init__(
        self,
        content: str,
        top: str | None = None,
        bottom: str | None = None,
        break_lines: bool = True,
        on_click: OnClickWidget | None = None,
        icon: str | None = None,
        button: ButtonWidget | None = None,
    ):
        data = dict(
            content=content,
            contentMultiline="true" if break_lines else "false",
        )
        if top:
            data["topLabel"] = top
        if bottom:
            data["bottomLabel"] = bottom
        if on_click:
            data["onClick"] = on_click
        if icon:
            data["icon"] = icon
        if button:
            data["button"] = button

        super().__init__(data)


class TextWidget(Widget):
    _key = "textParagraph"

    def __init__(self, text: str):
        super().__init__(text=text)


class ImageWidget(Widget):
    _key = "image"

    def __init__(self, image_url: str, on_click: OnClickWidget | None = None):
        data = dict(imageUrl=image_url)
        if on_click:
            data.update(on_click.as_data())
        super().__init__(data)


@dataclass
class Section:
    header: str | None = None
    widgets: list[Widget] = field(default_factory=list)

    def add_header(self, text: str):
        self.header = text

    def add_text(
        self,
        content: str,
        title: str = "",
        footer: str = "",
        click_url: str | None = None,
        icon: str | None = None,
        button: str | None = None,
    ):
        widget = KeyValueWidget(
            top=title,
            content=content,
            break_lines=True,
            bottom=footer,
            on_click=OnClickWidget(url=click_url) if click_url else None,
            icon=icon,
            button=button,
        )
        self.widgets.append(widget)

    def add_paragraph(self, text: str):
        self.widgets.append(TextWidget(text=text))

    def add_button(
        self,
        url,
        text: str | None = None,
        image_url: str | None = None,
        icon: str | None = None,
        append: bool = True,
    ):
        button = ButtonWidget(url=url, text=text, image_url=image_url, icon=icon)
        if append and self.widgets and "buttons" in self.widgets[-1]:
            self.widgets[-1]["buttons"].append(button)
        else:
            self.widgets.append(ButtonGroupWidget(buttons=[button]))

    def add_image(self, image_url: str, click_url: str | None = None):
        widget = ImageWidget(
            image_url=image_url,
            on_click=OnClickWidget(url=click_url) if click_url else None,
        )
        self.widgets.append(widget)

    def as_data(self):
        data = {
            "widgets": [widget.as_data() for widget in self.widgets],
        }
        if self.header:
            data["header"] = self.header
        return data

    def __bool__(self):
        return self.header is not None or bool(self.widgets)


@dataclass
class Card:
    header: Widget | None = None
    sections: list[Section] = field(default_factory=list)

    def add_header(self, title: str, subtitle: str = "", image_url: str | None = None, style: str = "IMAGE"):
        self.header = Widget(
            title=title,
            subtitle=subtitle,
            imageUrl=image_url,
            imageStyle=style,
        )

    def add_section(self, section: Section):
        if bool(section):
            self.sections.append(section)

    def as_data(self) -> dict:
        data = {"sections": [section.as_data() for section in self.sections]}
        if self.header:
            data["header"] = self.header.as_data()
        return data


class ChatsHook:
    def __init__(self, hook_url: str):
        self.hook_url = hook_url

    def _post(self, body: dict, thread_key: str | None = None) -> dict:
        url = self.hook_url
        if thread_key:
            url = f"{url}&threadKey={thread_key}"

        response = requests.post(
            url=url,
            headers={"Content-Type": "application/json; charset=UTF-8"},
            data=json.dumps(body),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def send_text(self, text: str, thread_key: str | None = None) -> dict:
        body = {"text": text}
        return self._post(body=body, thread_key=thread_key)

    def send_card(self, card: Card, additional_text: str | None = None, thread_key: str | None = None) -> dict:
        body = {
            "cards": [card.as_data()],
        }

        if additional_text:
            body["text"] = additional_text

        return self._post(body=body, thread_key=thread_key)


class ChatsBot(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = ["https://www.googleapis.com/auth/chat.bot"]

    def __init__(self, **kwargs):
        super().__init__(
            serviceName="chat",
            version="v1",
            cache_discovery=False,
            **kwargs,
        )

    def _room_path(self, room_id: str) -> str:
        prefix = "spaces/"
        room_path = f"{prefix}{room_id}" if not room_id.startswith(prefix) else room_id
        return room_path

    def _member_path(self, room_id: str, member_id: str) -> str:
        room_path = self._room_path(room_id=room_id)

        prefix = "members/"
        member_path = f"{prefix}{member_id}" if not member_id.startswith(prefix) else member_id

        return f"{room_path}/{member_path}"

    def get_room(self, room_id: str) -> ResourceType:
        return self._execute(
            method=self.client.spaces().get,
            name=self._room_path(room_id=room_id),
        )

    def get_rooms(self) -> Generator[ResourceType, None, None]:
        yield from self._paginate(
            method=self.client.spaces().list,
            result_key="spaces",
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
            result_key="memberships",
            params={"parent": self._room_path(room_id=room_id)},
        )

    def send_text(self, room_id: str, text: str) -> ResourceType:
        body = {"text": text}

        return self._execute(
            method=self.client.spaces().messages().create,
            parent=self._room_path(room_id=room_id),
            body=body,
        )

    def send_card(self, room_id: str, card: Card, additional_text: str | None = None) -> ResourceType:
        body = {
            "cards": [card.as_data()],
        }

        if additional_text:
            body["text"] = additional_text

        return self._execute(
            method=self.client.spaces().messages().create,
            parent=self._room_path(room_id=room_id),
            body=body,
        )


__all__ = (
    "Text",
    "Section",
    "Card",
    "ChatsBot",
    "ChatsHook",
)
