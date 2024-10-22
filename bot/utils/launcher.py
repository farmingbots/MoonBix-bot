import os
import glob
import argparse
import sys
import requests
from pyrogram import Client
from better_proxy import Proxy
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from rich.live import Live
from rich.layout import Layout
from datetime import datetime

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper_no_thread
from bot.core.query import run_tapper_no_thread_query
from bot.core.registrator import register_sessions
import importlib.util

console = Console()
curr_version = "3.0.5"

def create_header() -> Panel:
    grid = Table.grid(padding=1)
    grid.add_column(style="cyan", justify="center")
    grid.add_column(style="magenta")
    
    grid.add_row(
        """
    ███╗   ███╗ ██████╗  ██████╗ ███╗   ██╗██████╗ ██╗██╗  ██╗
    ████╗ ████║██╔═══██╗██╔═══██╗████╗  ██║██╔══██╗██║╚██╗██╔╝
    ██╔████╔██║██║   ██║██║   ██║██╔██╗ ██║██████╔╝██║ ╚███╔╝ 
    ██║╚██╔╝██║██║   ██║██║   ██║██║╚██╗██║██╔══██╗██║ ██╔██╗ 
    ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝██║ ╚████║██████╔╝██║██╔╝ ██╗
    ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚═╝╚═╝  ╚═╝
        """,
        f"\n[bold]Version:[/bold] {curr_version}\n[bold]Author:[/bold] github.com/farmingbots\n[bold]Time:[/bold] {datetime.now().strftime('%H:%M:%S')}"
    )
    
    return Panel(
        grid,
        box=box.DOUBLE,
        title="[bold cyan]MOONBIX BOT[/bold cyan]",
        border_style="blue"
    )

def create_menu() -> Panel:
    menu_items = Table.grid(padding=1)
    menu_items.add_column(style="cyan", justify="center")
    menu_items.add_row("[1] 🚀 Run Clicker (Session)")
    menu_items.add_row("[2] 📝 Create Session")
    
    return Panel(
        menu_items,
        title="[bold]Menu Options[/bold]",
        border_style="magenta",
        box=box.ROUNDED
    )

def check_version():
    try:
        version = requests.get("https://raw.githubusercontent.com/farmingbots/moonbix-bot/refs/heads/main/version")
        version_ = version.text.strip()
        if curr_version == version_:
            console.print(Panel.fit(
                "✅ Your version is up to date!",
                style="green",
                box=box.ROUNDED
            ))
        else:
            console.print(Panel.fit(
                f"⚠️  New version {version_} detected! Please update the bot!",
                style="yellow",
                box=box.ROUNDED
            ))
            sys.exit()
    except:
        console.print(Panel.fit(
            "❌ Failed to check version",
            style="red",
            box=box.ROUNDED
        ))

def get_session_names() -> list[str]:
    session_names = sorted(glob.glob("sessions/*.session"))
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]
    return session_names

def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []
    return proxies

def display_stats(sessions_count: int, proxies_count: int):
    stats = Table.grid(padding=1)
    stats.add_column(style="cyan")
    stats.add_column(style="green", justify="right")
    
    stats.add_row("Sessions detected:", str(sessions_count))
    stats.add_row("Proxies loaded:", str(proxies_count))
    
    console.print(Panel(
        stats,
        title="[bold]System Status[/bold]",
        border_style="blue",
        box=box.ROUNDED
    ))

async def get_tg_clients() -> list[Client]:
    global tg_clients

    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("❌ Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("❌ API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients

async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")
    
    console.clear()
    console.print(create_header())
    check_version()
    
    sessions_count = len(get_session_names())
    proxies_count = len(get_proxies())
    display_stats(sessions_count, proxies_count)
    
    console.print(create_menu())

    action = parser.parse_args().action

    if not action:
        while True:
            action = console.input("[bold cyan]Enter your choice >[/bold cyan] ")

            if not action.isdigit():
                console.print("❌ Action must be a number", style="red")
            elif action not in ["1", "2"]:
                console.print("❌ Action must be 1 or 2", style="red")
            else:
                action = int(action)
                break

    if action == 2:
        console.print("\n[bold green]Starting session registration...[/bold green]")
        await register_sessions()
    elif action == 1:
        console.print("\n[bold green]Initializing clicker...[/bold green]")
        tg_clients = await get_tg_clients()
        proxies = get_proxies()
        await run_tapper_no_thread(tg_clients=tg_clients, proxies=proxies)

if __name__ == "__main__":
    import asyncio
    asyncio.run(process())