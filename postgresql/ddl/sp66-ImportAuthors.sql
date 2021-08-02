-- weko#27127
SELECT setval('authors_id_seq', COALESCE((SELECT MAX(id)+1 FROM authors), 1), false);
