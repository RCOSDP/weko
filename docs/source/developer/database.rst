
Schema: invenio
===============


access_actionsroles
-------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('access_actionsroles_id_seq'::regclass)
     - 
   * - action
     - action
     - VARCHAR(80)
     - False
     - False
     - None
     - 
   * - exclude
     - exclude
     - BOOLEAN
     - True
     - False
     - false
     - 
   * - argument
     - argument
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - role_id
     - role_id
     - INTEGER
     - True
     - False
     - None
     - FK: accounts_role.id

Keys
^^^^

* UNIQUE KEY: access_actionsroles_unique (action, exclude, argument, role_id)
* KEY: ix_access_actionsroles_action (action)
* KEY: ix_access_actionsroles_argument (argument)
* KEY: ix_access_actionsroles_role_id (role_id)

access_actionssystemroles
-------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('access_actionssystemroles_id_seq'::regclass)
     - 
   * - action
     - action
     - VARCHAR(80)
     - False
     - False
     - None
     - 
   * - exclude
     - exclude
     - BOOLEAN
     - True
     - False
     - false
     - 
   * - argument
     - argument
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - role_name
     - role_name
     - VARCHAR(40)
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: access_actionssystemroles_unique (action, exclude, argument, role_name)
* KEY: ix_access_actionssystemroles_action (action)
* KEY: ix_access_actionssystemroles_argument (argument)
* KEY: ix_access_actionssystemroles_role_name (role_name)

access_actionsusers
-------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('access_actionsusers_id_seq'::regclass)
     - 
   * - action
     - action
     - VARCHAR(80)
     - False
     - False
     - None
     - 
   * - exclude
     - exclude
     - BOOLEAN
     - True
     - False
     - false
     - 
   * - argument
     - argument
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - user_id
     - user_id
     - INTEGER
     - True
     - False
     - None
     - FK: accounts_user.id

Keys
^^^^

* UNIQUE KEY: access_actionsusers_unique (action, exclude, argument, user_id)
* KEY: ix_access_actionsusers_action (action)
* KEY: ix_access_actionsusers_argument (argument)
* KEY: ix_access_actionsusers_user_id (user_id)

accounts_group
--------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('accounts_group_id_seq'::regclass)
     - 
   * - name
     - name
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - description
     - description
     - TEXT
     - False
     - False
     - None
     - 
   * - is_managed
     - is_managed
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - privacy_policy
     - privacy_policy
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - subscription_policy
     - subscription_policy
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - modified
     - modified
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: ix_accounts_group_name (name)

accounts_group_admin
--------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('accounts_group_admin_id_seq'::regclass)
     - 
   * - group_id
     - group_id
     - INTEGER
     - True
     - False
     - None
     - FK: accounts_group.id
   * - admin_type
     - admin_type
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - admin_id
     - admin_id
     - INTEGER
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_accounts_group_admin_group_id (group_id, admin_type, admin_id)

accounts_group_members
----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - user_id
     - user_id
     - INTEGER
     - True
     - True
     - None
     - FK: accounts_user.id
   * - group_id
     - group_id
     - INTEGER
     - True
     - True
     - None
     - FK: accounts_group.id
   * - state
     - state
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - modified
     - modified
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 

accounts_role
-------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('accounts_role_id_seq'::regclass)
     - 
   * - name
     - name
     - VARCHAR(80)
     - False
     - False
     - None
     - 
   * - description
     - description
     - VARCHAR(255)
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_accounts_role_name (name)

accounts_user
-------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('accounts_user_id_seq'::regclass)
     - 
   * - email
     - email
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - password
     - password
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - active
     - active
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - confirmed_at
     - confirmed_at
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - last_login_at
     - last_login_at
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - current_login_at
     - current_login_at
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - last_login_ip
     - last_login_ip
     - VARCHAR(50)
     - False
     - False
     - None
     - 
   * - current_login_ip
     - current_login_ip
     - VARCHAR(50)
     - False
     - False
     - None
     - 
   * - login_count
     - login_count
     - INTEGER
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_accounts_user_email (email)

accounts_user_session_activity
------------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - sid_s
     - sid_s
     - VARCHAR(255)
     - True
     - True
     - None
     - 
   * - user_id
     - user_id
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - ip
     - ip
     - VARCHAR(80)
     - False
     - False
     - None
     - 
   * - country
     - country
     - VARCHAR(3)
     - False
     - False
     - None
     - 
   * - browser
     - browser
     - VARCHAR(80)
     - False
     - False
     - None
     - 
   * - browser_version
     - browser_version
     - VARCHAR(30)
     - False
     - False
     - None
     - 
   * - os
     - os
     - VARCHAR(80)
     - False
     - False
     - None
     - 
   * - device
     - device
     - VARCHAR(80)
     - False
     - False
     - None
     - 

accounts_userrole
-----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - user_id
     - user_id
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - role_id
     - role_id
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_role.id

admin_lang_settings
-------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - lang_code
     - lang_code
     - VARCHAR(3)
     - True
     - True
     - None
     - 
   * - lang_name
     - lang_name
     - VARCHAR(30)
     - True
     - False
     - None
     - 
   * - is_registered
     - is_registered
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - sequence
     - sequence
     - INTEGER
     - False
     - False
     - None
     - 
   * - is_active
     - is_active
     - BOOLEAN
     - False
     - False
     - None
     - 

admin_settings
--------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('admin_settings_id_seq'::regclass)
     - 
   * - name
     - name
     - VARCHAR(30)
     - False
     - False
     - None
     - 
   * - settings
     - settings
     - JSONB
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_admin_settings_name (name)

alembic_version
---------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - version_num
     - version_num
     - VARCHAR(32)
     - True
     - True
     - None
     - 

api_certificate
---------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - api_code
     - api_code
     - VARCHAR(3)
     - True
     - True
     - None
     - 
   * - api_name
     - api_name
     - VARCHAR(25)
     - True
     - False
     - None
     - 
   * - cert_data
     - cert_data
     - JSONB
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_api_certificate_api_name (api_name)

authors
-------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - BIGINT
     - True
     - True
     - nextval('authors_id_seq'::regclass)
     - 
   * - gather_flg
     - gather_flg
     - BIGINT
     - False
     - False
     - None
     - 
   * - is_deleted
     - is_deleted
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - json
     - json
     - JSONB
     - False
     - False
     - None
     - 
authors_affiliation_settings
-----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('authors_affiliation_settings_id_seq'::regclass)
     - 
   * - name
     - name
     - TEXT
     - True
     - False
     - None
     - 
   * - scheme
     - scheme
     - TEXT
     - False
     - False
     - None
     - 
   * - url
     - url
     - TEXT
     - False
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_authors_affiliation_settings_scheme (scheme)

authors_prefix_settings
-----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('authors_prefix_settings_id_seq'::regclass)
     - 
   * - name
     - name
     - TEXT
     - True
     - False
     - None
     - 
   * - scheme
     - scheme
     - TEXT
     - False
     - False
     - None
     - 
   * - url
     - url
     - TEXT
     - False
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_authors_prefix_settings_scheme (scheme)

billing_permission
------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - user_id
     - user_id
     - INTEGER
     - True
     - True
     - nextval('billing_permission_user_id_seq'::regclass)
     - 
   * - is_active
     - is_active
     - BOOLEAN
     - True
     - False
     - None
     - 

changelist_indexes
------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('changelist_indexes_id_seq'::regclass)
     - 
   * - status
     - status
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - repository_id
     - repository_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - change_dump_manifest
     - change_dump_manifest
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - max_changes_size
     - max_changes_size
     - INTEGER
     - True
     - False
     - None
     - 
   * - interval_by_date
     - interval_by_date
     - INTEGER
     - True
     - False
     - None
     - 
   * - change_tracking_state
     - change_tracking_state
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - url_path
     - url_path
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - publish_date
     - publish_date
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_changelist_indexes_repository_id (repository_id)

