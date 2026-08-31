import click


@click.command("hello")
def hello():
    click.echo("Hello from the custom Bench CLI!")


commands = [hello]