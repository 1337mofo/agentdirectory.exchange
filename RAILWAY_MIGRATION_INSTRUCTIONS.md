# Railway Database Migration Instructions
**Date:** 2026-02-12  
**Task:** Run 100-category system migration

## Problem
Cannot connect to Railway PostgreSQL database remotely due to connection timeouts/issues.

## Solution
Run the migration directly from Railway dashboard.

---

## Step 1: Access Railway Dashboard

1. Go to https://railway.com/project/df459949-3d36-4601-afcc-e50869c28223
2. Click on **Postgres** service
3. Click on **Data** tab

---

## Step 2: Open SQL Console

In the Data tab, you'll see a SQL query console.

---

## Step 3: Run Migration SQL

**Option A: Copy-Paste (Recommended)**

1. Open file: `migrations/add_100_categories.sql`
2. Copy the ENTIRE contents
3. Paste into Railway SQL console
4. Click **Run** or press Ctrl+Enter

**Option B: Run via Railway CLI (Alternative)**

```bash
railway link df459949-3d36-4601-afcc-e50869c28223
railway run psql < migrations/add_100_categories.sql
```

---

## Step 4: Verify Migration

Run this query in SQL console:

```sql
SELECT tier, COUNT(*) as count 
FROM agent_categories 
GROUP BY tier 
ORDER BY tier;
```

**Expected Output:**
```
tier | count
-----|------
  1  |  20
  2  |  30
  3  |  30
  4  |  20
```

**Total: 100 categories**

---

## Step 5: Check Agent Table Columns

Verify new columns were added:

```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'agents' 
  AND column_name IN ('primary_use_case', 'use_case_tags', 'slug', 'protocol_support', 'agntcy_member');
```

**Expected Output:**
```
primary_use_case
use_case_tags
slug
protocol_support
agntcy_member
```

---

## Step 6: Refresh Materialized View (Optional)

```sql
REFRESH MATERIALIZED VIEW category_stats;
```

---

## Troubleshooting

**If migration fails partway through:**
- This is OK! SQL statements have `IF NOT EXISTS` and `ON CONFLICT DO NOTHING`
- Simply re-run the entire migration script
- It will skip already-completed parts

**If you see "relation already exists" errors:**
- This means some parts already ran
- The migration is idempotent (safe to re-run)
- Continue to next step

**If categories already exist:**
- Check count: `SELECT COUNT(*) FROM agent_categories;`
- If count is 100, migration is complete!

---

## After Migration Complete

**Notify Nova:** Send me a message confirming migration is done

**Next Steps (Automated):**
1. Nova will run agent auto-tagging script
2. Generate slugs for all agents
3. Tag agents with primary use cases
4. Deploy category pages live

---

## Alternative: Deploy Migration Script to Railway

If you prefer automated execution:

1. Push `run_migration.py` to Railway
2. Set environment variable: `DATABASE_URL` (already set)
3. Run: `railway run python run_migration.py`

This will execute the migration automatically.

---

## Questions?

If any issues arise during migration, ping Nova with:
- Error message (if any)
- Which SQL statement failed (line number)
- Current category count: `SELECT COUNT(*) FROM agent_categories;`

**Estimated Time:** 2-5 minutes

---

**Once this migration completes, we can deploy all 100 category pages!** 🚀

**Nova Eagle - AI Project Lead**
