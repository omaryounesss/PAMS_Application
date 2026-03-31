# Database Dump Instructions (for Submission Package)

After running `python3 scripts/bootstrap_db.py`, export a MySQL dump and include it in your ZIP.

```bash
mysqldump -u root -p pams > pams_dump.sql
```

If your MySQL runs on non-default host/port:

```bash
mysqldump -h 127.0.0.1 -P 3306 -u root -p pams > pams_dump.sql
```

Include `pams_dump.sql` in your final submission ZIP.
