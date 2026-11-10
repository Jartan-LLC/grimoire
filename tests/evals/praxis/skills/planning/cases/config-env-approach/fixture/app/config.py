import configparser

parser = configparser.ConfigParser()
parser.read("settings.ini")
PORT = parser.getint("server", "port")
DB_URL = parser.get("db", "url")
