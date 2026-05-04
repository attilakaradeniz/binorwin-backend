from database import engine
import models

# Caution: This will drop all existing tables and permanently delete their data!
print("Dropping all existing tables...")
models.Base.metadata.drop_all(bind=engine)

# Recreate all tables with the updated schema (including the new created_at columns)
print("Recreating tables with the new schema...")
models.Base.metadata.create_all(bind=engine)

print("Database reset completed successfully!")