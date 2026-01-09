import psycopg2
from psycopg2.extras import RealDictCursor

# Source (Railway)
source_conn = psycopg2.connect(
    host="shinkansen.proxy.rlwy.net",
    port=49888,
    user="postgres",
    password="wUXRJCcrvqKCaNLZaUiRDXEbsjdduujw",
    database="railway"
)

# Destination (Local)
dest_conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="s0m13i5",
    database="macro_indicators"
)

source_cur = source_conn.cursor(cursor_factory=RealDictCursor)
dest_cur = dest_conn.cursor()

print("Connected to both databases")

# Clear local database
print("\nClearing local database...")
dest_cur.execute("TRUNCATE TABLE macro_indicators.data_points CASCADE")
dest_cur.execute("TRUNCATE TABLE macro_indicators.indicators CASCADE")
dest_cur.execute("TRUNCATE TABLE macro_indicators.categories CASCADE")
dest_conn.commit()
print("Local database cleared")

# Copy categories
print("\nCopying categories...")
source_cur.execute("SELECT * FROM macro_indicators.categories ORDER BY id")
categories = source_cur.fetchall()
for cat in categories:
    dest_cur.execute(
        "INSERT INTO macro_indicators.categories (id, name, slug, description, display_order) VALUES (%s, %s, %s, %s, %s)",
        (cat['id'], cat['name'], cat['slug'], cat['description'], cat.get('display_order', 0))
    )
print(f"Copied {len(categories)} categories")

# Copy indicators
print("\nCopying indicators...")
source_cur.execute("SELECT * FROM macro_indicators.indicators ORDER BY id")
indicators = source_cur.fetchall()
for ind in indicators:
    dest_cur.execute(
        """INSERT INTO macro_indicators.indicators (id, name, slug, category_id, description, unit, 
           frequency, source, scrape_url, html_selector, display_order) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (ind['id'], ind['name'], ind['slug'], ind['category_id'], ind['description'],
         ind['unit'], ind['frequency'], ind['source'], ind['scrape_url'], 
         ind['html_selector'], ind['display_order'])
    )
print(f"Copied {len(indicators)} indicators")

# Copy data_points
print("\nCopying data points...")
source_cur.execute("SELECT * FROM macro_indicators.data_points ORDER BY id")
data_points = source_cur.fetchall()
batch_size = 1000
for i in range(0, len(data_points), batch_size):
    batch = data_points[i:i+batch_size]
    for dp in batch:
        dest_cur.execute(
            "INSERT INTO macro_indicators.data_points (id, indicator_id, date, value, series_type) VALUES (%s, %s, %s, %s, %s)",
            (dp['id'], dp['indicator_id'], dp['date'], dp['value'], dp['series_type'])
        )
    dest_conn.commit()
    print(f"  Copied {min(i+batch_size, len(data_points))}/{len(data_points)} data points")

print(f"\nTotal data points copied: {len(data_points)}")

# Update sequences
print("\nUpdating sequences...")
dest_cur.execute("SELECT setval('macro_indicators.categories_id_seq', (SELECT MAX(id) FROM macro_indicators.categories))")
dest_cur.execute("SELECT setval('macro_indicators.indicators_id_seq', (SELECT MAX(id) FROM macro_indicators.indicators))")
dest_cur.execute("SELECT setval('macro_indicators.data_points_id_seq', (SELECT MAX(id) FROM macro_indicators.data_points))")
dest_conn.commit()

print("\n✅ Migration completed successfully!")

source_cur.close()
dest_cur.close()
source_conn.close()
dest_conn.close()