communities_community
---------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - VARCHAR(100)
     - True
     - True
     - None
     - 
   * - id_role
     - id_role
     - INTEGER
     - True
     - False
     - None
     - FK: accounts_role.id
   * - id_user
     - id_user
     - INTEGER
     - True
     - False
     - None
     - FK: accounts_user.id
   * - title
     - title
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - description
     - description
     - TEXT
     - True
     - False
     - None
     - 
   * - page
     - page
     - TEXT
     - True
     - False
     - None
     - 
   * - curation_policy
     - curation_policy
     - TEXT
     - True
     - False
     - None
     - 
   * - community_header
     - community_header
     - TEXT
     - True
     - False
     - None
     - 
   * - community_footer
     - community_footer
     - TEXT
     - True
     - False
     - None
     - 
   * - last_record_accepted
     - last_record_accepted
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - logo_ext
     - logo_ext
     - VARCHAR(4)
     - False
     - False
     - None
     - 
   * - ranking
     - ranking
     - INTEGER
     - True
     - False
     - None
     - 
   * - fixed_points
     - fixed_points
     - INTEGER
     - True
     - False
     - None
     - 
   * - deleted_at
     - deleted_at
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - root_node_id
     - root_node_id
     - BIGINT
     - True
     - False
     - None
     - FK: index.id

communities_community_record
----------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id_community
     - id_community
     - VARCHAR(100)
     - True
     - True
     - None
     - FK: communities_community.id
   * - id_record
     - id_record
     - UUID
     - True
     - True
     - None
     - FK: records_metadata.id
   * - id_user
     - id_user
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - expires_at
     - expires_at
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 

communities_featured_community
------------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('communities_featured_community_id_seq'::regclass)
     - 
   * - id_community
     - id_community
     - VARCHAR(100)
     - True
     - False
     - None
     - FK: communities_community.id
   * - start_date
     - start_date
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 

doi_identifier
--------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - BIGINT
     - True
     - True
     - nextval('doi_identifier_id_seq'::regclass)
     - 
   * - repository
     - repository
     - VARCHAR(100)
     - True
     - False
     - None
     - 
   * - jalc_flag
     - jalc_flag
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - jalc_crossref_flag
     - jalc_crossref_flag
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - jalc_datacite_flag
     - jalc_datacite_flag
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - ndl_jalc_flag
     - ndl_jalc_flag
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - jalc_doi
     - jalc_doi
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - jalc_crossref_doi
     - jalc_crossref_doi
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - jalc_datacite_doi
     - jalc_datacite_doi
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - ndl_jalc_doi
     - ndl_jalc_doi
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - suffix
     - suffix
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - created_userId
     - created_userId
     - VARCHAR(50)
     - True
     - False
     - None
     - 
   * - created_date
     - created_date
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated_userId
     - updated_userId
     - VARCHAR(50)
     - True
     - False
     - None
     - 
   * - updated_date
     - updated_date
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 

facet_search_setting
--------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('facet_search_setting_id_seq'::regclass)
     - 
   * - name_en
     - name_en
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - name_jp
     - name_jp
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - mapping
     - mapping
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - aggregations
     - aggregations
     - JSONB
     - False
     - False
     - None
     - 
   * - active
     - active
     - BOOLEAN
     - False
     - False
     - None
     - 

feedback_email_setting
----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('feedback_email_setting_id_seq'::regclass)
     - 
   * - account_author
     - account_author
     - TEXT
     - True
     - False
     - None
     - 
   * - manual_mail
     - manual_mail
     - JSONB
     - False
     - False
     - None
     - 
   * - is_sending_feedback
     - is_sending_feedback
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - root_url
     - root_url
     - VARCHAR(100)
     - False
     - False
     - None
     - 

feedback_mail_failed
--------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('feedback_mail_failed_id_seq'::regclass)
     - 
   * - history_id
     - history_id
     - INTEGER
     - True
     - False
     - None
     - 
   * - author_id
     - author_id
     - VARCHAR(50)
     - False
     - False
     - None
     - 
   * - mail
     - mail
     - VARCHAR(255)
     - True
     - False
     - None
     - 

feedback_mail_history
---------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('feedback_mail_history_id_seq'::regclass)
     - 
   * - parent_id
     - parent_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - start_time
     - start_time
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - end_time
     - end_time
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - stats_time
     - stats_time
     - VARCHAR(7)
     - True
     - False
     - None
     - 
   * - count
     - count
     - INTEGER
     - True
     - False
     - None
     - 
   * - error
     - error
     - INTEGER
     - False
     - False
     - None
     - 
   * - is_latest
     - is_latest
     - BOOLEAN
     - True
     - False
     - None
     - 

feedback_mail_list
------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('feedback_mail_list_id_seq'::regclass)
     - 
   * - item_id
     - item_id
     - UUID
     - True
     - False
     - None
     - 
   * - mail_list
     - mail_list
     - JSONB
     - False
     - False
     - None
     - 

file_metadata
-------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('file_metadata_id_seq'::regclass)
     - 
   * - pid
     - pid
     - INTEGER
     - False
     - False
     - None
     - 
   * - contents
     - contents
     - BYTEA
     - False
     - False
     - None
     - 
   * - json
     - json
     - JSONB
     - False
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - True
     - False
     - None
     - 

file_metadata_version
---------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - None
     - 
   * - pid
     - pid
     - INTEGER
     - False
     - False
     - None
     - 
   * - contents
     - contents
     - BYTEA
     - False
     - False
     - None
     - 
   * - json
     - json
     - JSONB
     - False
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - transaction_id
     - transaction_id
     - BIGINT
     - True
     - True
     - None
     - 
   * - end_transaction_id
     - end_transaction_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - operation_type
     - operation_type
     - SMALLINT
     - True
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_file_metadata_version_end_transaction_id (end_transaction_id)
* KEY: ix_file_metadata_version_operation_type (operation_type)
* KEY: ix_file_metadata_version_transaction_id (transaction_id)

file_onetime_download
---------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('file_onetime_download_id_seq'::regclass)
     - 
   * - file_name
     - file_name
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - user_mail
     - user_mail
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - record_id
     - record_id
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - download_count
     - download_count
     - INTEGER
     - True
     - False
     - None
     - 
   * - expiration_date
     - expiration_date
     - INTEGER
     - True
     - False
     - None
     - 
   * - extra_info
     - extra_info
     - JSONB
     - False
     - False
     - None
     - 

file_permission
---------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('file_permission_id_seq'::regclass)
     - 
   * - user_id
     - user_id
     - INTEGER
     - True
     - False
     - None
     - 
   * - record_id
     - record_id
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - file_name
     - file_name
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - usage_application_activity_id
     - usage_application_activity_id
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - usage_report_activity_id
     - usage_report_activity_id
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - status
     - status
     - INTEGER
     - True
     - False
     - None
     - 
   * - open_date
     - open_date
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 

files_bucket
------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - UUID
     - True
     - True
     - None
     - 
   * - default_location
     - default_location
     - INTEGER
     - True
     - False
     - None
     - FK: files_location.id
   * - default_storage_class
     - default_storage_class
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - size
     - size
     - BIGINT
     - True
     - False
     - None
     - 
   * - quota_size
     - quota_size
     - BIGINT
     - False
     - False
     - None
     - 
   * - max_file_size
     - max_file_size
     - BIGINT
     - False
     - False
     - None
     - 
   * - locked
     - locked
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - deleted
     - deleted
     - BOOLEAN
     - True
     - False
     - None
     - 

files_buckettags
----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - bucket_id
     - bucket_id
     - UUID
     - True
     - True
     - None
     - FK: files_bucket.id
   * - key
     - key
     - VARCHAR(255)
     - True
     - True
     - None
     - 
   * - value
     - value
     - TEXT
     - True
     - False
     - None
     - 

files_files
-----------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - UUID
     - True
     - True
     - None
     - 
   * - uri
     - uri
     - TEXT
     - False
     - False
     - None
     - 
   * - storage_class
     - storage_class
     - VARCHAR(1)
     - False
     - False
     - None
     - 
   * - size
     - size
     - BIGINT
     - False
     - False
     - None
     - 
   * - checksum
     - checksum
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - readable
     - readable
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - writable
     - writable
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - last_check_at
     - last_check_at
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - last_check
     - last_check
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - json
     - json
     - JSONB
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_files_files_uri (uri)

files_location
--------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('files_location_id_seq'::regclass)
     - 
   * - name
     - name
     - VARCHAR(20)
     - True
     - False
     - None
     - 
   * - uri
     - uri
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - default
     - default
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - type
     - type
     - VARCHAR(20)
     - False
     - False
     - None
     - 
   * - access_key
     - access_key
     - VARCHAR(128)
     - False
     - False
     - None
     - 
   * - secret_key
     - secret_key
     - VARCHAR(128)
     - False
     - False
     - None
     - 
   * - size
     - size
     - BIGINT
     - False
     - False
     - None
     - 
   * - quota_size
     - quota_size
     - BIGINT
     - False
     - False
     - None
     - 
   * - max_file_size
     - max_file_size
     - BIGINT
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_files_location_name (name)

