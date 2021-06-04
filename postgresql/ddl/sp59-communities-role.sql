-- weko#25019, weko#25587
ALTER TABLE communities_community ADD COLUMN id_role INTEGER NOT NULL, ADD CONSTRAINT "fk_communities_community_id_role_accounts_role" FOREIGN KEY (id_role) REFERENCES accounts_role(id);
