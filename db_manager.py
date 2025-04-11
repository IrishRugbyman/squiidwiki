#!/usr/bin/env python
import os
import sys
import shutil
import argparse
import datetime
import json
import psycopg2
import psycopg2.extras
import subprocess
from pathlib import Path
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from backend.config.config import settings, Config

# Constants
BACKUP_DIR = settings.get_backup_dir()
EXPORT_DIR = settings.get_export_dir()
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

def create_backup(description=None):
    """
    Crée une sauvegarde de la base de données PostgreSQL.
    
    Args:
        description (str, optional): Description de la sauvegarde.
        
    Returns:
        Path: Chemin vers le fichier de sauvegarde créé.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    description = description.replace(" ", "_") if description else ""
    backup_file = BACKUP_DIR / f"db_backup_{timestamp}_{description}.sql"
    
    try:
        # Obtenir la configuration PostgreSQL
        pg_config = settings.get_pg_config()
        
        # Créer la commande pg_dump
        cmd = f"pg_dump -h {pg_config['host']} -p {pg_config['port']} -U {pg_config['user']} -F p -f {backup_file} {pg_config['database']}"
        
        # Définir la variable d'environnement PGPASSWORD
        os.environ['PGPASSWORD'] = pg_config['password']
        
        # Exécuter pg_dump
        result = os.system(cmd)
        
        if result == 0:
            print(f"Backup created successfully: {backup_file}")
            
            # Créer un fichier de métadonnées
            metadata = {
                "timestamp": timestamp,
                "description": description,
                "db_name": pg_config['database'],
                "db_mode": "postgres",
                "version": "1.0"
            }
            
            metadata_file = backup_file.with_suffix('.meta')
            with open(metadata_file, 'w') as f:
                for key, value in metadata.items():
                    f.write(f"{key}={value}\n")
                    
            return backup_file
        else:
            print("Error creating backup")
            return None
            
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def list_backups():
    """
    Liste toutes les sauvegardes disponibles.
    """
    try:
        # Trouver toutes les sauvegardes PostgreSQL
        pg_backups = sorted([f for f in BACKUP_DIR.glob("db_backup_*.sql")], reverse=True)
        
        if not pg_backups:
            print("No backups found.")
            return
            
        print("\nAvailable backups:")
        print("-" * 80)
        
        # Traiter les sauvegardes PostgreSQL
        for i, backup in enumerate(pg_backups):
            # Lire les métadonnées si disponibles
            metadata_file = backup.with_suffix('.meta')
            description = ""
            db_type = "PostgreSQL"
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = dict(line.strip().split('=') for line in f if '=' in line)
                    description = metadata.get('description', '')
                    
            # Obtenir la taille du fichier
            size_mb = backup.stat().st_size / (1024 * 1024)
            
            # Obtenir la date de création
            created = datetime.datetime.fromtimestamp(backup.stat().st_mtime)
            
            print(f"{i+1}. {backup.name}")
            print(f"   Type: {db_type}")
            print(f"   Size: {size_mb:.2f} MB")
            print(f"   Created: {created}")
            if description:
                print(f"   Description: {description}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Error listing backups: {e}")

def restore_backup(backup_file=None):
    """
    Restaure une sauvegarde de la base de données.
    
    Args:
        backup_file (str or Path, optional): Chemin vers le fichier de sauvegarde à restaurer.
    """
    try:
        if backup_file is None:
            # Lister les sauvegardes disponibles
            list_backups()
            backup_num = input("\nEnter the number of the backup to restore (or 'q' to quit): ")
            
            if backup_num.lower() == 'q':
                return
                
            try:
                backup_num = int(backup_num)
                pg_backups = sorted([f for f in BACKUP_DIR.glob("db_backup_*.sql")], reverse=True)
                
                if 1 <= backup_num <= len(pg_backups):
                    backup_file = pg_backups[backup_num - 1]
                else:
                    print("Invalid backup number.")
                    return
            except ValueError:
                print("Invalid input.")
                return
                
        backup_file = Path(backup_file)
        
        if not backup_file.exists():
            print(f"Error: Backup file {backup_file} not found.")
            return
            
        # Obtenir la configuration PostgreSQL
        pg_config = settings.get_pg_config()
        
        # Créer une sauvegarde avant la restauration
        pre_restore_backup = create_backup("pre_restore")
        if not pre_restore_backup:
            if not input("Failed to create pre-restore backup. Continue anyway? (y/N): ").lower().startswith('y'):
                return
                
        # Restaurer la sauvegarde PostgreSQL
        cmd = f"psql -h {pg_config['host']} -p {pg_config['port']} -U {pg_config['user']} -d {pg_config['database']} -f {backup_file}"
        os.environ['PGPASSWORD'] = pg_config['password']
        
        result = os.system(cmd)
        
        if result == 0:
            print(f"Successfully restored database from {backup_file}")
        else:
            print(f"Error restoring backup: Command returned {result}")
            
    except Exception as e:
        print(f"Error restoring backup: {e}")

def export_db_to_sql(output_path=None, db_path=None):
    """
    Exporte la base de données vers un fichier SQL.
    
    Args:
        output_path (str or Path, optional): Chemin où sauvegarder le fichier SQL.
        db_path (str or Path, optional): Chemin vers la base de données à exporter.
        
    Returns:
        Path: Chemin vers le fichier SQL créé.
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_path is None:
            output_path = EXPORT_DIR / f"pg_export_{timestamp}.sql"
            
        output_path = Path(output_path)
        os.makedirs(output_path.parent, exist_ok=True)
        
        # Obtenir la configuration PostgreSQL
        pg_config = settings.get_pg_config()
        
        # Exporter avec pg_dump
        cmd = f"pg_dump -h {pg_config['host']} -p {pg_config['port']} -U {pg_config['user']} -F p -f {output_path} {pg_config['database']}"
        os.environ['PGPASSWORD'] = pg_config['password']
        
        result = os.system(cmd)
        
        if result == 0:
            print(f"Database successfully exported to {output_path}")
            return output_path
        else:
            print(f"Error exporting database: Command returned {result}")
            return None
            
    except Exception as e:
        print(f"Error exporting database: {e}")
        return None

