import typer
from app.services.analyzer import run_analysis
from app.services.chromium_bookmark_reader import read_chromium_bookmarks
from app.services.html_bookmark_parser import parse_bookmarks_html

cli = typer.Typer()


@cli.command("analyze")
def analyze(
    file: str,
    folder: str = "Pendientes",
    limit: int | None = typer.Option(None, "--limit", "-l", help="Cantidad máxima de bookmarks a analizar luego de filtrar por carpeta."),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="No valida URLs por internet. Útil para carpetas grandes."),
):
    with open(file, "rb") as f:
        bookmarks = parse_bookmarks_html(f.read())
    summary = run_analysis(bookmarks, folder, limit=limit, skip_validation=skip_validation)
    typer.echo(summary.model_dump_json(indent=2))


@cli.command("analyze-browser")
def analyze_browser(
    browser: str,
    folder: str = "Pendientes",
    limit: int | None = typer.Option(None, "--limit", "-l", help="Cantidad máxima de bookmarks a analizar luego de filtrar por carpeta."),
    skip_validation: bool = typer.Option(False, "--skip-validation", help="No valida URLs por internet. Útil para carpetas grandes."),
):
    bookmarks, err = read_chromium_bookmarks(browser)
    if err:
        typer.echo(err)
        raise typer.Exit(1)
    summary = run_analysis(bookmarks, folder, limit=limit, skip_validation=skip_validation)
    typer.echo(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    cli()
