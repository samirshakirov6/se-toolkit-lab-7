# LMS API deployment

<h2>Table of contents</h2>

- [About the LMS API deployment](#about-the-lms-api-deployment)
- [Clone the repository (REMOTE)](#clone-the-repository-remote)
- [Configure the environment (REMOTE)](#configure-the-environment-remote)
- [Start the services (REMOTE)](#start-the-services-remote)
- [Populate the database (LOCAL)](#populate-the-database-local)
- [Verify the deployment (LOCAL)](#verify-the-deployment-local)
- [Troubleshooting](#troubleshooting)
  - [Port conflict (`port is already allocated`)](#port-conflict-port-is-already-allocated)
  - [Containers exit immediately](#containers-exit-immediately)
  - [Image pull fails](#image-pull-fails)

## About the LMS API deployment

This page describes how to deploy the [LMS API](./lms-api.md#about-the-lms-api) to [your VM](./vm.md#your-vm) using [`Docker Compose`](./docker-compose.md#what-is-docker-compose).

The deployment starts four [services](./docker-compose.md#service) defined in [`docker-compose.yml`](./docker-compose-yml.md#what-is-docker-composeyml):

- [`app`](./docker-compose-yml.md#app-service)
- [`postgres`](./docker-compose-yml.md#postgres-service)
- [`pgadmin`](./docker-compose-yml.md#pgadmin-service)
- [`caddy`](./docker-compose-yml.md#caddy-service).

## Clone the repository (REMOTE)

1. [Connect to your VM](./vm-access.md#connect-to-the-vm-as-the-user-user-local).

2. To navigate to the [home directory](./file-system.md#home-directory-),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd ~
   ```

3. To clone your [fork](./github.md#fork),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   git clone https://github.com/<your-github-username>/se-toolkit-lab-6
   ```

   Replace the placeholder [`<your-github-username>`](./github.md#your-github-username).

4. To enter the [repository](./github.md#repository) directory,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd se-toolkit-lab-6
   ```

## Configure the environment (REMOTE)

1. To create the [environment file](./environments.md#env-file) for [`Docker`](./docker.md#what-is-docker),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.docker.example .env.docker.secret
   ```

2. To open [`.env.docker.secret`](./dotenv-docker-secret.md#what-is-envdockersecret) in an editor,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   nano .env.docker.secret
   ```

3. Set the [`Autochecker` API credentials](./autochecker-api.md#autochecker-api-credentials):

   ```text
   AUTOCHECKER_API_LOGIN=<autochecker-api-login>
   AUTOCHECKER_API_PASSWORD=<autochecker-api-password>
   ```

   Replace the placeholders:

   - [`<autochecker-api-login>`](./autochecker-api.md#autochecker-api-login-placeholder)
   - [`<autochecker-api-password>`](./autochecker-api.md#autochecker-api-password-placeholder)

4. Set [`LMS_API_KEY`](./dotenv-docker-secret.md#lms_api_key) to a value you will remember.
   This is the [LMS API key](./lms-api.md#lms-api-key).

   ```text
   LMS_API_KEY=<lms-api-key>
   ```

   > 🟪 **Important**
   >
   > [`<lms-api-key>`](.) is the backend API key used for:
   >
   > - `Authorization: Bearer <lms-api-key>` in [`Swagger UI`](./swagger.md#what-is-swagger-ui)
   >
   > - the [LMS frontend](./lms-frontend.md#about-the-lms-frontend)

5. Save and exit:

   1. Press `Ctrl+O`.
   2. Press `Enter`.
   3. Press `Ctrl+X`.

## Start the services (REMOTE)

1. To start all services in the background,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret up --build -d
   ```

2. To check that the [containers](./docker.md#container) are running,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret ps --format "table {{.Service}}\t{{.Status}}"
   ```

   You should see all four services running:

   ```text
   SERVICE    STATUS
   app        Up 50 seconds
   caddy      Up 49 seconds
   pgadmin    Up 50 seconds
   postgres   Up 55 seconds (healthy)
   ```

> <h3>Troubleshooting</h3>
>
> [**Port conflict (`port is already allocated`)**](#port-conflict-port-is-already-allocated)
>
> [**Containers exit immediately**](#containers-exit-immediately)
>
> [**Image pull fails**](#image-pull-fails)

## Populate the database (LOCAL)

The [database](./database.md#what-is-a-database) starts empty.
You need to run the ETL pipeline to populate it with data from the [`Autochecker` API](./autochecker-api.md#about-the-autochecker-api).

1. Open in a browser: `<lms-api-base-url>/docs`.

   Replace the placeholders:

   - [`<lms-api-base-url>`](./lms-api.md#lms-api-base-url-placeholder)

   You should see the [`Swagger UI`](./swagger.md#what-is-swagger-ui) page.

2. [Authorize in `Swagger UI`](./swagger.md#authorize-in-swagger-ui) with the [`LMS_API_KEY`](./dotenv-docker-secret.md#lms_api_key) that you set in [`.env.docker.secret`](./dotenv-docker-secret.md#what-is-envdockersecret).

3. [Try the endpoint](./swagger.md#try-an-endpoint-in-swagger-ui) `POST /pipeline/sync`.

   You should get a response showing the number of items and logs loaded:

   ```json
   {
     "items_loaded": 120,
     "logs_loaded": 5000
   }
   ```

   > 🟦 **Note**
   >
   > The exact numbers depend on how much data the [`Autochecker` API](./autochecker-api.md#about-the-autochecker-api) has.
   > As long as both numbers are greater than 0, the sync worked.

4. [Try the endpoint](./swagger.md#try-an-endpoint-in-swagger-ui) `GET /items/`.

   You should get a non-empty array of items.

## Verify the deployment (LOCAL)

1. [Open `Swagger UI`](./swagger.md#open-swagger-ui).

2. Open in a browser: `<lms-api-base-url>/`.

   Replace the placeholder [`<lms-api-base-url>`](./lms-api.md#lms-api-base-url-placeholder).

   You should see the [frontend](./lms-frontend.md#about-the-lms-frontend).

3. Enter the [LMS API key](./lms-api.md#lms-api-key) to authenticate in the frontend.

4. Switch to the **Dashboard** tab.

   You should see charts with analytics data:

   - submissions timeline
   - score distribution
   - group performance
   - task pass rates

   > <h3>Troubleshooting</h3>
   >
   > If the dashboard shows no data or errors, make sure:
   >
   > - The ETL sync completed successfully ([Populate the database](#populate-the-database-local)).
   > - You entered the correct API key in the frontend.
   > - Try selecting a different lab in the dropdown (e.g., `lab-04`).

## Troubleshooting

### Port conflict (`port is already allocated`)

[Remove all containers](./docker.md#remove-all-containers), then run the `docker compose up` command again.

### Containers exit immediately

To rebuild all containers from scratch,

[run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

```terminal
docker compose --env-file .env.docker.secret down -v
docker compose --env-file .env.docker.secret up --build -d
```

### Image pull fails

Check your internet connection.
If you are behind a proxy, configure `Docker` to use it.
