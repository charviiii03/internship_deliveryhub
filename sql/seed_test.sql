INSERT INTO valid_shipments
(datetime, requestid, from_name, from_address, from_country_code, from_phone,
to_name, to_address, to_country_code, to_phone, service, state, return_code, return_json)
VALUES
(NOW(), 'sample-001', 'john', 'new york, usa', '+1', '9999999999',
'rahul', 'delhi, india', '+91', '8888888888', 'express', 'initiated', 200,
'{"status":"valid"}');

INSERT INTO invalid_shipments
(datetime, requestid, input_json, error_reason, return_code, return_json)
VALUES
(NOW(), 'sample-invalid-001',
'{"from_country_code":"+99","to_country_code":"+91"}',
'invalid from country code',
400,
'{"status":"invalid","reason":"invalid from country code"}');