from app.app import dynamic_app  # noqa We need this to load all sqlalchemy tables


if __name__ == "__main__":
    dynamic_app.run_commands()
    