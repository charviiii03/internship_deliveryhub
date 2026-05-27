#!/bin/bash

echo "setting up database..."

# run schema.sql on development database
# creates tables in deliveryhub_dev
mysql -u root deliveryhub_dev < sql/schema.sql

mysql -u root deliveryhub_test < sql/schema.sql

mysql -u root deliveryhub_prod < sql/schema.sql

# inserts sample/test data into testing database
mysql -u root deliveryhub_test < sql/seed_test.sql #used for testing purposes

echo "database setup completed"