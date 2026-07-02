-- ============================================================
-- DeliveryHub Database Schema
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id  INT          AUTO_INCREMENT PRIMARY KEY,
    full_name    VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20)  NOT NULL,
    email        VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS addresses (
    address_id    INT          AUTO_INCREMENT PRIMARY KEY,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city          VARCHAR(100),
    state_name    VARCHAR(100),
    state_code    VARCHAR(10),
    country       VARCHAR(100),
    country_code  VARCHAR(5),
    postal_code   VARCHAR(20)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS applications (
    id                INT          AUTO_INCREMENT PRIMARY KEY,
    application_id    VARCHAR(100) UNIQUE NOT NULL,
    application_token VARCHAR(255) NOT NULL,
    application_name  VARCHAR(100),
    user_email        VARCHAR(100),
    phone_number      VARCHAR(20),
    expiry_date       DATE,
    is_active         BOOLEAN      DEFAULT TRUE,
    created_at        DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS shipments (
    shipment_id          INT          AUTO_INCREMENT PRIMARY KEY,
    requestid            VARCHAR(100) UNIQUE,

    -- FIX: application_id must be VARCHAR(100) to match applications.application_id
    application_id       VARCHAR(100),

    sender_customer_id   INT NOT NULL,
    receiver_customer_id INT NOT NULL,
    from_address_id      INT NOT NULL,
    to_address_id        INT NOT NULL,
    service              VARCHAR(100) NOT NULL,
    validation_status    ENUM('valid', 'invalid', 'pending') DEFAULT 'pending',
    validation_reason    TEXT,
    state                VARCHAR(50)  DEFAULT 'initiated',
    return_code          INT,
    return_json          JSON,

    -- NEW: tracking number extracted from uploaded label PDF
    tracking_number      VARCHAR(100),

    created_at           DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_shipments_application
        FOREIGN KEY (application_id)
        REFERENCES applications(application_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_shipments_sender
        FOREIGN KEY (sender_customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_shipments_receiver
        FOREIGN KEY (receiver_customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_shipments_from_address
        FOREIGN KEY (from_address_id)
        REFERENCES addresses(address_id),

    -- FIX: was duplicated in old schema — now defined only once
    CONSTRAINT fk_shipments_to_address
        FOREIGN KEY (to_address_id)
        REFERENCES addresses(address_id)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS shipment_tracking (
    tracking_id    INT         AUTO_INCREMENT PRIMARY KEY,
    shipment_id    INT         NOT NULL,
    current_status VARCHAR(50) NOT NULL,
    updated_time   DATETIME    DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_tracking_shipment
        FOREIGN KEY (shipment_id)
        REFERENCES shipments(shipment_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS authentication_logs (
    log_id          INT          AUTO_INCREMENT PRIMARY KEY,
    application_id  VARCHAR(100) NOT NULL,
    endpoint        VARCHAR(150) NOT NULL,
    request_time    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    status          ENUM('success', 'failure') NOT NULL,
    reason          VARCHAR(255),
    ip_address      VARCHAR(100),
    request_details TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- FIX: was missing entirely from old schema
CREATE TABLE IF NOT EXISTS shipment_labels (
    label_id            INT          AUTO_INCREMENT PRIMARY KEY,
    shipment_id         INT          NOT NULL,
    file_name           VARCHAR(255) NOT NULL,
    file_path           VARCHAR(500) NOT NULL,
    uploaded_at         DATETIME     DEFAULT CURRENT_TIMESTAMP,
    emailed_to_customer BOOLEAN      DEFAULT FALSE,

    CONSTRAINT fk_label_shipment
        FOREIGN KEY (shipment_id)
        REFERENCES shipments(shipment_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
