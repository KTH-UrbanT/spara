-- This file contains test data for the database tables.

-- USERS TABLE
INSERT INTO users 
    (user_id, username, email, password_hash, created_at, last_logged_in) VALUES 
    (1, 'User 1', 'test1@example.com', 'password_hash_here', '2025-01-01 12:00:00', '2024-10-01 12:00:00'),
    (2, 'User 2', 'test2@example.com', 'password_hash_here', '2025-01-01 12:00:00', 'NOW()'),
    (3, 'Default User 3', NULL, NULL, '2025-01-01 12:00:00', 'NOW()');

-- SESSIONS TABLE
INSERT INTO sessions 
    (session_id, user_id, session_token, is_active, created_at, last_accessed) VALUES 
    (1, 1, 'session_token_1', FALSE, '2025-01-01 12:00:00', '2024-10-01 12:00:00'),
    (2, 2, 'session_token_2', FALSE, '2025-01-01 12:00:00', 'NOW()'),
    (3, 2, 'session_token_3', TRUE, '2025-04-01 12:00:00', 'NOW()'),
    (4, 3, 'session_token_4', TRUE, '2025-04-01 12:00:00', 'NOW()');

-- MESSAGES TABLE
INSERT INTO messages 
    (message_id, session_id, role, content, sent_at) VALUES
    (1, 1, 'user', 'Hello, how are you?', '2025-01-01 12:00:00'),
    (2, 1, 'assistant', 'I am fine, thank you!', '2025-01-01 12:00:01'),
    (3, 2, 'user', 'What is the weather like today?', '2025-04-01 12:00:00'),
    (4, 2, 'assistant', 'It is sunny and warm.', '2025-04-01 12:00:01'),
    (5, 3, 'user', 'Tell me a joke.', '2025-04-01 12:00:02'),
    (6, 3, 'assistant', 'Why did the chicken cross the road? To get to the other side!', '2025-04-01 12:00:03');

