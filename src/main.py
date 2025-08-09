"""
Main entry point for the Restaurant Booking Chat Agent.

This module provides the command-line interface to start the chat agent.
"""

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.command()
@click.option('--interface', default='terminal', help='Interface type: terminal or web')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def main(interface: str, debug: bool):
    """Start the Restaurant Booking Chat Agent."""
    console.print(Panel.fit(
        "[bold blue]Restaurant Booking Chat Agent[/bold blue]\n"
        "[dim]Welcome to TheHungryUnicorn booking system![/dim]",
        border_style="blue"
    ))
    
    if debug:
        console.print("[yellow]Debug mode enabled[/yellow]")
    
    if interface == 'terminal':
        console.print("[green]Starting terminal interface...[/green]")
        # TODO: Initialize terminal chat interface
        console.print("[red]Implementation coming soon![/red]")
    elif interface == 'web':
        console.print("[green]Starting web interface...[/green]")
        # TODO: Initialize web interface
        console.print("[red]Web interface implementation coming soon![/red]")
    else:
        console.print(f"[red]Unknown interface: {interface}[/red]")
        console.print("Available interfaces: terminal, web")


if __name__ == "__main__":
    main()