def import_sql(sql_file=None, db_path=None):
    """
    Importe un fichier SQL dans la base de données.
    
    Args:
        sql_file (str or Path): Chemin vers le fichier SQL à importer.
        db_path (str or Path, optional): Chemin vers la base de données cible.
    """
    try:
        if sql_file is None:
            # Lister les fichiers SQL disponibles
            sql_files = list(EXPORT_DIR.glob("*.sql"))
            if not sql_files:
                print("No SQL files found in export directory.")
                return
                
            print("\nAvailable SQL files:")
            for i, f in enumerate(sql_files, 1):
                print(f"{i}. {f.name}")
                
            file_num = input("\nEnter the number of the file to import (or 'q' to quit): ")
            
            if file_num.lower() == 'q':
                return
                
            try:
                file_num = int(file_num)
                if 1 <= file_num <= len(sql_files):
                    sql_file = sql_files[file_num - 1]
                else:
                    print("Invalid file number.")
                    return
            except ValueError:
                print("Invalid input.")
                return
                
        sql_file = Path(sql_file)
        
        if not sql_file.exists():
            print(f"Error: SQL file {sql_file} not found.")
            return
            
        # Créer une sauvegarde avant l'import
        pre_import_backup = create_backup("pre_import")
        if not pre_import_backup:
            if not input("Failed to create pre-import backup. Continue anyway? (y/N): ").lower().startswith('y'):
                return
                
        # Obtenir la configuration PostgreSQL
        pg_config = settings.get_pg_config()
        
        # Importer avec psql
        cmd = f"psql -h {pg_config['host']} -p {pg_config['port']} -U {pg_config['user']} -d {pg_config['database']} -f {sql_file}"
        os.environ['PGPASSWORD'] = pg_config['password']
        
        result = os.system(cmd)
        
        if result == 0:
            print(f"SQL file successfully imported into database")
        else:
            print(f"Error importing SQL file: Command returned {result}")
            
    except Exception as e:
        print(f"Error importing SQL file: {e}")

def list_exports():
    """
    Liste tous les fichiers d'export disponibles.
    """
    try:
        exports = list(EXPORT_DIR.glob("*.sql"))
        
        if not exports:
            print("No exports found.")
            return
            
        print("\nAvailable exports:")
        print("-" * 80)
        
        for i, export_file in enumerate(exports, 1):
            size_mb = export_file.stat().st_size / (1024 * 1024)
            created = datetime.datetime.fromtimestamp(export_file.stat().st_mtime)
            
            print(f"{i}. {export_file.name}")
            print(f"   Size: {size_mb:.2f} MB")
            print(f"   Created: {created}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Error listing exports: {e}")

