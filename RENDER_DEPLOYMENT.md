# Déploiement SquiidWiki sur Render

Ce guide explique comment déployer SquiidWiki sur la plateforme [Render](https://render.com).

## Prérequis

- Un compte [Render](https://render.com)
- Un dépôt GitHub contenant votre code SquiidWiki

## Étapes de déploiement

### 1. Créer le service Web

1. Connectez-vous à votre compte Render
2. Allez dans le tableau de bord et cliquez sur "New +"
3. Sélectionnez "Blueprint" (cela va configurer tous les services définis dans votre fichier `render.yaml`)
4. Connectez votre dépôt GitHub et sélectionnez le dépôt SquiidWiki
5. Suivez les étapes de configuration

Le fichier `render.yaml` de SquiidWiki définit deux services qui seront créés automatiquement :
- Un service web pour l'application
- Un service PostgreSQL pour la base de données

### 2. Configuration des variables d'environnement

Le fichier `render.yaml` définit déjà les variables d'environnement nécessaires, notamment :

- `APP_ENV` : environment (production)
- `DEBUG` : désactivé en production
- `POSTGRES_DB` : nom de la base de données
- `POSTGRES_HOST` : hôte de la base de données
- `POSTGRES_PORT` : port de la base de données
- `POSTGRES_USER` : utilisateur PostgreSQL
- `POSTGRES_PASSWORD` : mot de passe PostgreSQL
- `JWT_SECRET_KEY` : clé secrète pour l'authentification JWT
- `TEST_MODE` : désactivé en production
- `AUTH_BYPASS_ENABLED` : désactivé en production

### 3. Initialisation de la base de données

La première fois que votre application se lance, la base de données PostgreSQL est créée automatiquement, mais vous devez initialiser sa structure :

1. Allez dans le shell de votre service web sur Render
2. Exécutez `python -m backend.database.migrate_to_postgres`

### 4. Vérification du déploiement

1. Une fois le déploiement terminé, cliquez sur l'URL de votre application
2. Vérifiez que l'application fonctionne correctement en accédant à `/docs` pour voir la documentation Swagger de l'API

## Base de données PostgreSQL

Votre base de données PostgreSQL est gérée par Render et est accessible uniquement par votre service web par défaut. Pour y accéder directement :

1. Allez dans le tableau de bord de votre service PostgreSQL sur Render
2. Récupérez les informations de connexion (hôte, port, utilisateur, mot de passe)
3. Utilisez un client PostgreSQL pour vous connecter

## Sauvegarde et restauration

### Sauvegarder la base de données 

1. Allez dans le shell de votre service web sur Render
2. Exécutez `python db_manager.py backup`
3. Téléchargez le fichier de sauvegarde créé

### Restaurer une sauvegarde

1. Téléversez votre fichier de sauvegarde vers votre service web sur Render
2. Exécutez `python db_manager.py restore votre_fichier_sauvegarde.sql`

## Dépannage

- **Problème de connexion à la base de données** : Vérifiez les variables d'environnement dans le tableau de bord Render
- **Erreurs 500** : Consultez les logs du service web sur Render
- **Application lente au démarrage** : C'est normal pour les services sur le plan gratuit, qui se mettent en veille après une période d'inactivité 