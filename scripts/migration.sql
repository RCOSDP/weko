-- カラム追加時に初期値で設定が必要
-- 既存データへのsystem_created設定
-- oaiserver_set
ALTER TABLE oaiserver_set ADD COLUMN system_created BOOLEAN;
UPDATE oaiserver_set SET system_created = TRUE;
ALTER TABLE oaiserver_set ALTER COLUMN system_created SET NOT NULL;

-- pidrelations_pidrelation
-- 既存のプライマリキー削除
ALTER TABLE pidrelations_pidrelation DROP CONSTRAINT pk_pidrelations_pidrelation;
-- 新しいプライマリキーを設定
ALTER TABLE pidrelations_pidrelation ADD CONSTRAINT pk_pidrelations_pidrelation PRIMARY KEY (parent_id, child_id, relation_type);


ALTER TABLE access_actionsroles
DROP CONSTRAINT IF EXISTS fk_access_actionsroles_role_id_accounts_role;

ALTER TABLE accounts_userrole
DROP CONSTRAINT IF EXISTS fk_accounts_userrole_role_id;

ALTER TABLE communities_community
DROP CONSTRAINT fk_communities_community_id_role_accounts_role;

ALTER TABLE shibboleth_userrole
DROP CONSTRAINT IF EXISTS fk_shibboleth_userrole_role_id;

ALTER TABLE workflow_flow_action_role
DROP CONSTRAINT IF EXISTS fk_workflow_flow_action_role_action_role_accounts_role;

ALTER TABLE workflow_userrole
DROP CONSTRAINT IF EXISTS fk_workflow_userrole_role_id_accounts_role;


ALTER TABLE access_actionsroles
ALTER COLUMN role_id TYPE VARCHAR(80);

ALTER TABLE accounts_userrole
ALTER COLUMN role_id TYPE VARCHAR(80);

ALTER TABLE communities_community
ALTER COLUMN id_role TYPE VARCHAR(80);

ALTER TABLE shibboleth_userrole
ALTER COLUMN role_id TYPE VARCHAR(80);

ALTER TABLE workflow_flow_action_role
ALTER COLUMN action_role TYPE VARCHAR(80);

ALTER TABLE workflow_userrole
ALTER COLUMN role_id TYPE VARCHAR(80);

ALTER TABLE accounts_role
ALTER id TYPE VARCHAR(80);


ALTER TABLE access_actionsroles
ADD CONSTRAINT fk_access_actionsroles_role_id_accounts_role
FOREIGN KEY (role_id) REFERENCES accounts_role(id);

ALTER TABLE accounts_userrole
ADD CONSTRAINT fk_accounts_userrole_role_id
FOREIGN KEY (role_id) REFERENCES accounts_role(id);

ALTER TABLE communities_community
ADD CONSTRAINT fk_communities_community_id_role_accounts_role
FOREIGN KEY (id_role) REFERENCES accounts_role(id);

ALTER TABLE shibboleth_userrole
ADD CONSTRAINT fk_shibboleth_userrole_role_id
FOREIGN KEY (role_id) REFERENCES accounts_role(id);

ALTER TABLE workflow_flow_action_role
ADD CONSTRAINT fk_workflow_flow_action_role_action_role_accounts_role
FOREIGN KEY (action_role) REFERENCES accounts_role(id);

ALTER TABLE workflow_userrole
ADD CONSTRAINT fk_workflow_userrole_role_id_accounts_role
FOREIGN KEY (role_id) REFERENCES accounts_role(id);

-- accounts_role
ALTER TABLE accounts_role ADD COLUMN created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL;

ALTER TABLE accounts_role ADD COLUMN updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL;

ALTER TABLE accounts_role ADD COLUMN is_managed BOOLEAN DEFAULT TRUE NOT NULL;

ALTER TABLE accounts_role ADD COLUMN version_id INTEGER;
UPDATE accounts_role SET version_id = 0;
ALTER TABLE accounts_role ALTER COLUMN version_id SET NOT NULL;

-- accounts_user
ALTER TABLE accounts_user ADD COLUMN created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL;

ALTER TABLE accounts_user ADD COLUMN updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL;

ALTER TABLE accounts_user
ADD COLUMN username VARCHAR(255) UNIQUE,
ADD COLUMN displayname VARCHAR(255);

ALTER TABLE accounts_user
ADD COLUMN "domain" VARCHAR(255);


ALTER TABLE accounts_user ADD COLUMN version_id INTEGER;
UPDATE accounts_user SET version_id = 0;
ALTER TABLE accounts_user ALTER COLUMN version_id SET NOT NULL;


ALTER TABLE accounts_user
ADD COLUMN profile JSON DEFAULT '{}'::json,
ADD COLUMN preferences JSON DEFAULT '{}'::json;

ALTER TABLE accounts_user
ADD COLUMN blocked_at TIMESTAMP,
ADD COLUMN verified_at TIMESTAMP;


CREATE TABLE accounts_user_login_information (
    user_id INTEGER PRIMARY KEY,
    last_login_at TIMESTAMP,
    current_login_at TIMESTAMP,
    last_login_ip character varying,
    current_login_ip character varying(50),
    login_count character varying(50),
    CONSTRAINT fk_accounts_login_information_user_id FOREIGN KEY (user_id) REFERENCES accounts_user(id)
);
-- 
CREATE TABLE accounts_useridentity (
    id VARCHAR(255) PRIMARY KEY,
    id_user INTEGER NOT NULL,
    method VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES accounts_user(id)
);

CREATE INDEX accounts_useridentity_id_user_method ON accounts_useridentity (id, method);

-- accounts_useridentity
-- ←oauthclient_useridentity_bk
insert into accounts_useridentity
(
    id
    ,method
    ,id_user
    ,created
    ,updated
)
select
    id
    ,method
    ,id_user
    ,created
    ,updated
from
    oauthclient_useridentity_bk;
    
-- accounts_user_login_information
-- ←accounts_user_bk
insert into accounts_user_login_information
(
    user_id
    ,last_login_at
    ,current_login_at
    ,last_login_ip
    ,current_login_ip
    ,login_count
)
select
    id
    ,last_login_at
    ,current_login_at
    ,last_login_ip
    ,current_login_ip
    ,login_count
from
    accounts_user_bk;
    
-- accounts_userテーブルからカラム削除

ALTER TABLE accounts_user
DROP COLUMN last_login_at,
DROP COLUMN current_login_at,
DROP COLUMN last_login_ip,
DROP COLUMN current_login_ip,
DROP COLUMN login_count;



-- テーブル作成
CREATE TABLE accounts_domain_org (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts_domain_category (
    id SERIAL PRIMARY KEY,
    label VARCHAR(255),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts_domain (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    org_id INTEGER,
    category_id INTEGER,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES accounts_domain_org(id),
    FOREIGN KEY (category_id) REFERENCES accounts_domain_category(id)
);

-- テーブルバックアップの削除
drop table oaiserver_set_bk cascade;
  
drop table pidrelations_pidrelation_bk cascade; 

drop table access_actionsroles_bk cascade; 

drop table accounts_userrole_bk cascade; 

drop table accounts_role_bk cascade; 

drop table accounts_user_bk cascade; 

drop table oauthclient_useridentity_bk  cascade; 


