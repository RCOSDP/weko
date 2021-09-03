-- weko#20294, 25702
ALTER TABLE "public"."authors" ADD COLUMN "is_deleted" bool;
UPDATE "public"."authors" SET is_deleted = false WHERE is_deleted IS NULL;