files_multipartobject
---------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - upload_id
     - upload_id
     - UUID
     - True
     - True
     - None
     - 
   * - bucket_id
     - bucket_id
     - UUID
     - False
     - False
     - None
     - FK: files_bucket.id
   * - key
     - key
     - TEXT
     - False
     - False
     - None
     - 
   * - file_id
     - file_id
     - UUID
     - True
     - False
     - None
     - FK: files_files.id
   * - chunk_size
     - chunk_size
     - INTEGER
     - False
     - False
     - None
     - 
   * - size
     - size
     - BIGINT
     - False
     - False
     - None
     - 
   * - completed
     - completed
     - BOOLEAN
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uix_item (upload_id, bucket_id, key)

files_multipartobject_part
--------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - upload_id
     - upload_id
     - UUID
     - True
     - True
     - None
     - FK: files_multipartobject.upload_id
   * - part_number
     - part_number
     - INTEGER
     - True
     - True
     - None
     - 
   * - checksum
     - checksum
     - VARCHAR(255)
     - False
     - False
     - None
     - 

files_object
------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - version_id
     - version_id
     - UUID
     - True
     - True
     - None
     - 
   * - key
     - key
     - TEXT
     - True
     - False
     - None
     - 
   * - bucket_id
     - bucket_id
     - UUID
     - True
     - False
     - None
     - FK: files_bucket.id
   * - file_id
     - file_id
     - UUID
     - False
     - False
     - None
     - FK: files_files.id
   * - root_file_id
     - root_file_id
     - UUID
     - False
     - False
     - None
     - 
   * - _mimetype
     - _mimetype
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - is_head
     - is_head
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - created_user_id
     - created_user_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - updated_user_id
     - updated_user_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - is_show
     - is_show
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - is_thumbnail
     - is_thumbnail
     - BOOLEAN
     - True
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_files_object__mimetype (_mimetype)
* UNIQUE KEY: uq_files_object_bucket_id (bucket_id, version_id, key)

files_objecttags
----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - version_id
     - version_id
     - UUID
     - True
     - True
     - None
     - FK: files_object.version_id
   * - key
     - key
     - VARCHAR(255)
     - True
     - True
     - None
     - 
   * - value
     - value
     - TEXT
     - True
     - False
     - None
     - 

guest_activity
--------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('guest_activity_id_seq'::regclass)
     - 
   * - user_mail
     - user_mail
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - record_id
     - record_id
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - file_name
     - file_name
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - activity_id
     - activity_id
     - VARCHAR(24)
     - True
     - False
     - None
     - 
   * - token
     - token
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - expiration_date
     - expiration_date
     - INTEGER
     - True
     - False
     - None
     - 
   * - is_usage_report
     - is_usage_report
     - BOOLEAN
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: ix_guest_activity_activity_id (activity_id)

harvest_logs
------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('harvest_logs_id_seq'::regclass)
     - 
   * - harvest_setting_id
     - harvest_setting_id
     - INTEGER
     - True
     - False
     - None
     - 
   * - start_time
     - start_time
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - end_time
     - end_time
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - status
     - status
     - VARCHAR(10)
     - True
     - False
     - None
     - 
   * - errmsg
     - errmsg
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - requrl
     - requrl
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - counter
     - counter
     - JSONB
     - False
     - False
     - None
     - 
   * - setting
     - setting
     - JSONB
     - False
     - False
     - None
     - 

harvest_settings
----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('harvest_settings_id_seq'::regclass)
     - 
   * - repository_name
     - repository_name
     - VARCHAR(20)
     - True
     - False
     - None
     - 
   * - base_url
     - base_url
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - from_date
     - from_date
     - DATE
     - False
     - False
     - None
     - 
   * - until_date
     - until_date
     - DATE
     - False
     - False
     - None
     - 
   * - set_spec
     - set_spec
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - metadata_prefix
     - metadata_prefix
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - index_id
     - index_id
     - BIGINT
     - True
     - False
     - None
     - FK: index.id
   * - update_style
     - update_style
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - auto_distribution
     - auto_distribution
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - task_id
     - task_id
     - VARCHAR(40)
     - False
     - False
     - None
     - 
   * - item_processed
     - item_processed
     - INTEGER
     - False
     - False
     - None
     - 
   * - resumption_token
     - resumption_token
     - VARCHAR(512)
     - False
     - False
     - None
     - 
   * - schedule_enable
     - schedule_enable
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - schedule_frequency
     - schedule_frequency
     - VARCHAR(16)
     - False
     - False
     - None
     - 
   * - schedule_details
     - schedule_details
     - INTEGER
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_harvest_settings_repository_name (repository_name)

index
-----

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - BIGINT
     - True
     - True
     - nextval('index_id_seq'::regclass)
     - 
   * - parent
     - parent
     - BIGINT
     - True
     - False
     - None
     - 
   * - position
     - position
     - INTEGER
     - True
     - False
     - None
     - 
   * - index_name
     - index_name
     - TEXT
     - False
     - False
     - None
     - 
   * - index_name_english
     - index_name_english
     - TEXT
     - True
     - False
     - None
     - 
   * - index_link_name
     - index_link_name
     - TEXT
     - False
     - False
     - None
     - 
   * - index_link_name_english
     - index_link_name_english
     - TEXT
     - True
     - False
     - None
     - 
   * - harvest_spec
     - harvest_spec
     - TEXT
     - False
     - False
     - None
     - 
   * - index_link_enabled
     - index_link_enabled
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - comment
     - comment
     - TEXT
     - False
     - False
     - None
     - 
   * - more_check
     - more_check
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - display_no
     - display_no
     - INTEGER
     - True
     - False
     - None
     - 
   * - harvest_public_state
     - harvest_public_state
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - display_format
     - display_format
     - TEXT
     - False
     - False
     - None
     - 
   * - image_name
     - image_name
     - TEXT
     - True
     - False
     - None
     - 
   * - public_state
     - public_state
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - public_date
     - public_date
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - recursive_public_state
     - recursive_public_state
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - rss_status
     - rss_status
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - coverpage_state
     - coverpage_state
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - recursive_coverpage_check
     - recursive_coverpage_check
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - browsing_role
     - browsing_role
     - TEXT
     - False
     - False
     - None
     - 
   * - recursive_browsing_role
     - recursive_browsing_role
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - contribute_role
     - contribute_role
     - TEXT
     - False
     - False
     - None
     - 
   * - recursive_contribute_role
     - recursive_contribute_role
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - browsing_group
     - browsing_group
     - TEXT
     - False
     - False
     - None
     - 
   * - recursive_browsing_group
     - recursive_browsing_group
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - contribute_group
     - contribute_group
     - TEXT
     - False
     - False
     - None
     - 
   * - recursive_contribute_group
     - recursive_contribute_group
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - owner_user_id
     - owner_user_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - item_custom_sort
     - item_custom_sort
     - JSONB
     - False
     - False
     - None
     - 
   * - biblio_flag
     - biblio_flag
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - online_issn
     - online_issn
     - TEXT
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uix_position (parent, position)

index_style
-----------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - VARCHAR(100)
     - True
     - True
     - None
     - 
   * - width
     - width
     - TEXT
     - True
     - False
     - None
     - 
   * - height
     - height
     - TEXT
     - True
     - False
     - None
     - 
   * - index_link_enabled
     - index_link_enabled
     - BOOLEAN
     - True
     - False
     - None
     - 

institution_name
----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('institution_name_id_seq'::regclass)
     - 
   * - institution_name
     - institution_name
     - VARCHAR(255)
     - False
     - False
     - None
     - 

item_metadata
-------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - UUID
     - True
     - True
     - None
     - 
   * - item_type_id
     - item_type_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - json
     - json
     - JSONB
     - False
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - True
     - False
     - None
     - 

item_metadata_version
---------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - id
     - id
     - UUID
     - True
     - True
     - None
     - 
   * - item_type_id
     - item_type_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - json
     - json
     - JSONB
     - False
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - transaction_id
     - transaction_id
     - BIGINT
     - True
     - True
     - None
     - 
   * - end_transaction_id
     - end_transaction_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - operation_type
     - operation_type
     - SMALLINT
     - True
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_item_metadata_version_end_transaction_id (end_transaction_id)
* KEY: ix_item_metadata_version_operation_type (operation_type)
* KEY: ix_item_metadata_version_transaction_id (transaction_id)

