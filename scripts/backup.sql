-- テーブルバックアップ
create table oaiserver_set_bk as select * from oaiserver_set;

create table pidrelations_pidrelation_bk as select * from pidrelations_pidrelation;

create table access_actionsroles_bk as select * from access_actionsroles;

create table accounts_userrole_bk as select * from accounts_userrole;

create table accounts_role_bk as select * from accounts_role;

create table accounts_user_bk as select * from accounts_user;

create table oauthclient_useridentity_bk as select * from oauthclient_useridentity;
