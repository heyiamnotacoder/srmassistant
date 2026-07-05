# screening/exports/

Drop your database search exports here before running the screening workflow:

- `.ris` files (Embase, Scopus, Web of Science, Cochrane CENTRAL, Ovid, ...)
- `.nbib` files (PubMed → "Send to → Citation manager")

One file per database/search is fine — records are deduplicated across files automatically (DOI → PMID → normalized title). Export with abstracts included whenever the database offers the option; records without abstracts can only ever be screened as "maybe".
