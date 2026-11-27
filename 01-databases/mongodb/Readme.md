# MongoDB

MongoDB 7.0 Community Server, used by the web apps (for example `survey_service`). It isn't part of the root `docker-compose.yml`, so always run it through its Makefile. How it's wired: [docs/architecture.md](docs/architecture.md).

## Run it

All commands run from the repo root.

| | |
| --- | --- |
| Host | `mongodb://localhost:27017` (`MONGODB_HOST_PORT` in `ports.env`) |
| In-network | `mongodb://mongodb:27017` on `data-ops-network` |
| Root user | `MONGODB_INITDB_ROOT_USERNAME` / `MONGODB_INITDB_ROOT_PASSWORD` from `.env` (auth database `admin`) |
| Data | external volume `mongodb-data` |

First time on a new machine:

```sh
docker network create data-ops-network
docker volume create mongodb-data
```

Then:

```sh
make mongodb-dev-up         # start
make mongodb-dev-shell      # mongosh as root
make mongodb-dev-logs       # follow logs
make mongodb-dev-down       # remove the container (data volume kept)
make mongodb-help           # every target
```

## Create a test database

MongoDB creates a database the first time you write to it, so you can't have an empty one. The root credentials are environment variables inside the container. Use `sh -c '...'` so they expand there.

1. Create the database with a first document, plus a user limited to that database:

   ```sh
   docker exec mongodb sh -c 'mongosh --quiet -u "$MONGODB_INITDB_ROOT_USERNAME" -p "$MONGODB_INITDB_ROOT_PASSWORD" --eval "
     const t = db.getSiblingDB(\"test_orders\");
     t.items.insertOne({ name: \"first\" });
     t.createUser({ user: \"test_orders_user\", pwd: \"change-me\", roles: [{ role: \"readWrite\", db: \"test_orders\" }] });
   "'
   ```

   You can also run the same JavaScript in `make mongodb-dev-shell` after `use test_orders`.

2. Seed data from a JSON array file on the host. `mongoimport` ships in the image:

   ```sh
   docker exec -i mongodb sh -c 'mongoimport --quiet -u "$MONGODB_INITDB_ROOT_USERNAME" -p "$MONGODB_INITDB_ROOT_PASSWORD" --authenticationDatabase admin -d test_orders -c items --jsonArray' < items.json
   ```

3. Connect. The user lives in `test_orders`, so no `authSource` is needed:
   - host: `mongodb://test_orders_user:change-me@localhost:27017/test_orders`
   - another container: `mongodb://test_orders_user:change-me@mongodb:27017/test_orders`

4. Drop it when you're done:

   ```sh
   docker exec mongodb sh -c 'mongosh --quiet -u "$MONGODB_INITDB_ROOT_USERNAME" -p "$MONGODB_INITDB_ROOT_PASSWORD" --eval "
     const t = db.getSiblingDB(\"test_orders\"); t.dropUser(\"test_orders_user\"); t.dropDatabase();
   "'
   ```

## Backup and restore one database

`mongodump` and `mongorestore` are in the image too:

```sh
docker exec mongodb sh -c 'mongodump --quiet -u "$MONGODB_INITDB_ROOT_USERNAME" -p "$MONGODB_INITDB_ROOT_PASSWORD" --authenticationDatabase admin -d test_orders --archive' > test_orders.archive
docker exec -i mongodb sh -c 'mongorestore --quiet -u "$MONGODB_INITDB_ROOT_USERNAME" -p "$MONGODB_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive' < test_orders.archive
```
