CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    phone_number VARCHAR(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS addresses (
    address_id INT AUTO_INCREMENT PRIMARY KEY,

    address_line TEXT NOT NULL,

    city VARCHAR(100),

    state VARCHAR(100),

    country VARCHAR(100),

    country_code VARCHAR(5) NOT NULL,

    postal_code VARCHAR(20)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id INT AUTO_INCREMENT PRIMARY KEY,

    requestid VARCHAR(100) UNIQUE,

    sender_customer_id INT NOT NULL,

    receiver_customer_id INT NOT NULL,

    from_address_id INT NOT NULL,

    to_address_id INT NOT NULL,

    service VARCHAR(100) NOT NULL,

    validation_status ENUM('valid', 'invalid', 'pending')
        DEFAULT 'pending',

    validation_reason TEXT,

    state VARCHAR(50) DEFAULT 'initiated',

    return_code INT,

    return_json JSON,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_shipments_sender
        FOREIGN KEY (sender_customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_shipments_receiver
        FOREIGN KEY (receiver_customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_shipments_from_address
        FOREIGN KEY (from_address_id)
        REFERENCES addresses(address_id),

    CONSTRAINT fk_shipments_to_address
        FOREIGN KEY (to_address_id)
        REFERENCES addresses(address_id)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS shipment_tracking (
    tracking_id INT AUTO_INCREMENT PRIMARY KEY,

    shipment_id INT NOT NULL,

    current_status VARCHAR(50) NOT NULL,

    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_tracking_shipment
        FOREIGN KEY (shipment_id)
        REFERENCES shipments(shipment_id)
        ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;