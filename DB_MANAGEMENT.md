# Gestion de la Base de Données PostgreSQL pour SquiidWiki

Ce document explique comment gérer la base de données PostgreSQL pour SquiidWiki.

## Configuration PostgreSQL

### Prérequis

1. **Installation de PostgreSQL**:
   - Téléchargez et installez PostgreSQL depuis [le site officiel](https://www.postgresql.org/download/)
   - Assurez-vous que les outils en ligne de commande (`psql`, `pg_dump`) sont dans votre PATH

2. **Configuration**:
   - Créez un fichier `.env` à la racine du projet basé sur `.env.sample`
   - Configurez les paramètres PostgreSQL:
     ```
     POSTGRES_USER=votre_utilisateur
     POSTGRES_PASSWORD=votre_mot_de_passe
     POSTGRES_HOST=localhost
     POSTGRES_PORT=5432
     POSTGRES_DB=squiidvault
     ```

3. **Création de la base de données**:
   ```bash
   psql -U postgres -c "CREATE DATABASE squiidvault;"
   ```

4. **Initialisation de la structure**:
   ```bash
   python backend/database/migrate_to_postgres.py
   ```

## Utilitaire de Gestion de Base de Données

L'outil `db_manager.py` permet de gérer facilement votre base de données:

### Commandes générales

- **Voir l'aide**: `py db_manager.py --help`
- **Voir la configuration actuelle**: `py db_manager.py info`

### Sauvegardes et Restauration

- **Créer une sauvegarde**:
  ```bash
  py db_manager.py backup -d "Description de la sauvegarde"
  ```

- **Lister les sauvegardes**:
  ```bash
  py db_manager.py list
  ```

- **Restaurer une sauvegarde**:
  ```bash
  py db_manager.py restore -i 1  # Restaure la sauvegarde n°1
  ```
  ou
  ```bash
  py db_manager.py restore  # Mode interactif
  ```

### Exports et Imports SQL

- **Exporter la base de données en SQL**:
  ```bash
  py db_manager.py export
  ```

- **Lister les exports**:
  ```bash
  py db_manager.py list-exports
  ```

- **Importer un fichier SQL**:
  ```bash
  py db_manager.py import -f exports/nom_du_fichier.sql
  ```

### Synchronisation avec Render

Pour les utilisateurs de Render:

- **Préparer un upload vers Render**:
  ```bash
  py db_manager.py push
  ```
  Cette commande vous fournira des instructions pour téléverser votre base de données.

- **Instructions pour télécharger depuis Render**:
  ```bash
  py db_manager.py pull
  ```

## Maintenance pour PostgreSQL

### Backups complets

Pour créer une sauvegarde complète (en plus de l'utilitaire intégré):

```bash
pg_dump -U postgres -d squiidvault -f sauvegarde.sql
```

### Restauration complète

```bash
psql -U postgres -d squiidvault -f sauvegarde.sql
```

### Optimisation

Pour optimiser votre base de données PostgreSQL:

```bash
psql -U postgres -d squiidvault -c "VACUUM ANALYZE;"
```

## Configuration pour le Développement et la Production

### Environnement de Développement

```
APP_ENV=development
```

### Environnement de Test

```
APP_ENV=testing
TEST_MODE=1
```

### Environnement de Production

```
APP_ENV=production
```

## Sécurité et Bonnes Pratiques

1. **Utilisez des mots de passe forts** pour votre base de données
2. **Limitez l'accès réseau** à votre base de données PostgreSQL
3. **Effectuez des sauvegardes régulières**
4. **Utilisez des utilisateurs avec des privilèges limités** en production
5. **Ne stockez jamais les identifiants de production** dans votre code source

Pour toute question ou problème, consultez la documentation PostgreSQL officielle ou les ressources de la communauté. 