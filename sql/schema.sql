CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    -- Varchar 150 is way too much for a name. Most full names are less than 20 characters.
    -- We can keep it at 50 to be safe since 150 is excessive and can lead to wasted storage.
    full_name VARCHAR(150) NOT NULL,
    phone_number VARCHAR(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS addresses (
    address_id INT AUTO_INCREMENT PRIMARY KEY,

    -- One address line is not enough. Most websites have two fields. We can have address_line1 and address_line2. 
    --This allows for more flexibility in capturing addresses, especially for international shipments where the format can vary significantly.
    address_line TEXT NOT NULL,

    city VARCHAR(100),
    -- state is a reserved word in sql. so check line 16 again. I don't know if it will function properly. 
    state VARCHAR(100),
    -- need one more for state code, similar to country code.

    country VARCHAR(100),

    -- Remove country code. It is not necessary for an international Address. We can just use the country name. If we need to standardize it, we can create a separate table for countries and reference it here.
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