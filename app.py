def init_db():
    with get_db_connection() as conn:
        # Version corrigée : chaque colonne a juste son type, séparé par une virgule
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marque TEXT,
                modele TEXT,
                prix REAL,
                type_offre TEXT, 
                ville TEXT,
                pays TEXT, 
                kilometrage INTEGER,
                carburant TEXT
            )
        ''')
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        if cursor.fetchone()[0] == 0:
            sample_cars = [
                ('Mercedes-Benz', 'C220d', 39500, 'Vente', 'Magdeburg', 'Allemagne', 32000, 'Diesel'),
                ('BMW', 'Série 3', 450, 'Location', 'Paris', 'France', 20000, 'Essence'),
                ('Audi', 'A4', 28500, 'Vente', 'Genève', 'Suisse', 60000, 'Diesel'),
                ('Volkswagen', 'Golf', 180, 'Location', 'Berlin', 'Allemagne', 15000, 'Électrique'),
                ('Peugeot', '208', 14500, 'Vente', 'Lyon', 'France', 35000, 'Essence')
            ]
            conn.executemany('''
                INSERT INTO vehicles (marque, modele, prix, type_offre, ville, pays, kilometrage, carburant)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_cars)
            conn.commit()
