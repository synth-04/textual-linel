from linel.tui import LinelApp
from linel.database import Database

def main():
    app = LinelApp(db=Database())
    app.run()

if __name__ == "__main__":
    main()