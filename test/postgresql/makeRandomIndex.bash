#!/bin/bash

idx=1

make_index(){
  for i in `seq 0 100`; do
   name=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1`
   echo "INSERT INTO public.index (created, updated, id, parent, "position", index_name, index_name_english, index_link_name, index_link_name_english, harvest_spec, index_link_enabled, comment, more_check, display_no, harvest_public_state, display_format, image_name, public_state, public_date, recursive_public_state, rss_status, coverpage_state, recursive_coverpage_check, browsing_role, recursive_browsing_role, contribute_role, recursive_contribute_role, browsing_group, recursive_browsing_group, contribute_group, recursive_contribute_group, owner_user_id, item_custom_sort, biblio_flag, online_issn, is_deleted) VALUES (now(), now(), $idx, $2, $i, '$name', '$name', '', '$name', '', false, '', false, 5, true, '1', '', true, NULL, false, false, false, false, '3,-98,-99', false, '1,2,3,4,-98,-99', false, '', false, '', false, 1, '{}', false, '', false);"
   idx=$((idx+1))
 done
}

for j in `seq 0 50`;do
  make_index $idx $j
done




echo "SELECT pg_catalog.setval('public.index_id_seq', $idx, false);"
echo "ALTER TABLE ONLY public.index ADD CONSTRAINT pk_index PRIMARY KEY (id);"
echo "ALTER TABLE ONLY public.index ADD CONSTRAINT uix_position UNIQUE (parent, \"position\");"
