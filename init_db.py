import sqlalchemy.exc
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.sql import sqltypes

#  Requires SQLALCHEMY 1.4+

src_engine = create_engine("sqlite:///reflex_test.db")
src_metadata = MetaData(bind=src_engine)
exclude_tables = ('sqlite_master', 'sqlite_sequence', 'sqlite_temp_master', 'user_workout_metrics', 'unit_conversion',
                  )

tgt_engine = create_engine("sqlite:///reflex_dev.db")
tgt_metadata = MetaData(bind=tgt_engine)

@event.listens_for(src_metadata, "column_reflect")
def genericize_datatypes(inspector, tablename, column_dict):
   column_dict["type"] = column_dict["type"].as_generic(allow_nulltype=True)
"""
tgt_conn = tgt_engine.connect()
tgt_metadata.reflect()

# drop all tables in target database
for table in reversed(tgt_metadata.sorted_tables):
   if table.name not in exclude_tables:
      print('dropping table =', table.name)
      table.drop()

# # Delete all data in target database
# for table in reversed(tgt_metadata.sorted_tables):
#    table.delete()

tgt_metadata.clear()
tgt_metadata.reflect()
src_metadata.reflect()

# create all tables in target database
for table in src_metadata.sorted_tables:
   if table.name not in exclude_tables:
      table.create(bind=tgt_engine)

# refresh metadata before you can copy data
tgt_metadata.clear()
tgt_metadata.reflect()
"""

src_metadata.clear()
tgt_metadata.reflect()
src_metadata.reflect()

# Copy all data from src to target
for table in src_metadata.sorted_tables:
   try:
      tgt_table = tgt_metadata.tables[table.name]
      stmt = tgt_table.insert()
      for index, row in enumerate(table.select().execute()):
         print("table =", tgt_table.name, "Inserting row", index)
         stmt.execute(row._asdict())
   except sqlalchemy.exc.IntegrityError:
      continue