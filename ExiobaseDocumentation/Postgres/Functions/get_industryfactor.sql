CREATE OR REPLACE FUNCTION public.get_industryfactor(
    in_years       int[]  DEFAULT NULL,
    in_extensions  text[] DEFAULT NULL,
    in_factors     text[] DEFAULT NULL
)
RETURNS TABLE (
    country    varchar,           -- matches character varying
    sector     varchar,
    factor     varchar,
    year       int,
    value      double precision,
    extension  varchar
) AS $$
BEGIN
  RETURN QUERY
  SELECT
      i.country,
      i.sector,
      i.factor,
      i.year,
      i.value,
      i.extension
  FROM public.industryfactorshort AS i
  WHERE (in_years      IS NULL OR i.year      = ANY(in_years))
    AND (in_extensions IS NULL OR i.extension = ANY(in_extensions))
    AND (in_factors    IS NULL OR i.factor    = ANY(in_factors));
END;
$$ LANGUAGE plpgsql STABLE;
