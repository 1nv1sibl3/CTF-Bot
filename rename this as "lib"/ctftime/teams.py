from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

from config import CTFTIME_URL, USER_AGENT
from lib.ctftime.types import CTFTimeParticipatedEvent, CTFTimeTeam


async def get_ctftime_team_info(team_id: int) -> Optional[CTFTimeTeam]:
    # Request the team data from CTFtime.
    async with aiohttp.request(
        method="get",
        url=f"{CTFTIME_URL}/team/{team_id}",
        headers={"User-Agent": USER_AGENT()},
    ) as response:
        if response.status != 200:
            return None

        parser = BeautifulSoup(await response.text(), "html.parser")

    # Select the paragraphs containing overall rating place, points and eventually the
    # country place.
    if not (p := parser.select(".active p")):
        return None

    rank, points = [b_tag.text.strip() for b_tag in p.pop(0).find_all("b")]
    country_code, country_rank = None, None
    if p:
        a_tag = p.pop().find("a")
        country_code = a_tag["href"].split("/").pop()
        country_rank = int(a_tag.text.strip())

    # Get the results of the current year.
    table_rows = []
    for table in parser.select(".active .table-striped"):
        if (header := table.select("th")) and header.pop(0).text == "Place":
            table_rows = table.select("tr:has(td)")
            break

    result = CTFTimeTeam(
        overall_points=float(points),
        overall_rating_place=int(rank),
        country_place=country_rank,
        country_code=country_code,
        participated_in={},
    )
    for row in table_rows:
        # Select the table cells.
        event = row.select_one("td:not(.place_ico):has(a)").find("a")
        event_id = int(event["href"].split("/").pop())
        event_name = event.text.strip()


        cells = [td.text.strip() for td in row.select("td:not(.place_ico):not(:has(a))")]

        # If the third column is missing (due to rate not being determined), set a default.
        if len(cells) == 2:
            # Assume that when only two cells are returned, rating_points is missing.
            cells.append("0.000")  # or simply "0.000" if you want to remove the asterisk later

        if len(cells) != 3:
            print(f"Skipping row, unexpected number of cells: {cells}")
            continue

        place, ctf_points, rating_points = cells
        

        # Assemble the scoreboard entry.
        result.participated_in[event_id] = CTFTimeParticipatedEvent(
            place=int(place),
            event_name=event_name,
            event_id=event_id,
            ctf_points=float(ctf_points),
            rating_points=float(rating_points),
        )
    print(result)
    return result