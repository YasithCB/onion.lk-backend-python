import sqlite3

conn = sqlite3.connect('onionlk.db') 

cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE users (
        userId INTEGER PRIMARY KEY AUTOINCREMENT,
        mobileNumber TEXT,
        password TEXT
    )
''')
cursor.execute("INSERT INTO users (mobileNumber, password) VALUES (0767722095, 123456)")


cursor.execute('''
    CREATE TABLE drivers (
        driverId INTEGER PRIMARY KEY AUTOINCREMENT,
        mobileNumber TEXT,
        password TEXT,
        locationLat TEXT,
        locationLng TEXT
    )
''')
cursor.execute("INSERT INTO drivers (mobileNumber, password, locationLat, locationLng) VALUES (0767722096, 123456, 6.715017, 80.381284)")

cursor.execute('DROP TABLE IF EXISTS orders')
cursor.execute('''
    CREATE TABLE orders (
        orderId INTEGER PRIMARY KEY AUTOINCREMENT,
        imageUrl TEXT,
        description TEXT,
        userMobileNumber TEXT,
        storeName TEXT,
        maxBudget INT,
        locationLat TEXT,
        locationLng TEXT,
        assignedDriverMobileNumber TEXT,
        orderStatus TEXT,
        review TEXT,
        reviewScore REAL
    )
''')

cursor.execute("SELECT * FROM users")
print(cursor.fetchall())

cursor.execute("SELECT * FROM drivers")
print(cursor.fetchall())

cursor.execute("SELECT * FROM orders")
print(cursor.fetchall())


conn.commit()

cursor.close()            
conn.close()            