from typing import Optional

import aiohttp
import discord
from discord import app_commands


class Search(app_commands.Command):
    def __init__(self) -> None:
        super().__init__(
            name="search",
            description="Search for a topic in the CTF write-ups index.",
            callback=self.cmd_callback,  # type: ignore
        )

async def cmd_callback(
    self, interaction: discord.Interaction, query: str, limit: Optional[int] = 3
) -> None:
    """Search for a topic in the CTF write-ups index.

    Args:
        interaction: The interaction that triggered this command.
        query: The search query. Use double quotes for exact matches, and
            prepend a term with a "-" to exclude it.
        limit: Number of results to display (default: 3).
    """
    await interaction.response.defer()

    # Validate limit
    limit = limit if 0 < limit < 25 else 3

    try:
        # Query MongoDB
        results = list(
            collection.find(
                {"$text": {"$search": query}},
                {
                    "score": {"$meta": "textScore"},
                    "_id": False,
                    "ctftime_content": False,
                    "blog_content": False,
                },
            )
            .sort([("score", {"$meta": "textScore"})])
            .limit(limit)
        )

        # Build the embed
        embed = discord.Embed(
            title="🕸️ CTF Write-ups Search Index",
            colour=discord.Colour.blue(),
            description=(
                "No results found, want some cookies instead? 🍪"
                if len(results) == 0
                else f"🔍 Search results for: {query}"
            ),
        )
        for writeup in results:
            embed.add_field(
                name=f"🚩 {writeup.get('ctf', 'Unknown CTF')}",
                value="\n".join(
                    filter(
                        None,
                        [
                            "```yaml",
                            f"Search score: {writeup.get('score', 0):.2f}",
                            f"Challenge: {writeup.get('name', 'Unknown')}",
                            f"Tags: {writeup.get('tags', 'None')}",
                            f"Author: {writeup.get('author', 'Unknown')}",
                            f"Team: {writeup.get('team', 'Unknown')}",
                            "```",
                            writeup.get('ctftime', 'No CTFTime link'),
                            writeup.get('url', ''),
                        ],
                    )
                ),
                inline=False,
            )

        # Send the embed
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(
            f"An error occurred while searching: {str(e)}"
        )
