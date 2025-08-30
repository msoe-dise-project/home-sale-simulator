FROM python:3.12-slim

WORKDIR /app
COPY simulator.py /app/
COPY kc_house_data.csv /app/

RUN pip3 install -U pip wheel
RUN pip3 install pandas "psycopg[binary]"

CMD ["python3", "simulator.py", "--home-sale-csv-fl", "kc_house_data.csv", "--days-per-period", "7"]
