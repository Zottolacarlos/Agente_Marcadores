import typer
from app.logging_config import setup_logging
from app.services.analyzer import run_analysis
from app.services.chromium_bookmark_reader import read_chromium_bookmarks
from app.services.html_bookmark_parser import parse_bookmarks_html

setup_logging()
cli = typer.Typer()


def _report_ai(summary) -> None:
    if summary.ai_used:
        msg = f"IA: activada · enriquecidos {summary.ai_enriched} bookmarks"
        if summary.ai_low_confidence:
            msg += f" ({summary.ai_low_confidence} con baja confianza, revisar)"
        typer.echo(msg, err=True)
    if summary.warning:
        typer.echo(f"Aviso: {summary.warning}", err=True)


@cli.command("analyze")
def analyze(
    file: str,
    folder: str = "Pendientes",
    limit: int | None = typer.Option(None, "--limit", "-l", help="Cantidad máxima de bookmarks a analizar luego de filtrar por carpeta."),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="No valida URLs por internet. Útil para carpetas grandes."),
    use_ai: bool = typer.Option(False, "--use-ai", help="Usar IA opcional para enriquecer clasificación. Requiere OPENAI_API_KEY. Si falla, usa reglas locales."),
):
    with open(file, "rb") as f:
        bookmarks = parse_bookmarks_html(f.read())
    summary = run_analysis(bookmarks, folder, limit=limit, skip_validation=skip_validation, use_ai=use_ai)
    _report_ai(summary)
    typer.echo(summary.model_dump_json(indent=2))


@cli.command("analyze-browser")
def analyze_browser(
    browser: str,
    folder: str = "Pendientes",
    limit: int | None = typer.Option(None, "--limit", "-l", help="Cantidad máxima de bookmarks a analizar luego de filtrar por carpeta."),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="No valida URLs por internet. Útil para carpetas grandes."),
    use_ai: bool = typer.Option(False, "--use-ai", help="Usar IA opcional para enriquecer clasificación. Requiere OPENAI_API_KEY. Si falla, usa reglas locales."),
):
    bookmarks, err = read_chromium_bookmarks(browser)
    if err:
        typer.echo(err)
        raise typer.Exit(1)
    summary = run_analysis(bookmarks, folder, limit=limit, skip_validation=skip_validation, use_ai=use_ai)
    _report_ai(summary)
    typer.echo(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    cli()
