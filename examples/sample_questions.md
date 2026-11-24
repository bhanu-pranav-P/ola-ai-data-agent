# Sample questions to try

## For the SQL Analyst

- Which city generated the most revenue from completed bookings?
- Show me the top 5 drivers by number of completed trips
- What is the average fare per city?
- How many bookings were cancelled in each city?
- Which pickup area in Bengaluru has the most bookings?
- What is the average customer rating for SUV drivers vs Mini drivers?
- How much revenue came from bookings longer than 20 km?

## For the ETL Analyst

- Profile the file data/bookings.csv
- Clean data/bookings.csv and load it into a table called bookings_clean
- Load data/drivers.csv into a table called drivers_raw and summarise it

## Things the SQL agent should refuse

- Delete all cancelled bookings *(the read-only guard blocks this)*
- Update the fare of booking 5001 to 100 *(same — the agent can only SELECT)*
