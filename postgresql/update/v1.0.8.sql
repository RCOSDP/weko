ALTER TABLE public.feedback_mail_list ADD COLUMN account_author text;
ALTER TABLE public.index ADD COLUMN is_deleted boolean DEFAULT false;
