"""
Creates or updates the glossary terms listed in scripts/glossary_terms.json, publishing each one.
Existing terms are matched by name; terms not in the file are left untouched. See scripts/README.md.

    docker compose exec -T -e DRY_RUN=1 app python manage.py shell < scripts/import_glossary.py
"""
import json
import os

from django.db import transaction
from wagtailterms.models import Term

JSON = os.environ.get("JSON", "scripts/glossary_terms.json")
DRY_RUN = bool(os.environ.get("DRY_RUN"))

with open(JSON) as f:
    entries = json.load(f)

# PostgreSQL rejects longer values, SQLite silently stores them
max_length = Term._meta.get_field("term").max_length
too_long = [entry["term"] for entry in entries if len(entry["term"]) > max_length]
if too_long:
    raise SystemExit(f"Terms longer than {max_length} characters: {', '.join(too_long)}")

with transaction.atomic():
    created, updated = 0, 0
    for entry in entries:
        term = Term.objects.filter(term__iexact=entry["term"]).first()
        if term is None:
            term = Term(term=entry["term"])
            created += 1
            print("Creating:", entry["term"])
        else:
            updated += 1
            print("Updating:", entry["term"])
        term.definition = entry["definition"]
        term.save()
        term.save_revision().publish()
    print(f"Created {created} terms, updated {updated}")

    if DRY_RUN:
        transaction.set_rollback(True)
        print("DRY_RUN: nothing was saved")