item_reference
--------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - src_item_pid
     - src_item_pid
     - VARCHAR(255)
     - True
     - True
     - None
     - 
   * - dst_item_pid
     - dst_item_pid
     - VARCHAR(255)
     - True
     - True
     - None
     - 
   * - reference_type
     - reference_type
     - VARCHAR(50)
     - True
     - False
     - None
     - 

item_type
---------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('item_type_id_seq'::regclass)
     - 
   * - name_id
     - name_id
     - INTEGER
     - True
     - False
     - None
     - FK: item_type_name.id
   * - harvesting_type
     - harvesting_type
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - schema
     - schema
     - JSONB
     - False
     - False
     - None
     - 
   * - form
     - form
     - JSONB
     - False
     - False
     - None
     - 
   * - render
     - render
     - JSONB
     - False
     - False
     - None
     - 
   * - tag
     - tag
     - INTEGER
     - True
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - True
     - False
     - None
     - 
   * - is_deleted
     - is_deleted
     - BOOLEAN
     - True
     - False
     - None
     - 

item_type_edit_history
----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('item_type_edit_history_id_seq'::regclass)
     - 
   * - item_type_id
     - item_type_id
     - INTEGER
     - True
     - False
     - None
     - FK: item_type.id
   * - user_id
     - user_id
     - INTEGER
     - True
     - False
     - None
     - FK: accounts_user.id
   * - notes
     - notes
     - JSONB
     - False
     - False
     - None
     - 

item_type_mapping
-----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('item_type_mapping_id_seq'::regclass)
     - 
   * - item_type_id
     - item_type_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - mapping
     - mapping
     - JSONB
     - False
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - True
     - False
     - None
     - 

item_type_mapping_version
-------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - None
     - 
   * - item_type_id
     - item_type_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - mapping
     - mapping
     - JSONB
     - False
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - transaction_id
     - transaction_id
     - BIGINT
     - True
     - True
     - None
     - 
   * - end_transaction_id
     - end_transaction_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - operation_type
     - operation_type
     - SMALLINT
     - True
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_item_type_mapping_version_end_transaction_id (end_transaction_id)
* KEY: ix_item_type_mapping_version_operation_type (operation_type)
* KEY: ix_item_type_mapping_version_transaction_id (transaction_id)

item_type_name
--------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('item_type_name_id_seq'::regclass)
     - 
   * - name
     - name
     - TEXT
     - True
     - False
     - None
     - 
   * - has_site_license
     - has_site_license
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - is_active
     - is_active
     - BOOLEAN
     - True
     - False
     - true
     - 

Keys
^^^^

* UNIQUE KEY: uq_item_type_name_name (name)

item_type_property
------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('item_type_property_id_seq'::regclass)
     - 
   * - name
     - name
     - TEXT
     - True
     - False
     - None
     - 
   * - schema
     - schema
     - JSONB
     - False
     - False
     - None
     - 
   * - form
     - form
     - JSONB
     - False
     - False
     - None
     - 
   * - forms
     - forms
     - JSONB
     - False
     - False
     - None
     - 
   * - delflg
     - delflg
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - sort
     - sort
     - INTEGER
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_item_type_property_name (name)

item_type_version
-----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - None
     - 
   * - name_id
     - name_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - harvesting_type
     - harvesting_type
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - schema
     - schema
     - JSONB
     - False
     - False
     - None
     - 
   * - form
     - form
     - JSONB
     - False
     - False
     - None
     - 
   * - render
     - render
     - JSONB
     - False
     - False
     - None
     - 
   * - tag
     - tag
     - INTEGER
     - False
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - is_deleted
     - is_deleted
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - transaction_id
     - transaction_id
     - BIGINT
     - True
     - True
     - None
     - 
   * - end_transaction_id
     - end_transaction_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - operation_type
     - operation_type
     - SMALLINT
     - True
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_item_type_version_end_transaction_id (end_transaction_id)
* KEY: ix_item_type_version_operation_type (operation_type)
* KEY: ix_item_type_version_transaction_id (transaction_id)

journal
-------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - BIGINT
     - True
     - True
     - nextval('journal_id_seq'::regclass)
     - 
   * - index_id
     - index_id
     - BIGINT
     - True
     - False
     - None
     - FK: index.id
   * - publication_title
     - publication_title
     - TEXT
     - False
     - False
     - None
     - 
   * - print_identifier
     - print_identifier
     - TEXT
     - False
     - False
     - None
     - 
   * - online_identifier
     - online_identifier
     - TEXT
     - False
     - False
     - None
     - 
   * - date_first_issue_online
     - date_first_issue_online
     - TEXT
     - False
     - False
     - None
     - 
   * - num_first_vol_online
     - num_first_vol_online
     - TEXT
     - False
     - False
     - None
     - 
   * - num_first_issue_online
     - num_first_issue_online
     - TEXT
     - False
     - False
     - None
     - 
   * - date_last_issue_online
     - date_last_issue_online
     - TEXT
     - False
     - False
     - None
     - 
   * - num_last_vol_online
     - num_last_vol_online
     - TEXT
     - False
     - False
     - None
     - 
   * - num_last_issue_online
     - num_last_issue_online
     - TEXT
     - False
     - False
     - None
     - 
   * - title_url
     - title_url
     - TEXT
     - False
     - False
     - None
     - 
   * - first_author
     - first_author
     - TEXT
     - False
     - False
     - None
     - 
   * - title_id
     - title_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - embargo_info
     - embargo_info
     - TEXT
     - False
     - False
     - None
     - 
   * - coverage_depth
     - coverage_depth
     - TEXT
     - False
     - False
     - None
     - 
   * - coverage_notes
     - coverage_notes
     - TEXT
     - False
     - False
     - None
     - 
   * - publisher_name
     - publisher_name
     - TEXT
     - False
     - False
     - None
     - 
   * - publication_type
     - publication_type
     - TEXT
     - False
     - False
     - None
     - 
   * - date_monograph_published_print
     - date_monograph_published_print
     - TEXT
     - False
     - False
     - None
     - 
   * - date_monograph_published_online
     - date_monograph_published_online
     - TEXT
     - False
     - False
     - None
     - 
   * - monograph_volume
     - monograph_volume
     - TEXT
     - False
     - False
     - None
     - 
   * - monograph_edition
     - monograph_edition
     - TEXT
     - False
     - False
     - None
     - 
   * - first_editor
     - first_editor
     - TEXT
     - False
     - False
     - None
     - 
   * - parent_publication_title_id
     - parent_publication_title_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - preceding_publication_title_id
     - preceding_publication_title_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - access_type
     - access_type
     - TEXT
     - False
     - False
     - None
     - 
   * - language
     - language
     - TEXT
     - False
     - False
     - None
     - 
   * - title_alternative
     - title_alternative
     - TEXT
     - False
     - False
     - None
     - 
   * - title_transcription
     - title_transcription
     - TEXT
     - False
     - False
     - None
     - 
   * - ncid
     - ncid
     - TEXT
     - False
     - False
     - None
     - 
   * - ndl_callno
     - ndl_callno
     - TEXT
     - False
     - False
     - None
     - 
   * - ndl_bibid
     - ndl_bibid
     - TEXT
     - False
     - False
     - None
     - 
   * - jstage_code
     - jstage_code
     - TEXT
     - False
     - False
     - None
     - 
   * - ichushi_code
     - ichushi_code
     - TEXT
     - False
     - False
     - None
     - 
   * - deleted
     - deleted
     - TEXT
     - False
     - False
     - None
     - 
   * - is_output
     - is_output
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - owner_user_id
     - owner_user_id
     - INTEGER
     - False
     - False
     - None
     - 

journal_export_processing
-------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - BIGINT
     - True
     - True
     - nextval('journal_export_processing_id_seq'::regclass)
     - 
   * - start_time
     - start_time
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - end_time
     - end_time
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - status
     - status
     - BOOLEAN
     - False
     - False
     - None
     - 

loganalysis_restricted_crawler_list
-----------------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('loganalysis_restricted_crawler_list_id_seq'::regclass)
     - 
   * - list_url
     - list_url
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - is_active
     - is_active
     - BOOLEAN
     - False
     - False
     - None
     - 

loganalysis_restricted_ip_address
---------------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('loganalysis_restricted_ip_address_id_seq'::regclass)
     - 
   * - ip_address
     - ip_address
     - VARCHAR(16)
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_loganalysis_restricted_ip_address_ip_address (ip_address)

