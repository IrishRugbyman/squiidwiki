# Deploying SquiidWiki to Render

This guide explains how to deploy SquiidWiki to Render for continuous hosting, even when your local machine is turned off.

## Prerequisites

- A [Render](https://render.com) account (free tier is available)
- Your SquiidWiki codebase in a Git repository (GitHub, GitLab, etc.)

## Deployment Steps

1. **Sign up for Render** (if you haven't already)
   - Visit [render.com](https://render.com) and create an account

2. **Connect your Git repository**
   - From the Render dashboard, click "New" and select "Blueprint"
   - Connect to your GitHub/GitLab account
   - Select your SquiidWiki repository

3. **Configure the deployment**
   - Render will automatically detect the `render.yaml` file in your repository
   - Review the settings and click "Apply"

4. **Wait for deployment**
   - Render will build and deploy your application
   - This may take a few minutes

5. **Access your application**
   - Once deployed, Render will provide a URL (e.g., `https://squiidwiki.onrender.com`)
   - Your application will now be accessible via this URL from anywhere

## Environment Variables

The following environment variables are configured in `render.yaml`:

- `APP_ENV`: Set to "production"
- `DEBUG`: Set to "false"
- `DB_NAME`: The name of your database file
- `JWT_SECRET_KEY`: Automatically generated secure key
- `PORT`: Automatically assigned by Render
- `TEST_MODE`: Set to "0"
- `AUTH_BYPASS_ENABLED`: Set to "false"

## Persistent Storage

Your SQLite database is stored in Render's persistent disk storage at `/data/squiidvault.db`. This ensures your data remains intact even when the service restarts.

## Troubleshooting

- If your deployment fails, check the build logs in the Render dashboard
- Make sure all required dependencies are in your `requirements.txt` file
- Verify that the startup command in `render.yaml` is correct

## Manual Deployment (Alternative)

If you prefer to set up the service manually instead of using the Blueprint feature:

1. In Render dashboard, select "New" → "Web Service"
2. Connect your repository
3. Name your service (e.g., "squiidwiki")
4. Set the build command to: `pip install -r requirements.txt`
5. Set the start command to: `uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
6. Select a free or paid plan as needed
7. Set the environment variables as listed above
8. Add a persistent disk with mount path `/data` and at least 1GB of storage
9. Click "Create Web Service" 