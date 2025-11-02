# TODO: Set up Cloud Database for Class Representative Student Tracker

## Step 1: Sign up for PlanetScale
- Create a free PlanetScale account at https://planetscale.com
- Verify email and complete account setup

## Step 2: Create Database
- Create a new database named 'classrep_db'
- Choose the free tier plan
- Initialize with empty schema

## Step 3: Get Connection Details
- Generate a connection string from PlanetScale dashboard
- Note down the host, username, password, and database name

## Step 4: Update Application Code
- Modify app.py to use environment variables for database connection
- Replace hardcoded local MySQL credentials with environment variables
- Ensure the app can connect to PlanetScale database

## Step 5: Configure Environment Variables
- Add database connection environment variables to Vercel project settings
- Test the connection in development

## Step 6: Test and Deploy
- Test the app locally with PlanetScale connection
- Push changes to GitHub
- Redeploy to Vercel
- Verify the app works with persistent database

## Step 7: Verify Functionality
- Test login and all CRUD operations
- Ensure data persists across sessions
- Confirm no more internal server errors