mail_config
-----------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('mail_config_id_seq'::regclass)
     - 
   * - mail_server
     - mail_server
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - mail_port
     - mail_port
     - INTEGER
     - False
     - False
     - None
     - 
   * - mail_use_tls
     - mail_use_tls
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - mail_use_ssl
     - mail_use_ssl
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - mail_username
     - mail_username
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - mail_password
     - mail_password
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - mail_default_sender
     - mail_default_sender
     - VARCHAR(255)
     - False
     - False
     - None
     - 

oaiharvester_configs
--------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('oaiharvester_configs_id_seq'::regclass)
     - 
   * - baseurl
     - baseurl
     - VARCHAR(255)
     - True
     - False
     - ''::character varying
     - 
   * - metadataprefix
     - metadataprefix
     - VARCHAR(255)
     - True
     - False
     - 'oai_dc'::character varying
     - 
   * - comment
     - comment
     - TEXT
     - False
     - False
     - None
     - 
   * - name
     - name
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - lastrun
     - lastrun
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - setspecs
     - setspecs
     - TEXT
     - True
     - False
     - None
     - 

oaiserver_identify
------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('oaiserver_identify_id_seq'::regclass)
     - 
   * - outPutSetting
     - outPutSetting
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - emails
     - emails
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - repositoryName
     - repositoryName
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - earliestDatastamp
     - earliestDatastamp
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_oaiserver_identify_emails (emails)
* UNIQUE KEY: uq_oaiserver_identify_outPutSetting (outPutSetting)

oaiserver_schema
----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - UUID
     - True
     - True
     - None
     - 
   * - schema_name
     - schema_name
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - form_data
     - form_data
     - JSONB
     - False
     - False
     - None
     - 
   * - xsd
     - xsd
     - JSONB
     - True
     - False
     - None
     - 
   * - namespaces
     - namespaces
     - JSONB
     - False
     - False
     - None
     - 
   * - schema_location
     - schema_location
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - isvalid
     - isvalid
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - is_mapping
     - is_mapping
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - isfixed
     - isfixed
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - True
     - False
     - None
     - 
   * - target_namespace
     - target_namespace
     - VARCHAR(255)
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_oaiserver_schema_schema_name (schema_name)

oaiserver_schema_version
------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - id
     - id
     - UUID
     - True
     - True
     - None
     - 
   * - schema_name
     - schema_name
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - form_data
     - form_data
     - JSONB
     - False
     - False
     - None
     - 
   * - xsd
     - xsd
     - JSONB
     - False
     - False
     - None
     - 
   * - namespaces
     - namespaces
     - JSONB
     - False
     - False
     - None
     - 
   * - schema_location
     - schema_location
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - isvalid
     - isvalid
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - is_mapping
     - is_mapping
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - isfixed
     - isfixed
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - target_namespace
     - target_namespace
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - transaction_id
     - transaction_id
     - BIGINT
     - True
     - True
     - None
     - 
   * - end_transaction_id
     - end_transaction_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - operation_type
     - operation_type
     - SMALLINT
     - True
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_oaiserver_schema_version_end_transaction_id (end_transaction_id)
* KEY: ix_oaiserver_schema_version_operation_type (operation_type)
* KEY: ix_oaiserver_schema_version_transaction_id (transaction_id)

oaiserver_set
-------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - BIGINT
     - True
     - True
     - nextval('oaiserver_set_id_seq'::regclass)
     - 
   * - spec
     - spec
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - name
     - name
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - description
     - description
     - TEXT
     - False
     - False
     - None
     - 
   * - search_pattern
     - search_pattern
     - TEXT
     - False
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_oaiserver_set_name (name)
* UNIQUE KEY: uq_oaiserver_set_spec (spec)

oauth2server_client
-------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - name
     - name
     - VARCHAR(40)
     - False
     - False
     - None
     - 
   * - description
     - description
     - TEXT
     - False
     - False
     - None
     - 
   * - website
     - website
     - TEXT
     - False
     - False
     - None
     - 
   * - user_id
     - user_id
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - client_id
     - client_id
     - VARCHAR(255)
     - True
     - True
     - None
     - 
   * - client_secret
     - client_secret
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - is_confidential
     - is_confidential
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - is_internal
     - is_internal
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - _redirect_uris
     - _redirect_uris
     - TEXT
     - False
     - False
     - None
     - 
   * - _default_scopes
     - _default_scopes
     - TEXT
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: ix_oauth2server_client_client_secret (client_secret)
* KEY: ix_oauth2server_client_user_id (user_id)

oauth2server_token
------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('oauth2server_token_id_seq'::regclass)
     - 
   * - client_id
     - client_id
     - VARCHAR(255)
     - True
     - False
     - None
     - FK: oauth2server_client.client_id
   * - user_id
     - user_id
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - token_type
     - token_type
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - access_token
     - access_token
     - BYTEA
     - False
     - False
     - None
     - 
   * - refresh_token
     - refresh_token
     - BYTEA
     - False
     - False
     - None
     - 
   * - expires
     - expires
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - _scopes
     - _scopes
     - TEXT
     - False
     - False
     - None
     - 
   * - is_personal
     - is_personal
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - is_internal
     - is_internal
     - BOOLEAN
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: ix_oauth2server_token_access_token (access_token)
* KEY: ix_oauth2server_token_client_id (client_id)
* UNIQUE KEY: ix_oauth2server_token_refresh_token (refresh_token)
* KEY: ix_oauth2server_token_user_id (user_id)

oauthclient_remoteaccount
-------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('oauthclient_remoteaccount_id_seq'::regclass)
     - 
   * - user_id
     - user_id
     - INTEGER
     - True
     - False
     - None
     - FK: accounts_user.id
   * - client_id
     - client_id
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - extra_data
     - extra_data
     - JSON
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_oauthclient_remoteaccount_user_id (user_id, client_id)

oauthclient_remotetoken
-----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id_remote_account
     - id_remote_account
     - INTEGER
     - True
     - True
     - None
     - FK: oauthclient_remoteaccount.id
   * - token_type
     - token_type
     - VARCHAR(40)
     - True
     - True
     - None
     - 
   * - access_token
     - access_token
     - BYTEA
     - True
     - False
     - None
     - 
   * - secret
     - secret
     - TEXT
     - True
     - False
     - None
     - 

oauthclient_useridentity
------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - VARCHAR(255)
     - True
     - True
     - None
     - 
   * - method
     - method
     - VARCHAR(255)
     - True
     - True
     - None
     - 
   * - id_user
     - id_user
     - INTEGER
     - True
     - False
     - None
     - FK: accounts_user.id

Keys
^^^^

* UNIQUE KEY: useridentity_id_user_method (id_user, method)

pdfcoverpage_set
----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('pdfcoverpage_set_id_seq'::regclass)
     - 
   * - avail
     - avail
     - TEXT
     - False
     - False
     - None
     - 
   * - header_display_type
     - header_display_type
     - TEXT
     - False
     - False
     - None
     - 
   * - header_output_string
     - header_output_string
     - TEXT
     - False
     - False
     - None
     - 
   * - header_output_image
     - header_output_image
     - TEXT
     - False
     - False
     - None
     - 
   * - header_display_position
     - header_display_position
     - TEXT
     - False
     - False
     - None
     - 
   * - created_at
     - created_at
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated_at
     - updated_at
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 

pidrelations_pidrelation
------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - parent_id
     - parent_id
     - INTEGER
     - True
     - True
     - None
     - FK: pidstore_pid.id
   * - child_id
     - child_id
     - INTEGER
     - True
     - True
     - None
     - FK: pidstore_pid.id
   * - relation_type
     - relation_type
     - SMALLINT
     - True
     - False
     - None
     - 
   * - index
     - index
     - INTEGER
     - False
     - False
     - None
     - 

pidstore_pid
------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('pidstore_pid_id_seq'::regclass)
     - 
   * - pid_type
     - pid_type
     - VARCHAR(6)
     - True
     - False
     - None
     - 
   * - pid_value
     - pid_value
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - pid_provider
     - pid_provider
     - VARCHAR(8)
     - False
     - False
     - None
     - 
   * - status
     - status
     - CHAR(1)
     - True
     - False
     - None
     - 
   * - object_type
     - object_type
     - VARCHAR(3)
     - False
     - False
     - None
     - 
   * - object_uuid
     - object_uuid
     - UUID
     - False
     - False
     - None
     - 

Keys
^^^^

* KEY: idx_object (object_type, object_uuid)
* KEY: idx_status (status)
* UNIQUE KEY: uidx_type_pid (pid_type, pid_value)

pidstore_recid
--------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - recid
     - recid
     - BIGINT
     - True
     - True
     - nextval('pidstore_recid_recid_seq'::regclass)
     - 

