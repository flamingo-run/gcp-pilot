# More Information: <https://googleapis.dev/python/dns/latest/index.html>
import time
from enum import Enum
from typing import Generator, List

from google.api_core.exceptions import BadRequest, Conflict
from google.cloud import dns

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI


class RecordType(Enum):
    A = "A"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"

    @classmethod
    def prepare(cls, record_type: "RecordType", record: str):
        if record_type == cls.CNAME:
            return cls.build_dns_name(name=record)
        # TODO Parse MX, A records
        return record

    @classmethod
    def build_dns_name(cls, name: str) -> str:
        if name and not name.endswith("."):
            dns_name = f"{name}."
        else:
            dns_name = name
        return dns_name


class CloudDNS(GoogleCloudPilotAPI):
    _client_class = dns.Client

    def _get_client_extra_kwargs(self):
        return {
            "project": self.project_id,
        }

    def list_zones(self) -> Generator[dns.ManagedZone, None, None]:
        yield from self.client.list_zones()

    def _build_zone(self, name: str, dns_name: str, description: str = None) -> dns.ManagedZone:
        return self.client.zone(
            name=name,
            dns_name=RecordType.build_dns_name(name=dns_name),
            description=description,
        )

    def create_zone(
        self,
        name: str,
        dns_name: str,
        description: str = None,
        exists_ok: bool = True,
    ) -> dns.ManagedZone:
        zone = self._build_zone(name=name, dns_name=dns_name, description=description)
        if not zone.exists():
            return zone.create()
        if not exists_ok:
            raise exceptions.AlreadyExists()
        return zone

    def delete_zone(self, name: str, dns_name: str, exists_ok: bool = True) -> None:
        zone = self._build_zone(name=name, dns_name=dns_name)
        if not zone.exists and not exists_ok:
            raise exceptions.NotFound()
        return zone.delete()

    def list_records(self, zone_name: str, zone_dns: str) -> Generator[dns.ResourceRecordSet, None, None]:
        zone = self._build_zone(name=zone_name, dns_name=zone_dns)

        yield from zone.list_resource_record_sets()  # TODO Why paging does not work like docs?

    def _change_record(
        self,
        action: str,
        zone_name: str,
        zone_dns: str,
        name: str,
        record_type: RecordType,
        record_data: List[str] = None,
        ttl: int = 60 * 60,
        wait: bool = True,
    ) -> dns.ResourceRecordSet:
        zone = self._build_zone(name=zone_name, dns_name=zone_dns)

        parsed_record_data = (
            [RecordType.prepare(record_type=record_type, record=record) for record in record_data]
            if record_data
            else []
        )

        record_set = zone.resource_record_set(
            name=RecordType.build_dns_name(name=name),
            record_type=record_type.name,
            ttl=ttl,
            rrdatas=parsed_record_data,
        )
        changes = zone.changes()

        if action == "add":
            changes.add_record_set(record_set)
        elif action == "delete":
            changes.delete_record_set(record_set)
        else:
            raise exceptions.ValidationError(f"Action {action} is not support for record sets")

        try:
            changes.create()
        except BadRequest as e:
            if "is only permitted to have one record" in e.message:
                raise exceptions.AlreadyExists(e.message) from e
            raise
        except Conflict as e:
            raise exceptions.AlreadyExists(e.message) from e

        if wait:
            while changes.status != "done":
                print("Waiting for changes to complete")
                time.sleep(60)
                changes.reload()
        return record_set

    def add_record(  # pylint: disable=inconsistent-return-statements
        self,
        zone_name: str,
        zone_dns: str,
        name: str,
        record_type: RecordType,
        record_data: List[str],
        ttl: int = 5 * 60,
        wait: bool = True,
        exists_ok: bool = True,
    ) -> dns.ResourceRecordSet:
        try:
            return self._change_record(
                action="add",
                zone_name=zone_name,
                zone_dns=zone_dns,
                name=name,
                record_type=record_type,
                record_data=record_data,
                ttl=ttl,
                wait=wait,
            )
        except exceptions.AlreadyExists:
            if not exists_ok:
                raise
            # return  # TODO Fetch current record to return

    def delete_record(
        self,
        zone_name: str,
        zone_dns: str,
        name: str,
        record_type: RecordType,
        wait: bool = True,
    ) -> dns.ResourceRecordSet:
        return self._change_record(
            action="delete",
            zone_name=zone_name,
            zone_dns=zone_dns,
            name=name,
            record_type=record_type,
            wait=wait,
        )


__all__ = (
    "CloudDNS",
    "RecordType",
)
