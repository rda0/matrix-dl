#!/usr/bin/env python3
import argparse
import asyncio
import datetime as dt
import getpass
import os
import re
import sys
from typing import Optional

from mautrix.api import Path
from mautrix.client import Client
from mautrix.errors import MNotFound
from mautrix.types import RoomAlias, RoomID

DATE_FORMAT = "%Y-%m-%d"


class Colors:
    plat = sys.platform
    supported_platform = plat != "Pocket PC" and (plat != "win32" or "ANSICON" in os.environ)
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    if not supported_platform or not is_a_tty:
        HEADER = ""
        OKBLUE = ""
        OKGREEN = ""
        WARNING = ""
        FAIL = ""
        ENDC = ""
    else:
        HEADER = "\033[95m"
        OKBLUE = "\033[94m"
        OKGREEN = "\033[92m"
        WARNING = "\033[93m"
        FAIL = "\033[91m"
        ENDC = "\033[0m"

    force_disable = False

    @classmethod
    def disable(cls):
        cls.HEADER = ""
        cls.OKBLUE = ""
        cls.OKGREEN = ""
        cls.WARNING = ""
        cls.FAIL = ""
        cls.ENDC = ""

    @classmethod
    def enable(cls):
        if cls.force_disable:
            return
        cls.HEADER = "\033[95m"
        cls.OKBLUE = "\033[94m"
        cls.OKGREEN = "\033[92m"
        cls.WARNING = "\033[93m"
        cls.FAIL = "\033[91m"
        cls.ENDC = "\033[0m"


class MatrixLogGetter:
    def __init__(self):
        self.matrix_url = "https://matrix.org"
        self.username = None
        self.password = os.environ.get("MATRIX_PASSWORD")
        self.room = None
        self.start_date = "2017-01-01"
        self.end_date = None
        self.messages = []
        self.client: Optional[Client] = None

    async def run(self):
        self.start_date = dt.datetime.strptime(self.start_date, DATE_FORMAT).date()
        if self.end_date:
            self.end_date = dt.datetime.strptime(self.end_date, DATE_FORMAT).date()

        if not self.password:
            self.password = getpass.getpass()

        print(f"{self.username} connecting to {self.matrix_url}", file=sys.stderr)

        login_user = self.username
        if not login_user.startswith("@"):
            homeserver = re.sub(r"^https?://", "", self.matrix_url).rstrip("/")
            login_user = f"@{login_user}:{homeserver}"

        self.client = Client(mxid=login_user, base_url=self.matrix_url)

        try:
            await self.client.login(password=self.password)

            room_id = await self.resolve_room(self.room)
            if not room_id:
                print(f"Could not find room {self.room}", file=sys.stderr)
                sys.exit(1)

            await self.download(room_id)
        finally:
            try:
                self.print_messages()
            finally:
                session = getattr(getattr(self.client, "api", None), "session", None)
                if session is not None and not session.closed:
                    await session.close()

    async def resolve_room(self, room: str) -> Optional[str]:
        room = room.strip()

        if room.startswith("!"):
            return room

        if room.startswith("#"):
            try:
                resp = await self.client.resolve_room_alias(RoomAlias(room))
                return str(resp.room_id)
            except MNotFound:
                return None

        homeserver = re.sub(r"^https?://", "", self.matrix_url).rstrip("/")
        guessed_alias = f"#{room}:{homeserver}"
        try:
            resp = await self.client.resolve_room_alias(RoomAlias(guessed_alias))
            return str(resp.room_id)
        except MNotFound:
            return None

    async def download(self, room_id: str):
        token = None

        while True:
            query = {
                "dir": "b",
                "limit": 1000,
            }
            if token:
                query["from"] = token

            res = await self.client.api.request(
                "GET",
                Path.v3.rooms[RoomID(room_id)].messages,
                query_params=query,
            )

            chunk = res.get("chunk", [])
            token = res.get("end")

            if not chunk:
                return

            for event in chunk:
                if event.get("type") == "m.room.message":
                    self.messages.insert(0, event)

            oldest = self.messages[0] if self.messages else None
            if oldest:
                ts = oldest["origin_server_ts"] / 1000
                date = dt.datetime.fromtimestamp(ts).date()
                print(f"Getting messages before {date}", file=sys.stderr)
                if date < self.start_date:
                    return

            if not token:
                return

    def print_messages(self):
        print(f"Got {len(self.messages)} message events", file=sys.stderr)

        for message in self.messages:
            ts = message["origin_server_ts"] / 1000
            timestamp = dt.datetime.fromtimestamp(ts)
            date = timestamp.date()

            if date < self.start_date or (self.end_date and date > self.end_date):
                continue

            day = timestamp.strftime("%Y-%m-%d")
            time = timestamp.strftime("%H:%M:%S")

            sender = message.get("sender", "")
            user = sender[1:] if sender.startswith("@") else sender
            user = user.split(":")[0]

            content = message.get("content", {})
            msgtype = content.get("msgtype")
            body = content.get("body", "")

            if msgtype == "m.text":
                text = body
            elif msgtype == "m.notice":
                text = f"[notice] {body}"
            elif msgtype == "m.emote":
                text = f"* {user} {body}"
            elif msgtype == "m.image":
                text = f"[image] {body}"
            elif msgtype == "m.file":
                text = f"[file] {body}"
            elif msgtype == "m.audio":
                text = f"[audio] {body}"
            elif msgtype == "m.video":
                text = f"[video] {body}"
            else:
                text = body or f"[{msgtype or 'unknown message'}]"

            print(f"{day} {time} - {user}: {text}")


def main():
    getter = MatrixLogGetter()

    parser = argparse.ArgumentParser(
        description="Download backlogs from Matrix as raw text"
    )
    parser.add_argument(
        "username",
        type=str,
        help="Matrix username, either full MXID (@user:server) or localpart (user)",
    )
    parser.add_argument(
        "room",
        type=str,
        help="Room ID (!id:server), full alias (#alias:server), or bare alias name",
    )
    parser.add_argument(
        "--password",
        type=str,
        default=None,
        help="Will be asked later if not provided via this option or MATRIX_PASSWORD",
    )
    parser.add_argument(
        "--matrix-url",
        default=getter.matrix_url,
        help="URL of your homeserver (without trailing slash) [default: %(default)s]",
    )
    date_format_str = f"(format {DATE_FORMAT}) [default: %(default)s]"
    parser.add_argument(
        "--start-date",
        default="2017-01-01",
        help=f"Starting day to consider {date_format_str}",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help=f"Last day to consider (format {DATE_FORMAT})",
    )

    parser.parse_args(namespace=getter)
    asyncio.run(getter.run())


if __name__ == "__main__":
    main()