pidstore_redirect
-----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - UUID
     - True
     - True
     - None
     - 
   * - pid_id
     - pid_id
     - INTEGER
     - True
     - False
     - None
     - FK: pidstore_pid.id

ranking_settings
----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('ranking_settings_id_seq'::regclass)
     - 
   * - is_show
     - is_show
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - new_item_period
     - new_item_period
     - INTEGER
     - True
     - False
     - None
     - 
   * - statistical_period
     - statistical_period
     - INTEGER
     - True
     - False
     - None
     - 
   * - display_rank
     - display_rank
     - INTEGER
     - True
     - False
     - None
     - 
   * - rankings
     - rankings
     - JSONB
     - False
     - False
     - None
     - 

records_buckets
---------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - record_id
     - record_id
     - UUID
     - True
     - True
     - None
     - FK: records_metadata.id
   * - bucket_id
     - bucket_id
     - UUID
     - True
     - True
     - None
     - FK: files_bucket.id

records_metadata
----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - UUID
     - True
     - True
     - None
     - 
   * - json
     - json
     - JSONB
     - False
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - True
     - False
     - None
     - 

records_metadata_version
------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - id
     - id
     - UUID
     - True
     - True
     - None
     - 
   * - json
     - json
     - JSONB
     - False
     - False
     - None
     - 
   * - version_id
     - version_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - transaction_id
     - transaction_id
     - BIGINT
     - True
     - True
     - None
     - 
   * - end_transaction_id
     - end_transaction_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - operation_type
     - operation_type
     - SMALLINT
     - True
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_records_metadata_version_end_transaction_id (end_transaction_id)
* KEY: ix_records_metadata_version_operation_type (operation_type)
* KEY: ix_records_metadata_version_transaction_id (transaction_id)

resourcelist_indexes
--------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('resourcelist_indexes_id_seq'::regclass)
     - 
   * - status
     - status
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - repository_id
     - repository_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - resource_dump_manifest
     - resource_dump_manifest
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - url_path
     - url_path
     - VARCHAR(255)
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_resourcelist_indexes_repository_id (repository_id)

resync_indexes
--------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('resync_indexes_id_seq'::regclass)
     - 
   * - status
     - status
     - VARCHAR
     - True
     - False
     - None
     - 
   * - index_id
     - index_id
     - BIGINT
     - False
     - False
     - None
     - FK: index.id
   * - repository_name
     - repository_name
     - VARCHAR(50)
     - True
     - False
     - None
     - 
   * - from_date
     - from_date
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - to_date
     - to_date
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - resync_save_dir
     - resync_save_dir
     - VARCHAR(50)
     - True
     - False
     - None
     - 
   * - resync_mode
     - resync_mode
     - VARCHAR(20)
     - True
     - False
     - None
     - 
   * - saving_format
     - saving_format
     - VARCHAR(10)
     - True
     - False
     - None
     - 
   * - base_url
     - base_url
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - is_running
     - is_running
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - interval_by_day
     - interval_by_day
     - INTEGER
     - True
     - False
     - None
     - 
   * - task_id
     - task_id
     - VARCHAR(40)
     - False
     - False
     - None
     - 
   * - result
     - result
     - JSONB
     - False
     - False
     - None
     - 

resync_logs
-----------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('resync_logs_id_seq'::regclass)
     - 
   * - resync_indexes_id
     - resync_indexes_id
     - INTEGER
     - False
     - False
     - None
     - FK: resync_indexes.id
   * - log_type
     - log_type
     - VARCHAR(10)
     - False
     - False
     - None
     - 
   * - task_id
     - task_id
     - VARCHAR(40)
     - False
     - False
     - None
     - 
   * - start_time
     - start_time
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - end_time
     - end_time
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - status
     - status
     - VARCHAR(10)
     - True
     - False
     - None
     - 
   * - errmsg
     - errmsg
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - counter
     - counter
     - JSONB
     - False
     - False
     - None
     - 

search_management
-----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('search_management_id_seq'::regclass)
     - 
   * - default_dis_num
     - default_dis_num
     - INTEGER
     - True
     - False
     - None
     - 
   * - default_dis_sort_index
     - default_dis_sort_index
     - TEXT
     - False
     - False
     - None
     - 
   * - default_dis_sort_keyword
     - default_dis_sort_keyword
     - TEXT
     - False
     - False
     - None
     - 
   * - sort_setting
     - sort_setting
     - JSONB
     - False
     - False
     - None
     - 
   * - search_conditions
     - search_conditions
     - JSONB
     - False
     - False
     - None
     - 
   * - search_setting_all
     - search_setting_all
     - JSONB
     - False
     - False
     - None
     - 
   * - display_control
     - display_control
     - JSONB
     - False
     - False
     - None
     - 
   * - init_disp_setting
     - init_disp_setting
     - JSONB
     - False
     - False
     - None
     - 
   * - create_date
     - create_date
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 

session_lifetime
----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('session_lifetime_id_seq'::regclass)
     - 
   * - lifetime
     - lifetime
     - INTEGER
     - True
     - False
     - None
     - 
   * - create_date
     - create_date
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - is_delete
     - is_delete
     - BOOLEAN
     - True
     - False
     - None
     - 

shibboleth_user
---------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('shibboleth_user_id_seq'::regclass)
     - 
   * - shib_eppn
     - shib_eppn
     - VARCHAR(2310)
     - True
     - False
     - None
     - 
   * - weko_uid
     - weko_uid
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - shib_handle
     - shib_handle
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - shib_role_authority_name
     - shib_role_authority_name
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - shib_page_name
     - shib_page_name
     - VARCHAR(1024)
     - False
     - False
     - None
     - 
   * - shib_active_flag
     - shib_active_flag
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - shib_mail
     - shib_mail
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - shib_user_name
     - shib_user_name
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - shib_ip_range_flag
     - shib_ip_range_flag
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - shib_organization
     - shib_organization
     - VARCHAR(255)
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_shibboleth_user_shib_eppn (shib_eppn)
* UNIQUE KEY: uq_shibboleth_user_shib_user_name (shib_user_name)

shibboleth_userrole
-------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - shib_user_id
     - shib_user_id
     - INTEGER
     - False
     - False
     - None
     - FK: shibboleth_user.id
   * - role_id
     - role_id
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_role.id

site_info
---------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('site_info_id_seq'::regclass)
     - 
   * - copy_right
     - copy_right
     - TEXT
     - False
     - False
     - None
     - 
   * - description
     - description
     - TEXT
     - False
     - False
     - None
     - 
   * - keyword
     - keyword
     - TEXT
     - False
     - False
     - None
     - 
   * - favicon
     - favicon
     - TEXT
     - False
     - False
     - None
     - 
   * - favicon_name
     - favicon_name
     - TEXT
     - False
     - False
     - None
     - 
   * - site_name
     - site_name
     - JSONB
     - True
     - False
     - None
     - 
   * - notify
     - notify
     - JSONB
     - True
     - False
     - None
     - 
   * - google_tracking_id_user
     - google_tracking_id_user
     - TEXT
     - False
     - False
     - None
     - 
   * - addthis_user_id
     - addthis_user_id
     - TEXT
     - False
     - False
     - None
     - 
   * - ogp_image
     - ogp_image
     - TEXT
     - False
     - False
     - None
     - 
   * - ogp_image_name
     - ogp_image_name
     - TEXT
     - False
     - False
     - None
     - 

sitelicense_info
----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - organization_id
     - organization_id
     - INTEGER
     - True
     - True
     - nextval('sitelicense_info_organization_id_seq'::regclass)
     - 
   * - organization_name
     - organization_name
     - TEXT
     - True
     - False
     - None
     - 
   * - domain_name
     - domain_name
     - TEXT
     - False
     - False
     - None
     - 
   * - mail_address
     - mail_address
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - receive_mail_flag
     - receive_mail_flag
     - VARCHAR(1)
     - True
     - False
     - None
     - 

sitelicense_ip_address
----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - organization_id
     - organization_id
     - INTEGER
     - True
     - True
     - None
     - FK: sitelicense_info.organization_id
   * - organization_no
     - organization_no
     - INTEGER
     - True
     - True
     - nextval('sitelicense_ip_address_organization_no_seq'::regclass)
     - 
   * - start_ip_address
     - start_ip_address
     - VARCHAR(16)
     - True
     - False
     - None
     - 
   * - finish_ip_address
     - finish_ip_address
     - VARCHAR(16)
     - True
     - False
     - None
     - 

