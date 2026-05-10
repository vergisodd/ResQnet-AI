"""Compatibility note for the retired Python dashboard.

The active ResQNet AI demo dashboard is now the static HTML/CSS/JS command
center served by FastAPI at /dashboard.
"""


def main() -> None:
    print(
        "ResQNet AI dashboard is served by FastAPI. Run:\n"
        "  uvicorn app.main:app --reload --port 8000\n"
        "Then open:\n"
        "  http://127.0.0.1:8000/dashboard"
    )


if __name__ == "__main__":
    main()
