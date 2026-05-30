INSERT INTO customers (full_name, phone_number)
VALUES
('john', '9999999999'),
('rahul', '8888888888');


INSERT INTO addresses (
    address_line1,
    city,
    state_name,
    country,
    country_code,
    postal_code
)
VALUES
('new york, usa', 'New York', 'NY', 'United States of America', 'US', '10001'),
('delhi, india', 'Delhi', 'Delhi', 'India', 'IN', '110001');

INSERT IGNORE INTO shipments (
    requestid,
    sender_customer_id,
    receiver_customer_id,
    from_address_id,
    to_address_id,
    service,
    validation_status,
    validation_reason,
    state,
    return_code,
    return_json
)
VALUES
(
    'sample-001',
    1,
    2,
    1,
    2,
    'express',
    'valid',
    NULL,
    'initiated',
    200,
    '{"status":"valid"}'
);

INSERT IGNORE INTO shipments ( -- this ignore skips it, if duplicate exists
    requestid,
    sender_customer_id,
    receiver_customer_id,
    from_address_id,
    to_address_id,
    service,
    validation_status,
    validation_reason,
    state,
    return_code,
    return_json
)
VALUES
(
    'sample-invalid-001',
    1,
    2,
    1,
    2,
    'express',
    'invalid',
    'invalid from country code',
    'initiated',
    400,
    '{"status":"invalid","reason":"invalid from country code"}'
);

INSERT INTO shipment_tracking (
    shipment_id,
    current_status
)
VALUES
(1, 'initiated'),
(2, 'validation_failed');

INSERT INTO applications
(application_id, application_token, application_name, expiry_date)
VALUES
('app123', 'token123', 'test_client', '2026-12-31');