stats_aggregation
-----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - VARCHAR(100)
     - True
     - True
     - None
     - 
   * - source_id
     - source_id
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - index
     - index
     - VARCHAR(100)
     - True
     - False
     - None
     - 
   * - type
     - type
     - VARCHAR(50)
     - True
     - False
     - None
     - 
   * - source
     - source
     - JSONB
     - False
     - False
     - None
     - 
   * - date
     - date
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_stats_aggregation_date (date)
* UNIQUE KEY: uq_stats_key_stats_aggregation (source_id, index)

stats_bookmark
--------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - VARCHAR(100)
     - True
     - True
     - None
     - 
   * - source_id
     - source_id
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - index
     - index
     - VARCHAR(100)
     - True
     - False
     - None
     - 
   * - type
     - type
     - VARCHAR(50)
     - True
     - False
     - None
     - 
   * - source
     - source
     - JSONB
     - False
     - False
     - None
     - 
   * - date
     - date
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_stats_bookmark_date (date)
* UNIQUE KEY: uq_stats_key_stats_bookmark (source_id, index)

stats_email_address
-------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('stats_email_address_id_seq'::regclass)
     - 
   * - email_address
     - email_address
     - VARCHAR(255)
     - True
     - False
     - None
     - 

stats_events
------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - VARCHAR(100)
     - True
     - True
     - None
     - 
   * - source_id
     - source_id
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - index
     - index
     - VARCHAR(100)
     - True
     - False
     - None
     - 
   * - type
     - type
     - VARCHAR(50)
     - True
     - False
     - None
     - 
   * - source
     - source
     - JSONB
     - False
     - False
     - None
     - 
   * - date
     - date
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_stats_events_date (date)
* UNIQUE KEY: uq_stats_key_stats_events (source_id, index)

stats_report_target
-------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - target_id
     - target_id
     - VARCHAR(100)
     - True
     - True
     - None
     - 
   * - target_name
     - target_name
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - target_unit
     - target_unit
     - VARCHAR(100)
     - False
     - False
     - None
     - 

stats_report_unit
-----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - unit_id
     - unit_id
     - VARCHAR(100)
     - True
     - True
     - None
     - 
   * - unit_name
     - unit_name
     - VARCHAR(255)
     - True
     - False
     - None
     - 

transaction
-----------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - issued_at
     - issued_at
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - id
     - id
     - BIGINT
     - True
     - True
     - None
     - 
   * - remote_addr
     - remote_addr
     - VARCHAR(50)
     - False
     - False
     - None
     - 
   * - user_id
     - user_id
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id

Keys
^^^^

* KEY: ix_transaction_user_id (user_id)

userprofiles_userprofile
------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - user_id
     - user_id
     - INTEGER
     - True
     - True
     - None
     - FK: accounts_user.id
   * - username
     - username
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - displayname
     - displayname
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - fullname
     - fullname
     - VARCHAR(100)
     - True
     - False
     - None
     - 
   * - timezone
     - timezone
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - language
     - language
     - VARCHAR(255)
     - True
     - False
     - None
     - 
   * - university
     - university
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - department
     - department
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - position
     - position
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - otherPosition
     - otherPosition
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - phoneNumber
     - phoneNumber
     - VARCHAR(15)
     - False
     - False
     - None
     - 
   * - instituteName
     - instituteName
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - institutePosition
     - institutePosition
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - instituteName2
     - instituteName2
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - institutePosition2
     - institutePosition2
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - instituteName3
     - instituteName3
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - institutePosition3
     - institutePosition3
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - instituteName4
     - instituteName4
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - institutePosition4
     - institutePosition4
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - instituteName5
     - instituteName5
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - institutePosition5
     - institutePosition5
     - VARCHAR(255)
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_userprofiles_userprofile_username (username)

widget_design_page
------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('widget_design_page_id_seq'::regclass)
     - 
   * - title
     - title
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - repository_id
     - repository_id
     - VARCHAR(100)
     - True
     - False
     - None
     - 
   * - url
     - url
     - VARCHAR(100)
     - True
     - False
     - None
     - 
   * - template_name
     - template_name
     - VARCHAR(100)
     - False
     - False
     - None
     - 
   * - content
     - content
     - TEXT
     - False
     - False
     - None
     - 
   * - settings
     - settings
     - JSONB
     - False
     - False
     - None
     - 
   * - is_main_layout
     - is_main_layout
     - BOOLEAN
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: uq_widget_design_page_url (url)

widget_design_page_multi_lang_data
----------------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('widget_design_page_multi_lang_data_id_seq'::regclass)
     - 
   * - widget_design_page_id
     - widget_design_page_id
     - INTEGER
     - True
     - False
     - None
     - FK: widget_design_page.id
   * - lang_code
     - lang_code
     - VARCHAR(3)
     - True
     - False
     - None
     - 
   * - title
     - title
     - VARCHAR(100)
     - False
     - False
     - None
     - 

widget_design_setting
---------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - repository_id
     - repository_id
     - VARCHAR(100)
     - True
     - True
     - None
     - 
   * - settings
     - settings
     - JSONB
     - False
     - False
     - None
     - 

widget_items
------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - widget_id
     - widget_id
     - INTEGER
     - True
     - True
     - nextval('widget_items_widget_id_seq'::regclass)
     - 
   * - repository_id
     - repository_id
     - VARCHAR(100)
     - True
     - False
     - None
     - 
   * - widget_type
     - widget_type
     - VARCHAR(100)
     - True
     - False
     - None
     - 
   * - settings
     - settings
     - JSONB
     - False
     - False
     - None
     - 
   * - is_enabled
     - is_enabled
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - is_deleted
     - is_deleted
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - locked
     - locked
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - locked_by_user
     - locked_by_user
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id

widget_multi_lang_data
----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('widget_multi_lang_data_id_seq'::regclass)
     - 
   * - widget_id
     - widget_id
     - INTEGER
     - True
     - False
     - None
     - 
   * - lang_code
     - lang_code
     - VARCHAR(3)
     - True
     - False
     - None
     - 
   * - label
     - label
     - VARCHAR(100)
     - True
     - False
     - None
     - 
   * - description_data
     - description_data
     - JSONB
     - False
     - False
     - None
     - 
   * - is_deleted
     - is_deleted
     - BOOLEAN
     - False
     - False
     - None
     - 

widget_type
-----------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - type_id
     - type_id
     - VARCHAR(100)
     - True
     - True
     - None
     - 
   * - type_name
     - type_name
     - VARCHAR(100)
     - True
     - False
     - None
     - 

workflow_action
---------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_action_id_seq'::regclass)
     - 
   * - action_name
     - action_name
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - action_desc
     - action_desc
     - TEXT
     - False
     - False
     - None
     - 
   * - action_endpoint
     - action_endpoint
     - VARCHAR(24)
     - False
     - False
     - None
     - 
   * - action_version
     - action_version
     - VARCHAR(64)
     - False
     - False
     - None
     - 
   * - action_makedate
     - action_makedate
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - action_lastdate
     - action_lastdate
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - action_is_need_agree
     - action_is_need_agree
     - BOOLEAN
     - False
     - False
     - None
     - 

workflow_action_feedbackmail
----------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_action_feedbackmail_id_seq'::regclass)
     - 
   * - activity_id
     - activity_id
     - VARCHAR(24)
     - True
     - False
     - None
     - 
   * - action_id
     - action_id
     - INTEGER
     - False
     - False
     - None
     - FK: workflow_action.id
   * - feedback_maillist
     - feedback_maillist
     - JSONB
     - False
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_workflow_action_feedbackmail_activity_id (activity_id)

workflow_action_history
-----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_action_history_id_seq'::regclass)
     - 
   * - activity_id
     - activity_id
     - VARCHAR(24)
     - True
     - False
     - None
     - 
   * - action_id
     - action_id
     - INTEGER
     - True
     - False
     - None
     - 
   * - action_version
     - action_version
     - VARCHAR(24)
     - False
     - False
     - None
     - 
   * - action_status
     - action_status
     - VARCHAR(1)
     - False
     - False
     - None
     - FK: workflow_action_status.action_status_id
   * - action_user
     - action_user
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - action_date
     - action_date
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - action_comment
     - action_comment
     - TEXT
     - False
     - False
     - None
     - 
   * - action_order
     - action_order
     - INTEGER
     - False
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_workflow_action_history_activity_id (activity_id)

