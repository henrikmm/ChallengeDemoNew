import os
from datetime import datetime
from typing import Optional
import aiohttp
from sems_portal_api import (
    login_to_sems,
    login_response_to_token,
    get_station_ids,
    get_collated_plant_details,
    get_plant_power_chart,
    set_region,
)


class GoodWeClient:
    """Lightweight wrapper around the sems_portal_api library.

    Handles authentication, token management and provides helper
    methods for fetching plant details and power charts.
    """

    def __init__(self) -> None:
        self.username = os.getenv("SEMS_USERNAME")
        self.password = os.getenv("SEMS_PASSWORD")
        self.station_id = os.getenv("SEMS_STATION_ID")
        region = os.getenv("SEMS_REGION")
        if region:
            set_region(region)
        self.session: Optional[aiohttp.ClientSession] = None
        self.token: Optional[str] = None

    async def _ensure_session(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession()
        if self.token is None:
            login_resp = await login_to_sems(self.session, self.username, self.password)
            self.token = login_response_to_token(login_resp)
        if not self.station_id:
            ids = await get_station_ids(self.session, self.token)
            if ids:
                self.station_id = ids[0]

    async def get_collated_details(self):
        await self._ensure_session()
        return await get_collated_plant_details(self.session, self.station_id, self.token)

    async def get_power_chart(self, date: datetime):
        await self._ensure_session()
        return await get_plant_power_chart(self.session, self.station_id, self.token, date)

    async def close(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None
            self.token = None


client = GoodWeClient()
