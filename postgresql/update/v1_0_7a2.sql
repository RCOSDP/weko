CREATE OR REPLACE FUNCTION update_v107a2()
RETURNS void AS $$
BEGIN
    IF (SELECT COUNT(id) FROM authors_prefix_settings WHERE scheme='e-Rad_Researcher')=0 THEN
        INSERT INTO authors_prefix_settings ( name,scheme,url,created,updated ) VALUES ('e-Rad_Researcher','e-Rad_Researcher','','2024-12-24 00:00:00','2024-12-24 00:00:00');
    END IF;
    IF (SELECT COUNT(id) FROM authors_prefix_settings WHERE scheme='ROR')=0 THEN
        INSERT INTO authors_prefix_settings ( name,scheme,url,created,updated ) VALUES ('ROR','ROR','https://ror.org/##','2024-12-24 00:00:00','2024-12-24 00:00:00');
    END IF;
    IF (SELECT COUNT(id) FROM authors_prefix_settings WHERE scheme='ISNI')=0 THEN
        INSERT INTO authors_prefix_settings ( name,scheme,url,created,updated ) VALUES ('ISNI','ISNI','http://www.isni.org/isni/##','2024-12-24 00:00:00','2024-12-24 00:00:00');
    END IF;
    IF (SELECT COUNT(id) FROM authors_prefix_settings WHERE scheme='VIAF')=0 THEN
        INSERT INTO authors_prefix_settings ( name,scheme,url,created,updated ) VALUES ('VIAF','VIAF','https://viaf.org/viaf/##','2024-12-24 00:00:00','2024-12-24 00:00:00');
    END IF;

    IF (SELECT COUNT(id) FROM authors_prefix_settings WHERE scheme='AID')=0 THEN
        INSERT INTO authors_prefix_settings ( name,scheme,url,created,updated ) VALUES ('AID','AID','','2024-12-24 00:00:00','2024-12-24 00:00:00');
    END IF;
    IF (SELECT COUNT(id) FROM authors_prefix_settings WHERE scheme='Ringgold')=0 THEN
        INSERT INTO authors_prefix_settings ( name,scheme,url,created,updated ) VALUES ('Ringgold','Ringgold','','2024-12-24 00:00:00','2024-12-24 00:00:00');
    END IF;
    IF (SELECT COUNT(id) FROM authors_affiliation_settings WHERE scheme='ROR')=0 THEN
        INSERT INTO authors_affiliation_settings ( name,scheme,url,created,updated ) VALUES ('ROR','ROR','https://ror.org/##','2024-12-24 00:00:00','2024-12-24 00:00:00');
    END IF;
END;
$$ LANGUAGE plpgsql;
SELECT update_v107a2();