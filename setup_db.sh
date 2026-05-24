#!/bin/bash

echo "setting up database..."

mysql -u root deliveryhub_dev < sql/schema.sql
mysql -u root deliveryhub_test < sql/schema.sql
mysql -u root deliveryhub_prod < sql/schema.sql

mysql -u root deliveryhub_test < sql/seed_test.sql

echo "database setup completed"