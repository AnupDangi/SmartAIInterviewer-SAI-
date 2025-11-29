# Database Cleanup Instructions

## Remove Old RAG Tables

The old RAG system used `chunks` and `files` tables which are no longer needed. 
We've also identified unused tables: `messages` and `sessions`.

### Option 1: Automatic Cleanup (Recommended)

The `init_db()` function in `src/db/config.py` will automatically drop these tables when the backend starts.

Just restart your backend server and the cleanup will happen automatically.

### Option 2: Manual SQL Cleanup

If you want to manually clean up, run this SQL in your Neon database:

```sql
-- Drop old RAG tables
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS files CASCADE;

-- Drop unused tables
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
```

### Tables to Keep

- ✅ `users` - User accounts
- ✅ `interviews` - Interview records
- ✅ `interview_sessions` - Conversation history
- ✅ `interview_memory` - NEW: Stores extracted CV/JD details (will be created automatically)

### After Cleanup

After cleanup, your database will have:
- Cleaner schema
- No unused tables
- New `interview_memory` table for structured CV/JD data
- Better performance (no vector operations)

