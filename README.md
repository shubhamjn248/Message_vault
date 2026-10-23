# Message Vault

An authenticated Python web service that stores messages only after redacting sensitive information. The application detects JWT-like tokens, email addresses, valid IPv4 addresses, and Luhn-valid credit-card candidates.

The project includes a web UI, REST APIs, a Python CLI, SQLite persistence, HTTPS with an automatically generated self-signed certificate, Docker support, pytest API/unit tests, and Playwright end-to-end tests.

## Features

- Redacts sensitive information before persisting messages.
- Provides authenticated create, list, retrieve, and delete APIs.
- Displays stored messages in an HTML table.
- Uses HTTP Basic authentication for the web UI and API.
- Supports HTTPS using a self-signed certificate generated at startup.
- Persists messages in a SQLite database stored in a Docker volume.
- Includes a Python CLI and automated API, unit, and browser tests.

## Prerequisites

To run the application:
- Docker Desktop on Windows/macOS, or Docker Engine with the Docker Compose plugin on Linux.

To run tests and the CLI locally:
- Python 3.12 recommended.
- Git, if cloning the repository.
- Playwright Chromium for browser tests.

Docker is sufficient to run the application. A local Python environment is required for the CLI and test suite.

## 1. Start the application using Docker

### Step 1: Configure credentials

Copy `.env.example` to `.env` in the project root.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Open `.env` and set your own credentials:

```dotenv
APP_USERNAME=demo
APP_PASSWORD=change-this-password
```

These values are examples. Replace the password with a strong password before starting the application.

The application reads its authentication credentials at startup. If you change `.env` while the application is running, recreate the application container so the new values take effect.

**Important:** Keep `.env` out of version control. Never commit real credentials or private keys.

### Step 2: Build and start the application

From the project root, run:

```bash
docker compose up --build -d
```

Check the container status:

```bash
docker compose ps
```

View application logs if startup fails:

```bash
docker compose logs
```

### Step 3: Open the web UI

Open:

https://localhost:8443

Sign in using the `APP_USERNAME` and `APP_PASSWORD` configured in `.env`.

The application uses a locally generated self-signed TLS certificate. Your browser may display a certificate warning because the certificate is not signed by a publicly trusted certificate authority.

For this local development application, verify that you are connecting to `localhost` before proceeding. Do not disable certificate verification for production services.

### Step 4: Check application health

Open:

https://localhost:8443/health

The health endpoint is intended for checking whether the application is responding and does not require Basic authentication.

### Step 5: Stop the application

```bash
docker compose down
```

This stops and removes the containers but preserves the named Docker volumes.

To remove the persisted database and generated certificate volumes as well:

```bash
docker compose down -v
```

**Warning:** The `-v` option permanently removes the data stored in those Docker volumes, including saved messages and the generated certificate.

## 2. Authentication and TLS

### Authentication

The web UI and API use HTTP Basic authentication.

Credentials are configured using environment variables at application startup:

- `APP_USERNAME`
- `APP_PASSWORD`

There is no user registration endpoint.

Use the same credentials in the browser, CLI, Postman, and Playwright tests.

### TLS certificate

The application automatically generates a self-signed certificate on first startup and stores it in the `message_certs` Docker volume.

The certificate includes these subject alternative names:

- `localhost`
- `127.0.0.1`

The certificate is intended for local development, not production use.

The Python CLI skips TLS certificate verification when no CA bundle is supplied. This is a convenience for the local demo only. For stricter verification, obtain the server certificate from the running container and supply it using the CLI's `--ca-bundle` option.

For example, if the container is named `message-vault`:

```powershell
docker cp message-vault:/certs/server.crt .\server.crt
python -m client.cli --ca-bundle .\server.crt list
```

Adjust the container name or certificate path if your Docker configuration differs. Keep certificate private keys out of version control.

## 3. Python setup for local tests and CLI

Use Python 3.12 for the local environment to improve compatibility with the project's dependencies.

### Windows PowerShell

Create a virtual environment:

```powershell
py -3.12 -m venv .venv
```

Install dependencies using the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install the Chromium browser for Playwright:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

Using the full path avoids PowerShell activation-policy problems. Alternatively, activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If your PowerShell execution policy blocks activation, you can continue using the full-path commands above without changing the policy.

