# home-sale-simulator
Simulates home sale events

## Building the Docker Image
To build a Docker image, do the following:

```bash
docker build -t home-sale-event-simulator simulator
```

## Creating the Postgres Table
The simulator deposits events into Postgres table.
Here are the instructors for creating a database
and table.  These instructions assume you have
Postgres running locally (e.g., in a Docker container).

```bash
$ psql -h 127.0.0.1 -U postgres postgres
Password for user postgres:
psql (15.10 (Debian 15.10-0+deb12u1), server 17.2 (Debian 17.2-1.pgdg120+1))
WARNING: psql major version 15, server major version 17.
         Some psql features might not work.
Type "help" for help.

postgres=# 

postgres=# CREATE DATABASE house_price_prediction_service;
CREATE DATABASE
postgres=# \c house_price_prediction_service
psql (15.10 (Debian 15.10-0+deb12u1), server 17.2 (Debian 17.2-1.pgdg120+1))
WARNING: psql major version 15, server major version 17.
         Some psql features might not work.
You are now connected to database "house_price_prediction_service" as user "postgres".
house_price_prediction_service=# 

Lastly, you can create your tables:

house_price_prediction_service=# CREATE TABLE raw_home_sale_events (
                           id serial,
                           data JSONB NOT NULL,
                           event_date date NOT NULL
                           );

CREATE TABLE
house_price_prediction_service=# \d
                       List of relations
 Schema |              Name               |   Type   |  Owner
--------+---------------------------------+----------+----------
 public | raw_home_sale_events            | table    | postgres
 public | raw_home_sale_events_id_seq     | sequence | postgres
(2 rows)

house_price_prediction_service=# \q
```

## Running the Container
To run, the container run a Docker command like so:

```bash
$ docker run --name "home-sale-event-simulator" --network home-sale-event-system -d -e POSTGRES_USERNAME="postgres" -e POSTGRES_PASSWORD="psql-password" -e POSTGRES_HOST="postgres" home-sale-event-simulator
```

The container takes several environmental variables:

* POSTGRES_USERNAME: username for the Postgres database user
* POSTGRES_PASSWORD: password for the Postgres database user
* POSTGRES_PASSWORD: hostname for the system the Postgres database service is running on
* ENABLE_DRIFT: If not passed, drift is not enabled (the default).  If the string "1" is passed,
  then prices are multipled by different values to simulate label drift.

## Validating Output
To check that it's running, you can check that the Postgres table contains events,

```bash
$ psql -h 127.0.0.1 -U postgres house_price_prediction_service
Password for user postgres:
psql (15.10 (Debian 15.10-0+deb12u1), server 17.2 (Debian 17.2-1.pgdg120+1))
WARNING: psql major version 15, server major version 17.
         Some psql features might not work.
Type "help" for help.

house_price_prediction_service=# SELECT * FROM raw_home_sale_events LIMIT 10;
```
