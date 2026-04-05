# Assets Doc

# Data Migration Assets (Patterns)

## 1.

1. Source DB: Use FK relationships as a map to discover what data to extract
2. Target DB: Treat it as a data dump - just copy the pre-validated data without constraint checking
3. After loading: Re-enable FKs so the target DB enforces integrity going forward

- This data migration pattersn is useful for cases:
  - Source data is already validated/consistent
  - Doing a one-time bulk load
  - You want maximum insertion speed
  - Re-enable constraints after loading
