CREATE TABLE IF NOT EXISTS valid_shipments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    datetime DATETIME,
    requestid VARCHAR(100),
    from_name VARCHAR(100),
    from_address TEXT,
    from_country_code VARCHAR(10),
    from_phone VARCHAR(20),
    to_name VARCHAR(100),
    to_address TEXT,
    to_country_code VARCHAR(10),
    to_phone VARCHAR(20),
    service VARCHAR(50),
    state VARCHAR(50) DEFAULT 'initiated',
    return_code INT,
    return_json JSON
);

CREATE TABLE IF NOT EXISTS invalid_shipments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    datetime DATETIME,
    requestid VARCHAR(100),
    input_json JSON,
    error_reason TEXT,
    return_code INT,
    return_json JSON
);
CREATE TABLE shipment_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    requestid VARCHAR(100),
    current_status VARCHAR(50),
    updated_time DATETIME
);