### macOS/Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m playwright install chromium
```

If `python3.12` is not installed, install it using the official Python distribution for your operating system.

## HTTPS Certificate Setup

The application runs over HTTPS using a self-signed certificate. Because this certificate is not issued by a trusted Certificate Authority (CA), clients such as the Python CLI and Postman may reject the connection unless the certificate is explicitly trusted.

### 1. Export the server certificate

Start the application using Docker Compose:

```powershell
docker compose up -d
```

Copy the server certificate from the running container into the project root:

```powershell
docker cp message-vault:/certs/server.crt .\server.crt
```

If your container has a different name, find it with:

```powershell
docker ps
```

The exported `server.crt` file contains the public certificate only. **Do not export or share the private key (`server.key`).**

Keep the certificate available while testing locally. If the container regenerates its certificate, export the updated certificate again.

### 2. Configure the Python CLI

Pass the exported certificate to the CLI using the `--ca-bundle` option:

```powershell
python -m client.cli --ca-bundle .\server.crt create "Test message"
```

Use the configured application username and password if your CLI requires them. For example:

```powershell
python -m client.cli --username demo --password "change-this-password" --ca-bundle .\server.crt create "Test message"
```

Replace the example credentials with the values configured for your environment.

### 3. Configure Postman

Postman also needs to trust the self-signed certificate to make HTTPS requests without certificate-validation errors.

1. Start the application and export `server.crt` using the steps above.
2. Open **Postman Settings**.
3. Find the **Certificates** section.
4. Add a CA certificate for the host `localhost` and port `8443`, selecting the exported `server.crt` file as the CA certificate. If your Postman version provides a different certificate configuration flow, use its corresponding CA certificate option.
5. Ensure SSL certificate verification is enabled, then save the settings.

Now send requests to:

```text
https://localhost:8443
```

For protected endpoints, configure **Authorization → Basic Auth** in Postman using the application credentials from your environment.

#### Example API requests

**Create a message**

- Method: `POST`
- URL: `https://localhost:8443/api/messages`
- Authorization: Basic Auth
- Body: raw → JSON

```json
{
  "message": "Contact alice@example.com from 192.168.1.10"
}
```

**List messages**

- Method: `GET`
- URL: `https://localhost:8443/api/messages`

**Retrieve a message**

- Method: `GET`
- URL: `https://localhost:8443/api/messages/{id}`

**Delete a message**

- Method: `DELETE`
- URL: `https://localhost:8443/api/messages/{id}`

Replace `{id}` with an actual message ID returned by the create or list endpoint.

### Troubleshooting

- **Certificate verification failed:** Confirm that Postman or the CLI is using the exported `server.crt` and that it matches the certificate currently served by the container.
- **401 Unauthorized:** Verify the configured Basic Auth credentials.
- **Connection refused:** Check that the container is running and that port `8443` is published.
- **Certificate hostname mismatch:** Access the application using `localhost`, matching the certificate's hostname.

> **Security note:** This self-signed certificate setup is intended for local development and testing. Do not disable SSL verification as a permanent workaround, and do not use this development certificate as a production trust configuration.

## 4. Python CLI usage

Run CLI commands from the project root while the Docker application is running.

The CLI uses this default base URL:

`https://localhost:8443`

Set credentials to match the running application. If you have changed the default credentials in `.env`, the CLI's default credentials will not automatically change unless the CLI explicitly loads those environment variables. Pass the credentials as arguments or set the supported environment variables.

Examples using explicit credentials:

```bash
python -m client.cli --username demo --password 'change-this-password' create "Email jane@example.com from 192.168.1.10"

python -m client.cli --username demo --password 'change-this-password' list

python -m client.cli --username demo --password 'change-this-password' get 1

python -m client.cli --username demo --password 'change-this-password' delete 1
```

Replace the example credentials and message ID with your configured values.

The CLI's default TLS behavior is intended for local testing. Supply `--ca-bundle` to verify the server certificate against a trusted certificate bundle. Do not disable certificate verification in production.

## 5. REST API examples

Base URL:

`https://localhost:8443`

All message endpoints require HTTP Basic authentication.

### Create a message

**Endpoint:** `POST /api/messages`

Example request using curl:

```bash
curl -k -u demo:change-this-password \
  -H "Content-Type: application/json" \
  -d '{"message":"Contact jane@example.com from 192.168.1.10"}' \
  https://localhost:8443/api/messages
```

The response should contain the newly created message, including its generated ID and redacted content. The exact response fields depend on the API schema.

### List messages

**Endpoint:** `GET /api/messages`

```bash
curl -k -u demo:change-this-password \
  https://localhost:8443/api/messages
```

### Retrieve one message

**Endpoint:** `GET /api/messages/{id}`

```bash
curl -k -u demo:change-this-password \
  https://localhost:8443/api/messages/1
```

### Delete a message

**Endpoint:** `DELETE /api/messages/{id}`

```bash
curl -k -u demo:change-this-password \
  -X DELETE \
  https://localhost:8443/api/messages/1
```

A successful deletion returns HTTP `204 No Content`. A request for a nonexistent message should return HTTP `404 Not Found`.

The `-k` option tells curl to skip certificate verification. Use it only for this local self-signed certificate example.

### Using Postman

1. Create a request and set the URL to `https://localhost:8443/api/messages`.
2. Open the **Authorization** tab and select **Basic Auth**.
3. Enter the credentials configured in `.env`.
4. For a POST request, select **Body → raw → JSON** and use:

