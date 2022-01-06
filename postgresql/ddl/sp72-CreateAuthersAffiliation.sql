--for weko#29350
CREATE TABLE public.authors_affiliation_settings (
    id integer NOT NULL,
    name text NOT NULL,
    scheme text,
    url text,
    created timestamp NOT NULL,
    updated timestamp NOT NULL,
    CONSTRAINT pk_authors_affiliation_settings PRIMARY KEY (id)
);
INSERT INTO public.authors_affiliation_settings 
    (name, scheme, url) 
    VALUES
        ('ISNI', 'ISNI', 'http://www.isni.org/isni/'),
        ('GRID', 'GRID', 'https://www.grid.ac/institutes/'), 
        ('Ringgold', 'Ringgold', ''), 
        ('kakenhi', 'kakenhi', '')
    )
    
