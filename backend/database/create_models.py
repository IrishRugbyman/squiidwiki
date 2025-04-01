import io
import os
import sys
import pathlib
from sqlalchemy import create_engine, MetaData
from sqlacodegen_v2.generators import DeclarativeGenerator
from dotenv import load_dotenv

# Change working directory to the script directory
path = pathlib.Path(__file__).parent.resolve()
os.chdir(path)
load_dotenv()

# Define the path to your SQLite database file
# Adjust the relative path if needed (this follows your original DB_PATH example)
DB_PATH = pathlib.Path(__file__).parent.parent.parent / "squiidvault.db"


def generate_model(database_path, outfile=None):
    """
    Connects to the SQLite database, reflects its schema, and generates
    SQLAlchemy model code to the specified output file (or stdout if None).
    """
    # Create a SQLite engine for your gangdatabase
    engine = create_engine(f"sqlite:///{database_path}")

    # Reflect the entire database schema
    metadata = MetaData()
    metadata.reflect(engine)

    # Prepare output file (or use stdout)
    outfile = io.open(outfile, 'w', encoding='utf-8') if outfile else sys.stdout

    # Generate models using sqlacodegen's DeclarativeGenerator
    options = set()
    generator = DeclarativeGenerator(metadata, engine, options)
    outfile.write(generator.generate())


if __name__ == "__main__":
    # This will generate the models into 'gang_db_alchemy.py'
    generate_model(DB_PATH, 'db_alchemy_models.py')
