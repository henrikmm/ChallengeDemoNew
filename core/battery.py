from .goodwe_client import client


async def get_batery_usage():
    details = await client.get_collated_details()
    info = details["powerPlant"]["info"]
    return {
        "battery_level": info.get("soc"),
        "is_charging": info.get("batteryStatusStr") == "Charging",
        "generation_live": info.get("generationLive"),
        "house_load": info.get("houseLoad"),
    }


async def check_battery_energy_flow():
    details = await client.get_collated_details()
    info = details["powerPlant"]["info"]
    destinations = []
    if info.get("houseLoad", 0) > 0:
        destinations.append("Home")
    if info.get("gridLoad", 0) > 0:
        destinations.append("Grid")
    return {"energy_destinations": destinations}


def add_destination_to_battery_flow(destinations):
    return {"message": f"Started sending energy to: {', '.join(destinations)}"}


def remove_destination_from_battery_flow(destinations):
    return {"message": f"Stopped sending energy to: {', '.join(destinations)}"}
