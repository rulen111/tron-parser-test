# Tron Parser Test
Tiny `fastapi` service for Tron wallet parsing. Accepts address of a wallet in question, creates the query and stores it in a PostgreSQL database using `sqlalchemy`. On each POST request a background task is started, parsing account data and updating respective query in db.

Any interaction or request is asynchronous, db operations use `asyncpg` driver. Service configuration object can be found at `./src/config.py` highlighting all env variables used. Local, test or production configuration is chosen based on the value of `ENV` environment variable.
## How to use
**Build and deploy:**
```
docker-compose up --build
```
**Tron-parser:** http://localhost:8080/docs

## Future improvements
- `poetry` package management and `alembic` migrations
- Semaphore mechanism to limit the calls to Tron API
- Compensation cron job to retry parsing queries which were not parsed successfully in a background task
- Separate db operations logic using repository pattern
- Opt out of using `tronpy` and create a client using raw API