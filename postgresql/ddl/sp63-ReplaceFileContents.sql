-- weko#26497
ALTER TABLE "public"."files_object" ADD COLUMN "root_file_id" uuid;
UPDATE "public"."files_object" SET root_file_id = file_id WHERE root_file_id IS NULL;
