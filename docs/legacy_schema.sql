USE xpro_support_db;

CREATE TABLE ticket_theme(
    id INT auto_increment PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE tickets(
    id VARCHAR(64) PRIMARY KEY,
    seq INT AUTO_INCREMENT UNIQUE,
    group_chat_id BIGINT NOT NULL,
    group_title VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    message TEXT,
    theme_id INT,
    user_id BIGINT,
    username VARCHAR(255),
    submit_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status VARCHAR(32) DEFAULT 'open',
    FOREIGN KEY (theme_id) REFERENCES ticket_theme(id)
);