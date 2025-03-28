# Kosmos - technical test

## How to setting up environment and install dependencies

With `uv` create an new environment:

```bash
uv venv
```

Activate shell:

```bash
source .venv//bin/activate
```

Install dependencies:

```bash
uv pip install -e .
```

## How to run

> IMPORTANT: if you want to provide an custom `.env` file, you must add the follow flag: `--env-file .env`

Up `server`:

```bash
uv run python src//server.py
```

Up `client`:

```bash
uv run python src//client.py
```

## SSL certificates

At this time and as test mode, at the root of the repo some test certificates are provided, if you want to
use some custom certs, you must be able to create at this two simple commands:

> Generate certificate as server:

```bash
openssl req -new -x509 -days 365 -nodes -out auth//server.crt -keyout auth//server.key
```

> Generate certificate as client:

```bash
openssl req -new -x509 -days 365 -nodes -out auth//clients//client.crt -keyout auth//clients//client.key
```

## Enviroment variables

If you want to change the default port at server, and host that it's running it:

You must need to create an file `.env.` at root of project:

> Be carefull, aty this time, this `.env` file are shared between `server` and `client` file.

```bash
# .env file
SCKT_PORT=5000
HOST="0.0.0.0"
```
