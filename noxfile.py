import nox

nox.options.sessions = ["test"]


@nox.session(python=["3.13"], reuse_venv=True)
def test(session):
    """Run the test suite."""
    session.install("poetry")
    session.run("poetry", "install", "--no-root", external=True)
    session.run("pytest", "-vs", "tests/", *session.posargs)


@nox.session(python="3.13", reuse_venv=True)
def lint(session):
    """Lint the codebase."""
    session.install("poetry")
    session.run("poetry", "install", "--no-root", external=True)
    session.run("ruff", "check", "src", "tests")


@nox.session(python="3.13", reuse_venv=True)
def format(session):
    """Format the code."""
    session.install("poetry")
    session.run("poetry", "install", "--no-root", external=True)
    session.run("ruff", "format", "src", "tests")
