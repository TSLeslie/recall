"""Recall CLI - Command-line interface for Recall.

This module provides the main CLI application using Typer.
It includes commands for:
- Core: version, status, config, init
- Search: ask, search
- Notes: note, notes, voice
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from recall import __version__
from recall.config import RecallConfig, get_default_config
from recall.knowledge.graphrag import RecallGraphRAG
from recall.notes.quick_note import create_note, list_notes
from recall.notes.voice_note import record_voice_note
from recall.storage.index import RecordingIndex

# Create the main app
app = typer.Typer(
    name="recall",
    help="Recall - Local AI Note-Taking & Memory Bank",
    no_args_is_help=True,
)

# Create sub-apps for command groups
config_app = typer.Typer(help="Configuration commands")
app.add_typer(config_app, name="config")

# Rich console for pretty output
console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"[bold]recall[/bold] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """Recall - Local AI Note-Taking & Memory Bank.

    Capture audio, transcribe with Whisper, summarize with local LLM,
    and search your knowledge base with Graph RAG.
    """
    pass


# ============================================================================
# Core Commands (Ticket 6.1)
# ============================================================================


@app.command()
def status():
    """Show Recall status and configuration."""
    config = get_default_config()

    console.print("[bold]Recall Status[/bold]\n")

    # Storage info
    console.print(f"[cyan]Storage Directory:[/cyan] {config.storage_dir}")
    storage_exists = config.storage_dir.exists()
    status_icon = "✓" if storage_exists else "✗"
    console.print(f"  Status: {status_icon} {'exists' if storage_exists else 'not created'}")

    # Models info
    console.print(f"\n[cyan]Models Directory:[/cyan] {config.models_dir}")
    models_exists = config.models_dir.exists()
    status_icon = "✓" if models_exists else "✗"
    console.print(f"  Status: {status_icon} {'exists' if models_exists else 'not created'}")

    # Whisper model
    console.print(f"\n[cyan]Whisper Model:[/cyan] {config.whisper_model}")

    # LLM model
    if config.llm_model_path:
        llm_exists = config.llm_model_path.exists()
        status_icon = "✓" if llm_exists else "✗"
        console.print(f"[cyan]LLM Model:[/cyan] {config.llm_model_path}")
        console.print(f"  Status: {status_icon} {'available' if llm_exists else 'not found'}")
    else:
        console.print("[cyan]LLM Model:[/cyan] not configured")


@app.command()
def init():
    """Initialize Recall storage and configuration."""
    config = get_default_config()

    # Create directories
    config.storage_dir.mkdir(parents=True, exist_ok=True)
    config.models_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (config.storage_dir / "recordings").mkdir(exist_ok=True)
    (config.storage_dir / "notes").mkdir(exist_ok=True)
    (config.storage_dir / "knowledge").mkdir(exist_ok=True)

    console.print("[green]✓[/green] Recall initialized successfully!")
    console.print(f"\n[cyan]Storage:[/cyan] {config.storage_dir}")
    console.print(f"[cyan]Models:[/cyan] {config.models_dir}")
    console.print("\n[dim]Run 'recall status' to see full configuration.[/dim]")


# Config subcommands
@config_app.command("show")
def config_show():
    """Show current configuration."""
    config = get_default_config()

    table = Table(title="Recall Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Storage Directory", str(config.storage_dir))
    table.add_row("Models Directory", str(config.models_dir))
    table.add_row("Whisper Model", config.whisper_model)
    table.add_row(
        "LLM Model Path", str(config.llm_model_path) if config.llm_model_path else "not set"
    )

    console.print(table)


@config_app.command("path")
def config_path():
    """Show configuration file path."""
    config_file = Path.home() / ".recall" / "config.yaml"
    console.print(f"[cyan]Config file:[/cyan] {config_file}")

    if config_file.exists():
        console.print("[green]✓[/green] File exists")
    else:
        console.print("[yellow]![/yellow] File not created yet (using defaults)")


# ============================================================================
# Search Commands (Ticket 6.2)
# ============================================================================


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask the knowledge base"),
    sources: bool = typer.Option(False, "--sources", "-s", help="Show source references"),
):
    """Ask a question to your knowledge base using Graph RAG."""
    config = get_default_config()

    # Check if knowledge base exists
    knowledge_dir = config.storage_dir / "knowledge"
    if not knowledge_dir.exists():
        console.print("[yellow]No knowledge base found.[/yellow]")
        console.print("Run 'recall init' to initialize, then add some recordings or notes.")
        raise typer.Exit(1)

    try:
        # Initialize GraphRAG
        graphrag = RecallGraphRAG(
            working_dir=knowledge_dir,
            model_path=str(config.llm_model_path) if config.llm_model_path else None,
        )

        # Query
        result = graphrag.query(question)

        console.print(f"\n[bold]Answer:[/bold]\n{result.answer}\n")

        if sources and result.sources:
            console.print("[cyan]Sources:[/cyan]")
            for source in result.sources:
                console.print(f"  • {source}")

        if hasattr(result, "confidence"):
            console.print(f"\n[dim]Confidence: {result.confidence:.0%}[/dim]")

    except Exception as e:
        console.print(f"[red]Error querying knowledge base:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
    source: Optional[str] = typer.Option(None, "--source", help="Filter by source type"),
):
    """Search recordings and notes by keyword."""
    config = get_default_config()

    # Check if storage exists
    if not config.storage_dir.exists():
        console.print("[yellow]No storage found.[/yellow]")
        console.print("Run 'recall init' to initialize.")
        raise typer.Exit(1)

    try:
        # Initialize index
        index_path = config.storage_dir / "index.db"
        index = RecordingIndex(index_path)

        # Search
        results = index.search(query, limit=limit, source=source)

        if not results:
            console.print(f"[yellow]No results found for:[/yellow] {query}")
            return

        console.print(f"\n[bold]Found {len(results)} result(s):[/bold]\n")

        for result in results:
            title = getattr(result, "title", None) or "Untitled"
            source_type = getattr(result, "source", "unknown")
            timestamp = getattr(result, "timestamp", "")
            snippet = (
                getattr(result, "snippet", "")[:100] + "..."
                if getattr(result, "snippet", "")
                else ""
            )

            console.print(f"[cyan]{title}[/cyan] [{source_type}]")
            console.print(f"  [dim]{timestamp}[/dim]")
            if snippet:
                console.print(f"  {snippet}")
            console.print()

    except Exception as e:
        console.print(f"[red]Error searching:[/red] {e}")
        raise typer.Exit(1)


# ============================================================================
# Notes Commands (Ticket 6.3)
# ============================================================================


@app.command()
def note(
    content: str = typer.Argument(..., help="Note content"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Note title"),
    tag: Optional[List[str]] = typer.Option(
        None, "--tag", help="Add tags (can use multiple times)"
    ),
    index: bool = typer.Option(False, "--index", "-i", help="Index in knowledge base"),
):
    """Create a quick text note."""
    config = get_default_config()

    # Ensure storage exists
    notes_dir = config.storage_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create note
        graphrag = None
        if index:
            knowledge_dir = config.storage_dir / "knowledge"
            if knowledge_dir.exists():
                graphrag = RecallGraphRAG(
                    working_dir=knowledge_dir,
                    model_path=str(config.llm_model_path) if config.llm_model_path else None,
                )

        recording = create_note(
            content=content,
            title=title,
            tags=tag or [],
            base_dir=notes_dir,
            graphrag=graphrag,
        )

        console.print("[green]✓[/green] Note created!")
        if title:
            console.print(f"[cyan]Title:[/cyan] {title}")
        if tag:
            console.print(f"[cyan]Tags:[/cyan] {', '.join(tag)}")
        if index:
            console.print("[dim]Indexed in knowledge base[/dim]")

    except Exception as e:
        console.print(f"[red]Error creating note:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def notes(
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of notes to show"),
):
    """List recent notes."""
    config = get_default_config()

    notes_dir = config.storage_dir / "notes"
    if not notes_dir.exists():
        console.print("[yellow]No notes found.[/yellow]")
        console.print("Create a note with: recall note 'Your note content'")
        return

    try:
        notes_list = list_notes(notes_dir, limit=limit)

        if not notes_list:
            console.print("[yellow]No notes found.[/yellow]")
            return

        console.print(f"\n[bold]Recent Notes ({len(notes_list)}):[/bold]\n")

        for note_item in notes_list:
            title = getattr(note_item, "title", None) or "Untitled"
            timestamp = getattr(note_item, "timestamp", "")
            tags = getattr(note_item, "tags", [])
            preview = (
                getattr(note_item, "transcript", "")[:80] + "..."
                if len(getattr(note_item, "transcript", "")) > 80
                else getattr(note_item, "transcript", "")
            )

            console.print(f"[cyan]{title}[/cyan]")
            console.print(f"  [dim]{timestamp}[/dim]")
            if tags:
                console.print(f"  Tags: {', '.join(tags)}")
            console.print(f"  {preview}")
            console.print()

    except Exception as e:
        console.print(f"[red]Error listing notes:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def voice(
    duration: Optional[int] = typer.Option(
        None, "--duration", "-d", help="Recording duration in seconds"
    ),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Note title"),
    tag: Optional[List[str]] = typer.Option(None, "--tag", help="Add tags"),
    index: bool = typer.Option(False, "--index", "-i", help="Index in knowledge base"),
):
    """Record a voice note (requires microphone)."""
    config = get_default_config()

    notes_dir = config.storage_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    try:
        if duration is None:
            console.print("[yellow]Please specify duration with --duration[/yellow]")
            console.print("Example: recall voice --duration 30")
            raise typer.Exit(1)

        console.print(f"[cyan]Recording for {duration} seconds...[/cyan]")
        console.print("[dim]Press Ctrl+C to stop early[/dim]\n")

        recording = record_voice_note(
            duration_seconds=duration,
            title=title,
            tags=tag or [],
            base_dir=notes_dir,
            whisper_model=config.whisper_model,
        )

        console.print("\n[green]✓[/green] Voice note recorded and transcribed!")
        if title:
            console.print(f"[cyan]Title:[/cyan] {title}")
        console.print(f"\n[bold]Transcript:[/bold]\n{recording.transcript[:500]}...")

    except KeyboardInterrupt:
        console.print("\n[yellow]Recording cancelled[/yellow]")
    except Exception as e:
        error_msg = str(e).lower()
        if "audio" in error_msg or "microphone" in error_msg or "sounddevice" in error_msg:
            console.print("[yellow]No audio device available.[/yellow]")
            console.print("Voice notes require a microphone.")
        else:
            console.print(f"[red]Error recording:[/red] {e}")
        raise typer.Exit(1)


# Entry point
def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
