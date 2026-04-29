import argparse

from dotenv import load_dotenv

from src.app.program_review import create_app


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Team 13 local demo entrypoint.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the local ingestion and summary demo server.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for the local demo server.")
    parser.add_argument("--port", type=int, default=5000, help="Port for the local demo server.")
    args = parser.parse_args()

    if args.demo:
        create_app().run(host=args.host, port=args.port, debug=True)
        return

    print("Team 13 scaffold is set up.")
    print("Run `python src/main.py --demo` to start the local ingestion demo.")
    print("See docs/team-plan.md for ownership and shared folders.")
    print("See docs/api-contracts.md for shared schemas.")


if __name__ == "__main__":
    main()
