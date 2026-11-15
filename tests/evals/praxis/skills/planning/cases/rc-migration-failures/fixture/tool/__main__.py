from tool.config import load


def main():
    settings = load()
    print(settings.get("core", {}).get("greeting", "hello"))


main()
