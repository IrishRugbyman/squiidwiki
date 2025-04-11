# SquiidWiki

Une application de gestion et de visualisation de données pour suivre les alliances et relations dans les gangs.

## Fonctionnalités

- Gestion des ensembles (gangs, groupes)
- Suivi des membres et de leurs statuts
- Enregistrement des relations entre gangs (alliances et rivalités)
- Suivi des événements (fusillades, meurtres, assistances)
- Interface API RESTful complète

## Prérequis

- Python 3.9+
- PostgreSQL 13+
- Pip

## Installation

1. Clonez ce dépôt:
```bash
git clone https://github.com/votre-nom/squiidwiki.git
cd squiidwiki
```

2. Installez les dépendances:
```bash
pip install -r requirements.txt
```

3. Configurez PostgreSQL:
```bash
# Créez une base de données PostgreSQL
createdb squiidvault

# Ou connectez-vous à PostgreSQL et créez la base de données
psql -U postgres
CREATE DATABASE squiidvault;
```

4. Initialisez la structure de la base de données:
```bash
python backend/database/migrate_to_postgres.py
```

5. Lancez le serveur:
```bash
python main.py
```

## Configuration

Les paramètres de l'application sont définis dans `backend/config/config.py`. Vous pouvez configurer:

- Les connexions PostgreSQL
- Les paramètres du serveur
- La sécurité (JWT, etc.)
- Le logging

## Déploiement sur Render

Cette application est configurée pour être déployée sur Render avec une base de données PostgreSQL.

1. Créez un compte sur [Render](https://render.com/)
2. Liez votre dépôt GitHub
3. Render détectera automatiquement le fichier `render.yaml` et configurera les services

## Gestion de Base de Données

Pour les opérations courantes sur la base de données, utilisez l'utilitaire `db_manager.py`:

```bash
# Sauvegarder la base de données
python db_manager.py backup

# Restaurer une sauvegarde
python db_manager.py restore

# Exporter la base de données
python db_manager.py export

# Importer une base de données
python db_manager.py import
```

## Licence

Ce projet est sous licence [MIT](LICENSE).
