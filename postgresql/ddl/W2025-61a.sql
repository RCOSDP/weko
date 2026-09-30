DO $$
BEGIN
  RAISE NOTICE 'Start: W2025-61a.sql';
  UPDATE index
  SET
    browsing_group =
      CASE
        WHEN (browsing_group IS NULL OR browsing_group = '')
             THEN '-89'
        WHEN browsing_group LIKE '%-89%'
             THEN browsing_group
        ELSE browsing_group || ',-89'
      END,
    contribute_group =
      CASE
        WHEN (contribute_group IS NULL OR contribute_group = '')
             THEN '-89'
        WHEN contribute_group LIKE '%-89%'
             THEN contribute_group
        ELSE contribute_group || ',-89'
      END
  WHERE is_deleted = false;
  RAISE NOTICE 'Update completed.';
END
$$;
