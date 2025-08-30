#!/usr/bin/env python

import argparse
import copy
import datetime as dt
import json
import logging
import os
import pprint
import random
import sys
import time

import pandas as pd
import psycopg
from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)

USERNAME_KEY = "POSTGRES_USERNAME"
PASSWORD_KEY = "POSTGRES_PASSWORD"
HOST_KEY = "POSTGRES_HOST"
DRIFT_KEY = "ENABLE_DRIFT"

DATABASE = "home_price_prediction_service"

DAYS_TO_SEC = 24 * 60 * 60

class Simulator:
    def __init__(self, home_records, days_per_period, multiply_price):
        self.home_records = home_records
        self.multiply_price = multiply_price

        # if drift enables, kick in immediately
        if multiply_price:
            print("Drift enabled")
            self.price_multipliers = [2.0, 4.0, 1.0]
        else:
            self.price_multipliers = [1.0]

        self.sleep_delay = days_per_period * DAYS_TO_SEC / len(home_records)
        logger.debug("{} seconds per record".format(self.sleep_delay))

    def simulate_period(self):
        current_price_multiplier = self.price_multipliers[0]

        # rotate multiplier
        if self.multiply_price:
            multiplier = self.price_multipliers.pop(0)
            self.price_multipliers.append(multiplier)

        # shuffle record order to disrupt correlation with day of week
        logger.debug("start shuffle")
        shuffled_home_records = copy.deepcopy(self.home_records)
        random.shuffle(shuffled_home_records)
        logger.debug("end shuffle")

        for record in shuffled_home_records:
            record["economic_conditions"] = current_price_multiplier

            # add some random noise to the price to worsen model results
            per_rec_multiplier = current_price_multiplier + random.normalvariate(sigma=0.05)
            record["price"] = record["price"] * per_rec_multiplier

            record["sale_date"] = dt.date.today().isoformat()
            logger.debug(pprint.pformat(record))
            logger.debug("")
            yield record

            time.sleep(self.sleep_delay)

def store_events(conn_string, simulator):
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            while True:
                for record in simulator.simulate_period():
                    cur.execute("INSERT INTO raw_home_sale_events (data) VALUES (%s);",
                                [Jsonb(record)])

                    conn.commit()

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--home-sale-csv-fl",
                        type=str,
                        required=True)

    parser.add_argument("--days-per-period",
                        type=int,
                        required=True)

    parser.add_argument("--dry-run",
                        action="store_true")

    return parser.parse_args()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args()

    home_sales_df = pd.read_csv(args.home_sale_csv_fl)

    # keep only last sale event for a given home
    home_sales_df = home_sales_df.drop_duplicates(subset=["id"], keep="last", ignore_index=True)
    home_sales_df = home_sales_df.drop(columns=["id"])
    home_sales_df = home_sales_df.rename(columns={ "date" : "sale_date" })

    logger.debug("{} home records".format(len(home_sales_df)))

    multiply_prices = False
    if DRIFT_KEY in os.environ and os.environ[DRIFT_KEY] == "1":
        multiply_prices = True

    simulator = Simulator(home_sales_df.to_dict("records"),
                          args.days_per_period,
                          multiply_prices)

    if args.dry_run:
        for record in simulator.simulate_period():
            pass

    else:
        for key in [USERNAME_KEY, PASSWORD_KEY, HOST_KEY]:
            if key not in os.environ:
                msg = "Must specify environmental variable {}".format(key)
                logger.error(msg)
                sys.exit(1)

        conn_string = "postgresql://{}:{}@{}:5432/{}".format(os.environ[USERNAME_KEY],
                                                             os.environ[PASSWORD_KEY],
                                                             os.environ[HOST_KEY],
                                                             DATABASE)

        store_events(conn_string,
                     simulator)