def render_upload_instructions():
    """
    Affiche les instructions pour téléverser la base de données sur Render.
    """
    print("\n========== INSTRUCTIONS FOR RENDER UPLOAD (PostgreSQL) ==========")
    print("To upload your database to Render:")
    print("\n1. Create a backup or export of your local database:")
    print("   python db_manager.py backup  # create backup")
    print("   python db_manager.py export  # export to SQL")
    
    print("\n2. Upload the SQL file to Render using:")
    print("   - The Render dashboard")
    print("   - Or direct database connection:")
    print("     psql postgresql://user:password@host:5432/database < backup.sql")
    
    print("\nNote: Replace user, password, host, and database with your Render credentials.")
    print("=" * 65)

def render_download_instructions():
    """
    Affiche les instructions pour télécharger la base de données depuis Render.
    """
    print("\n========== INSTRUCTIONS FOR RENDER DOWNLOAD (PostgreSQL) ==========")
    print("To download your database from Render to your local environment:")
    
    print("\n1. Get your database credentials from Render dashboard")
    
    print("\n2. Use pg_dump to create a backup:")
    print("   pg_dump postgresql://user:password@host:5432/database > backup.sql")
    
    print("\n3. Import the backup to your local database:")
    print("   python db_manager.py import backup.sql")
    
    print("\nNote: Replace user, password, host, and database with your Render credentials.")
    print("=" * 67)

def main():
    parser = argparse.ArgumentParser(description="Database Management Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a database backup")
    backup_parser.add_argument("-d", "--description", help="Description for the backup")
    
    # List backups command
    subparsers.add_parser("list", help="List all database backups")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore a database backup")
    restore_parser.add_argument("-i", "--index", type=int, help="Index of the backup to restore")
    restore_parser.add_argument("-f", "--file", help="Path to backup file")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export database to SQL")
    export_parser.add_argument("-o", "--output", help="Output file path")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import SQL into database")
    import_parser.add_argument("-f", "--file", required=True, help="SQL file to import")
    
    # List exports command
    subparsers.add_parser("list-exports", help="List all SQL exports")
    
    # Render push preparation command
    subparsers.add_parser("push", help="Prepare database for upload to Render")
    
    # Render pull instructions command
    subparsers.add_parser("pull", help="Get instructions for downloading database from Render")
    
    # DB info command
    subparsers.add_parser("info", help="Display current database configuration")
    
    args = parser.parse_args()
    
    if args.command == "backup":
        create_backup(args.description)
    elif args.command == "list":
        list_backups()
    elif args.command == "restore":
        if not args.index and not args.file:
            backups = list_backups()
            if backups:
                idx = input("\nEnter backup number to restore (or 'q' to quit): ")
                if idx.lower() == 'q':
                    return
                try:
                    restore_backup(backup_file=args.file)
                except ValueError:
                    print("Invalid input. Please enter a number.")
        else:
            restore_backup(backup_file=args.file)
    elif args.command == "export":
        export_db_to_sql(args.output)
    elif args.command == "import":
        import_sql(sql_file=args.file)
    elif args.command == "list-exports":
        list_exports()
    elif args.command == "push":
        render_upload_instructions()
    elif args.command == "pull":
        render_download_instructions()
    elif args.command == "info":
        print(f"\nCurrent Database Configuration:")
        print(f"Database Mode: {'postgres'}")
        print(f"PostgreSQL Connection:")
        print(f"  Host: {settings.get_pg_config()['host']}")
        print(f"  Port: {settings.get_pg_config()['port']}")
        print(f"  Database: {settings.get_pg_config()['database']}")
        print(f"  User: {settings.get_pg_config()['user']}")
        print(f"  Password: {'*' * len(settings.get_pg_config()['password'])}")
        print(f"\nBackup Directory: {BACKUP_DIR}")
        print(f"Export Directory: {EXPORT_DIR}")
        print(f"Environment: {'Production' if settings.is_production() else 'Development'}")
    else:
        # If no command is provided, show the help menu
        parser.print_help()

if __name__ == "__main__":
    main() 