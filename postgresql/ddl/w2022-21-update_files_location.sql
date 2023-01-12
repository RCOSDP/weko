ALTER TABLE public.files_location ADD COLUMN s3_endpoint_url varchar(128);
ALTER TABLE public.files_location ADD COLUMN s3_send_file_directly boolean NOT NULL DEFAULT true;