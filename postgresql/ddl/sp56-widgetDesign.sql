-- weko#20300, weko#16639
ALTER TABLE widget_items ADD created timestamp NOT NULL DEFAULT now();
ALTER TABLE widget_items ADD updated timestamp NOT NULL DEFAULT now();
ALTER TABLE widget_items ADD locked boolean;
ALTER TABLE widget_items ADD locked_by_user integer;