```json
{
  "message": "Contact jane@example.com from 192.168.1.10"
}
```

5. Send the request and verify that the returned message contains the redaction placeholders rather than the original sensitive values.
6. To list messages, use `GET /api/messages`. To retrieve or delete a particular message, use `/api/messages/{id}` with the ID returned by the create request.

Because the certificate is self-signed, Postman may reject the HTTPS connection initially. For local testing only, disable SSL certificate verification in Postman's settings. Re-enable it for normal use, and never use this workaround for production services.

## 6. Run the automated tests

Ensure the dependencies are installed in your virtual environment.

### Unit and API tests

Run:

```bash
python -m pytest -m "not e2e" -v
```

These tests cover redaction and API behavior using the in-process test client.

Make sure the tests use a dedicated test database rather than a database containing messages you want to retain. Check the test fixtures and `DATABASE_URL` configuration before running tests against a shared or persistent database.

### Playwright end-to-end tests

The UI tests target the running Docker application, so start the application before running them.

Set the credentials to match the running container.

Windows PowerShell:

```powershell
$env:APP_USERNAME = "demo"
$env:APP_PASSWORD = "change-this-password"

python -m pytest tests/test_ui.py -v
```

macOS/Linux:

```bash
export APP_USERNAME="demo"
export APP_PASSWORD="change-this-password"

python -m pytest tests/test_ui.py -v
```

These tests verify redaction in the UI and message deletion. They use the local self-signed certificate configuration for the test environment and attempt to clean up created messages.

To run all tests:

```bash
python -m pytest -v
```

If the UI tests fail to connect, check that Docker is running, the application is listening on port `8443`, the credentials match, and Chromium is installed.

## 7. Design decisions

- **Redaction before persistence:** The application transforms message content before storing it. Raw sensitive values should not be persisted.
- **JWT detection:** JWT-like compact tokens are detected using a heuristic, not a complete JWT parser.
- **Credit-card detection:** Candidate card numbers are redacted when they match the supported length and Luhn validation rules.
- **IP validation:** IPv4 candidates are replaced only when Python's `ipaddress` module considers them valid.
- **Authentication:** HTTP Basic credentials are configured through startup environment variables. Use strong secrets outside local development.
- **TLS:** HTTPS is enabled with an automatically generated self-signed certificate for local development.
- **Persistence:** SQLite keeps the project lightweight, with Docker volumes preserving database state across container recreation.
- **UI escaping:** Jinja template autoescaping helps protect against stored HTML injection.

## 8. Known limitations and future improvements

- Redaction is heuristic and may miss unusual or obfuscated sensitive data.
- The JWT detection logic supports a limited pattern rather than every valid JWT representation.
- HTTP Basic authentication over TLS is adequate for this exercise, but production services should consider stronger identity management, secret rotation, rate limiting, and audit controls.
- The self-signed certificate and local CLI TLS-verification shortcut are not suitable as production defaults.
- SQLite is suitable for this small challenge but may need replacement for workloads requiring higher concurrency.
- The application does not currently include pagination, retention policies, database migrations, or comprehensive load testing.
- Future improvements could include structured logging with sensitive-data protection, fuzz testing, CI integration, coverage thresholds, and broader negative tests for authentication, TLS, and API error handling.

## 9. Challenges Encountered

1. **Environment Setup:** Setting up the development environment on the laptop, installing the required software and dependencies, and configuring the application to run locally using Docker.

2. **Reviewing AI-Generated Code:** Reviewing AI-generated code to ensure it followed good coding practices, avoided code duplication, did not expose hardcoded credentials, and provided adequate functional and UI test coverage.

3. **Debugging and Integration:** Troubleshooting issues encountered during development and testing, including frequently restarting Docker containers, SSL certificate configuration and verification failures, synchronizing certificate and key files with Docker, and test failures caused by credentials not being passed correctly.

## 10. Self-Assessed Areas for Improvement

1. **API Design and Test Planning:** Further improving API endpoint design by clearly defining use cases, expected behavior, and acceptance criteria before implementation. Strengthening test planning by identifying appropriate unit, integration, and end-to-end test cases, including negative and boundary scenarios. Ensuring test data is cleaned up after execution to keep tests independent and repeatable.

2. **Error Handling and Diagnostics:** Improving error handling by providing clear, consistent, and actionable error messages for different failure scenarios, such as invalid input, authentication failures, missing resources, and internal server errors. This would make debugging easier for both developers and users.

3. **Edge-Case Handling:** Strengthening input validation and test coverage for edge cases, including sensitive data at the end of a sentence followed by punctuation, such as `email is test@yopmail.com.` or `IP is 124.1.1.1.`, as well as empty or whitespace-only input. Ensuring punctuation is handled correctly and sensitive information is redacted without leaving any unintended exposure.
