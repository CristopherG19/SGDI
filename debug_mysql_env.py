import sys
import os

print("Executable:", sys.executable)
print("CWD:", os.getcwd())
print("Path:", sys.path)

try:
    import mysql
    print("MySQL package found at:", mysql.__path__)
except ImportError as e:
    print("Error importing mysql:", e)

try:
    import mysql.connector
    print("MySQL Connector found at:", mysql.connector.__file__)
except ImportError as e:
    print("Error importing mysql.connector:", e)
