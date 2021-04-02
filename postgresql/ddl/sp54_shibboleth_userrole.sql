-- weko#23911
CREATE TABLE shibboleth_userrole (
    shib_user_id integer,
    role_id integer,
    CONSTRAINT "fk_shibboleth_userrole_role_id" FOREIGN KEY (role_id) REFERENCES accounts_role(id),
    CONSTRAINT "fk_shibboleth_userrole_user_id" FOREIGN KEY (shib_user_id) REFERENCES shibboleth_user(id)
);
