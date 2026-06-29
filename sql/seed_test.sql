-- =============================================================
-- DeliveryHub Seed Data (Test)
-- Fixed: address_line → address_line1, added email to customers,
--        added DeliveryHub default application entry
-- =============================================================

-- Default DeliveryHub application (always present as the system default)
INSERT IGNORE INTO applications
    (application_id, application_token, application_name, user_email, expiry_date)
VALUES
    ('deliveryhub-default', 'SYSTEM_DEFAULT_TOKEN_NOT_FOR_AUTH', 'DeliveryHub', 'admin@deliveryhub.com', '2099-12-31');

-- Test application
INSERT IGNORE INTO applications
    (application_id, application_token, application_name, user_email, expiry_date)
VALUES
    ('app123', 'token123', 'test_client', 'testclient@example.com', '2026-12-31');


-- Customers (email column is required - NOT NULL UNIQUE in schema)
INSERT IGNORE INTO customers (full_name, phone_number, email)
VALUES
    ('John Smith',  '+1 2097390823', 'johnsmith@example.com'),
    ('Rahul Kumar', '+91 8888888888', 'rahul@example.com');


-- Addresses (use address_line1, not address_line)
INSERT IGNORE INTO addresses (
    address_line1,
    address_line2,
    city,
    state_name,
    country,
    country_code,
    postal_code
)
VALUES
    ('164 Seneca Pl', NULL, 'New York', 'NY', 'USA', 'US', '10001'),
    ('6-4-370, Krishna Nagar Colony', 'Bhoiguda', 'Secunderabad', 'Telangana', 'India', 'IN', '500080');


-- Sample shipments
INSERT IGNORE INTO shipments (
    requestid,
    application_id,
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
    'deliveryhub-default',
    1, 2, 1, 2,
    'Express International',
    'valid', NULL, 'initiated', 200,
    '{"status":"valid","message":"Shipment request accepted successfully"}'
),
(
    'sample-invalid-001',
    'deliveryhub-default',
    1, 2, 1, 2,
    'Express International',
    'invalid', 'Invalid sender country code', 'initiated', 400,
    '{"status":"invalid","reason":"Invalid sender country code"}'
),
(
    'sample-valid-002',
    'app123',
    1, 2, 1, 2,
    'Standard',
    'valid', NULL, 'assigned', 200,
    '{"status":"valid","message":"Shipment request accepted successfully"}'
),
(
    'sample-invalid-phone',
    'app123',
    1, 2, 1, 2,
    'Express International',
    'invalid', 'Sender phone number missing', 'validation_failed', 400,
    '{"status":"invalid","reason":"Sender phone number is required"}'
);


-- Tracking entries
INSERT IGNORE INTO shipment_tracking (shipment_id, current_status)
VALUES
    (1, 'initiated'),
    (2, 'validation_failed'),
    (3, 'assigned'),
    (4, 'validation_failed');