workflow_action_identifier
--------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_action_identifier_id_seq'::regclass)
     - 
   * - activity_id
     - activity_id
     - VARCHAR(24)
     - True
     - False
     - None
     - 
   * - action_id
     - action_id
     - INTEGER
     - False
     - False
     - None
     - FK: workflow_action.id
   * - action_identifier_select
     - action_identifier_select
     - INTEGER
     - False
     - False
     - None
     - 
   * - action_identifier_jalc_doi
     - action_identifier_jalc_doi
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - action_identifier_jalc_cr_doi
     - action_identifier_jalc_cr_doi
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - action_identifier_jalc_dc_doi
     - action_identifier_jalc_dc_doi
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - action_identifier_ndl_jalc_doi
     - action_identifier_ndl_jalc_doi
     - VARCHAR(255)
     - False
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_workflow_action_identifier_activity_id (activity_id)

workflow_action_journal
-----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_action_journal_id_seq'::regclass)
     - 
   * - activity_id
     - activity_id
     - VARCHAR(24)
     - True
     - False
     - None
     - 
   * - action_id
     - action_id
     - INTEGER
     - False
     - False
     - None
     - FK: workflow_action.id
   * - action_journal
     - action_journal
     - JSONB
     - False
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_workflow_action_journal_activity_id (activity_id)

workflow_action_status
----------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_action_status_id_seq'::regclass)
     - 
   * - action_status_id
     - action_status_id
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - action_status_name
     - action_status_name
     - VARCHAR(32)
     - False
     - False
     - None
     - 
   * - action_status_desc
     - action_status_desc
     - TEXT
     - False
     - False
     - None
     - 
   * - action_scopes
     - action_scopes
     - VARCHAR(64)
     - False
     - False
     - None
     - 
   * - action_displays
     - action_displays
     - TEXT
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: ix_workflow_action_status_action_status_id (action_status_id)

workflow_activity
-----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_activity_id_seq'::regclass)
     - 
   * - activity_id
     - activity_id
     - VARCHAR(24)
     - True
     - False
     - None
     - 
   * - activity_name
     - activity_name
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - item_id
     - item_id
     - UUID
     - False
     - False
     - None
     - 
   * - workflow_id
     - workflow_id
     - INTEGER
     - True
     - False
     - None
     - FK: workflow_workflow.id
   * - workflow_status
     - workflow_status
     - INTEGER
     - False
     - False
     - None
     - 
   * - flow_id
     - flow_id
     - INTEGER
     - False
     - False
     - None
     - FK: workflow_flow_define.id
   * - action_id
     - action_id
     - INTEGER
     - False
     - False
     - None
     - FK: workflow_action.id
   * - action_status
     - action_status
     - VARCHAR(1)
     - False
     - False
     - None
     - FK: workflow_action_status.action_status_id
   * - activity_login_user
     - activity_login_user
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - activity_update_user
     - activity_update_user
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - activity_status
     - activity_status
     - VARCHAR(1)
     - False
     - False
     - None
     - 
   * - activity_start
     - activity_start
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - activity_end
     - activity_end
     - TIMESTAMP WITHOUT TIME ZONE
     - False
     - False
     - None
     - 
   * - activity_community_id
     - activity_community_id
     - TEXT
     - False
     - False
     - None
     - 
   * - activity_confirm_term_of_use
     - activity_confirm_term_of_use
     - BOOLEAN
     - False
     - False
     - None
     - 
   * - title
     - title
     - TEXT
     - False
     - False
     - None
     - 
   * - shared_user_id
     - shared_user_id
     - INTEGER
     - False
     - False
     - None
     - 
   * - temp_data
     - temp_data
     - JSONB
     - False
     - False
     - None
     - 
   * - approval1
     - approval1
     - TEXT
     - False
     - False
     - None
     - 
   * - approval2
     - approval2
     - TEXT
     - False
     - False
     - None
     - 
   * - extra_info
     - extra_info
     - JSONB
     - False
     - False
     - None
     - 
   * - action_order
     - action_order
     - INTEGER
     - False
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: ix_workflow_activity_activity_id (activity_id)
* KEY: ix_workflow_activity_item_id (item_id)

workflow_activity_action
------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_activity_action_id_seq'::regclass)
     - 
   * - activity_id
     - activity_id
     - VARCHAR(24)
     - True
     - False
     - None
     - FK: workflow_activity.activity_id
   * - action_id
     - action_id
     - INTEGER
     - False
     - False
     - None
     - FK: workflow_action.id
   * - action_status
     - action_status
     - VARCHAR(1)
     - True
     - False
     - None
     - FK: workflow_action_status.action_status_id
   * - action_comment
     - action_comment
     - TEXT
     - False
     - False
     - None
     - 
   * - action_handler
     - action_handler
     - INTEGER
     - False
     - False
     - None
     - 
   * - action_order
     - action_order
     - INTEGER
     - False
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_workflow_activity_action_activity_id (activity_id)

workflow_flow_action
--------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_flow_action_id_seq'::regclass)
     - 
   * - flow_id
     - flow_id
     - UUID
     - True
     - False
     - None
     - FK: workflow_flow_define.flow_id
   * - action_id
     - action_id
     - INTEGER
     - True
     - False
     - None
     - FK: workflow_action.id
   * - action_version
     - action_version
     - VARCHAR(64)
     - False
     - False
     - None
     - 
   * - action_order
     - action_order
     - INTEGER
     - True
     - False
     - None
     - 
   * - action_condition
     - action_condition
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - action_status
     - action_status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - action_date
     - action_date
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - send_mail_setting
     - send_mail_setting
     - JSONB
     - False
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_workflow_flow_action_flow_id (flow_id)

workflow_flow_action_role
-------------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_flow_action_role_id_seq'::regclass)
     - 
   * - flow_action_id
     - flow_action_id
     - INTEGER
     - True
     - False
     - None
     - FK: workflow_flow_action.id
   * - action_role
     - action_role
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_role.id
   * - action_role_exclude
     - action_role_exclude
     - BOOLEAN
     - True
     - False
     - false
     - 
   * - action_user
     - action_user
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - action_user_exclude
     - action_user_exclude
     - BOOLEAN
     - True
     - False
     - false
     - 
   * - specify_property
     - specify_property
     - VARCHAR(255)
     - False
     - False
     - None
     - 

Keys
^^^^

* KEY: ix_workflow_flow_action_role_flow_action_id (flow_action_id)

workflow_flow_define
--------------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_flow_define_id_seq'::regclass)
     - 
   * - flow_id
     - flow_id
     - UUID
     - True
     - False
     - None
     - 
   * - flow_name
     - flow_name
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - flow_user
     - flow_user
     - INTEGER
     - False
     - False
     - None
     - FK: accounts_user.id
   * - flow_status
     - flow_status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - is_deleted
     - is_deleted
     - BOOLEAN
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: ix_workflow_flow_define_flow_id (flow_id)
* UNIQUE KEY: ix_workflow_flow_define_flow_name (flow_name)

workflow_userrole
-----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - workflow_id
     - workflow_id
     - INTEGER
     - True
     - True
     - None
     - FK: workflow_workflow.id
   * - role_id
     - role_id
     - INTEGER
     - True
     - True
     - None
     - FK: accounts_role.id

workflow_workflow
-----------------

.. list-table::
   :header-rows: 1

   * - Fullname
     - Name
     - Type
     - NOT NULL
     - PKey
     - Default
     - Comment
   * - status
     - status
     - VARCHAR(1)
     - True
     - False
     - None
     - 
   * - created
     - created
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - updated
     - updated
     - TIMESTAMP WITHOUT TIME ZONE
     - True
     - False
     - None
     - 
   * - id
     - id
     - INTEGER
     - True
     - True
     - nextval('workflow_workflow_id_seq'::regclass)
     - 
   * - flows_id
     - flows_id
     - UUID
     - True
     - False
     - None
     - 
   * - flows_name
     - flows_name
     - VARCHAR(255)
     - False
     - False
     - None
     - 
   * - itemtype_id
     - itemtype_id
     - INTEGER
     - True
     - False
     - None
     - FK: item_type.id
   * - index_tree_id
     - index_tree_id
     - BIGINT
     - False
     - False
     - None
     - 
   * - flow_id
     - flow_id
     - INTEGER
     - True
     - False
     - None
     - FK: workflow_flow_define.id
   * - is_deleted
     - is_deleted
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - open_restricted
     - open_restricted
     - BOOLEAN
     - True
     - False
     - None
     - 
   * - is_gakuninrdm
     - is_gakuninrdm
     - BOOLEAN
     - True
     - False
     - None
     - 

Keys
^^^^

* UNIQUE KEY: ix_workflow_workflow_flows_id (flows_id)
