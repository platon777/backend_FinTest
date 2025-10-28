import asyncio
import pyodbc
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_pyodbc_connection():
    """Test direct connection using pyodbc."""
    print("\n=== Testing Direct PYODBC Connection ===")
    try:
        connection_string = (
            f"DRIVER={{{settings.DB_DRIVER}}};"
            f"SERVER={settings.DB_SERVER};"
            f"DATABASE={settings.DB_NAME};"
            f"UID={settings.DB_USER};"
            f"PWD={settings.DB_PASSWORD};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
        )
        print(f"Connection string: DRIVER={{{settings.DB_DRIVER}}};SERVER={settings.DB_SERVER};DATABASE={settings.DB_NAME};UID={settings.DB_USER};...")

        conn = pyodbc.connect(connection_string, timeout=30)
        cursor = conn.cursor()

        # Test query
        cursor.execute("SELECT @@VERSION as version")
        row = cursor.fetchone()
        print(f"✓ Connection successful!")
        print(f"SQL Server Version: {row.version[:100]}...")

        # Get database info
        cursor.execute("SELECT DB_NAME() as current_db")
        row = cursor.fetchone()
        print(f"Current Database: {row.current_db}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        return False


def test_sqlalchemy_sync_connection():
    """Test SQLAlchemy synchronous connection."""
    print("\n=== Testing SQLAlchemy Sync Connection ===")
    try:
        # For sync, we need to use pymssql or pyodbc
        sync_url = settings.DATABASE_URL.replace("mssql+pyodbc://", "mssql+pyodbc://")
        print(f"Using URL: {sync_url[:50]}...")

        engine = create_engine(sync_url, echo=False)

        with engine.connect() as connection:
            result = connection.execute(text("SELECT @@VERSION as version"))
            row = result.fetchone()
            print(f"✓ SQLAlchemy connection successful!")
            print(f"SQL Server Version: {row[0][:100]}...")

        engine.dispose()
        return True

    except Exception as e:
        print(f"✗ SQLAlchemy connection failed: {str(e)}")
        return False


async def test_sqlalchemy_async_connection():
    """Test SQLAlchemy async connection (if supported)."""
    print("\n=== Testing SQLAlchemy Async Connection ===")
    print("Note: Async connections for SQL Server may require aioodbc")

    try:
        # For async with SQL Server, we might need to use aioodbc
        # The URL format would be different
        from app.db.database import engine

        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT @@VERSION as version"))
            row = result.fetchone()
            print(f"✓ Async SQLAlchemy connection successful!")
            print(f"SQL Server Version: {row[0][:100]}...")

        await engine.dispose()
        return True

    except Exception as e:
        print(f"✗ Async SQLAlchemy connection failed: {str(e)}")
        print("This is expected if async drivers are not properly configured.")
        print("Consider using synchronous connections or configuring aioodbc.")
        return False


def list_available_drivers():
    """List all available ODBC drivers."""
    print("\n=== Available ODBC Drivers ===")
    drivers = pyodbc.drivers()
    for driver in drivers:
        print(f"  - {driver}")

    if "ODBC Driver 18 for SQL Server" in drivers:
        print("\n✓ ODBC Driver 18 for SQL Server is available")
    elif "ODBC Driver 17 for SQL Server" in drivers:
        print("\n! ODBC Driver 17 found (you may want to update .env to use Driver 17)")
    else:
        print("\n✗ No SQL Server ODBC driver found!")
        print("Please install ODBC Driver 18 for SQL Server:")
        print("https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")


if __name__ == "__main__":
    print("="*60)
    print("SQL Server Azure Connection Test")
    print("="*60)
    print(f"Server: {settings.DB_SERVER}")
    print(f"Database: {settings.DB_NAME}")
    print(f"User: {settings.DB_USER}")
    print("="*60)

    # List drivers
    list_available_drivers()

    # Test connections
    pyodbc_success = test_pyodbc_connection()
    sqlalchemy_sync_success = test_sqlalchemy_sync_connection()

    # Test async (optional)
    # Uncomment if you want to test async
    # asyncio.run(test_sqlalchemy_async_connection())

    print("\n" + "="*60)
    print("Test Summary:")
    print(f"  PYODBC: {'✓ PASS' if pyodbc_success else '✗ FAIL'}")
    print(f"  SQLAlchemy Sync: {'✓ PASS' if sqlalchemy_sync_success else '✗ FAIL'}")
    print("="*60)
