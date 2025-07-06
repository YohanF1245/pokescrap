import sqlite3
import os

class DatabaseManagerV2:
    def __init__(self, db_path="pokemon_shasse_v2.db"):
        self.db_path = db_path
        self.create_tables()

    def create_connection(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        """Crée toutes les tables avec le nouveau schéma amélioré."""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        # Table Pokemon (inchangée)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pokemon (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                number INTEGER,
                sprite_url TEXT,
                generation INTEGER NOT NULL,
                is_shiny_lock BOOLEAN DEFAULT 0,
                high_quality_image TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des jeux (inchangée)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                generation INTEGER NOT NULL
            )
        ''')
        
        # Table des méthodes de chasse (AMÉLIORÉE)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hunt_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_general BOOLEAN DEFAULT 0,  -- ✅ NOUVEAU : indique si méthode générale
                category TEXT  -- ✅ NOUVEAU : "breeding", "encounter", "reset", etc.
            )
        ''')
        
        # Table des localisations (inchangée)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                region TEXT,
                description TEXT
            )
        ''')
        
        # ✅ NOUVELLE TABLE : Associations Pokemon-Méthodes GÉNÉRALES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pokemon_general_methods (
                pokemon_id INTEGER,
                hunt_method_id INTEGER,
                conditions TEXT,
                notes TEXT,
                PRIMARY KEY (pokemon_id, hunt_method_id),
                FOREIGN KEY (pokemon_id) REFERENCES pokemon (id),
                FOREIGN KEY (hunt_method_id) REFERENCES hunt_methods (id)
            )
        ''')
        
        # ✅ NOUVELLE TABLE : Associations Pokemon-Méthodes SPÉCIFIQUES par jeu/lieu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pokemon_specific_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pokemon_id INTEGER NOT NULL,
                hunt_method_id INTEGER NOT NULL,
                game_id INTEGER NOT NULL,
                location_id INTEGER,  -- ✅ Peut être NULL
                probability TEXT,
                conditions TEXT,
                notes TEXT,
                FOREIGN KEY (pokemon_id) REFERENCES pokemon (id),
                FOREIGN KEY (hunt_method_id) REFERENCES hunt_methods (id),
                FOREIGN KEY (game_id) REFERENCES games (id),
                FOREIGN KEY (location_id) REFERENCES locations (id)
            )
        ''')
        
        # Table Pokemon-Jeux (simplifiée)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pokemon_games (
                pokemon_id INTEGER,
                game_id INTEGER,
                availability TEXT,  -- ✅ "starter", "wild", "gift", etc.
                PRIMARY KEY (pokemon_id, game_id),
                FOREIGN KEY (pokemon_id) REFERENCES pokemon (id),
                FOREIGN KEY (game_id) REFERENCES games (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Tables V2 créées avec succès")

    def insert_pokemon(self, name, number, sprite_url, generation, is_shiny_lock=False, high_quality_image=None, description=None):
        """Insère un nouveau Pokemon."""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM pokemon WHERE name = ? AND generation = ?', (name, generation))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return existing[0]
        
        cursor.execute('''
            INSERT INTO pokemon (name, number, sprite_url, generation, is_shiny_lock, high_quality_image, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, number, sprite_url, generation, is_shiny_lock, high_quality_image, description))
        
        pokemon_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return pokemon_id

    def insert_hunt_method(self, name, description=None, is_general=False, category=None):
        """Insère une méthode de chasse avec support des méthodes générales."""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM hunt_methods WHERE name = ?', (name,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return existing[0]
        
        cursor.execute('''
            INSERT INTO hunt_methods (name, description, is_general, category) 
            VALUES (?, ?, ?, ?)
        ''', (name, description, is_general, category))
        
        method_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return method_id

    def insert_game(self, name, generation):
        """Insère un jeu."""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM games WHERE name = ?', (name,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return existing[0]
        
        cursor.execute('INSERT INTO games (name, generation) VALUES (?, ?)', (name, generation))
        game_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return game_id

    def insert_location(self, name, region=None, description=None):
        """Insère une localisation."""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM locations WHERE name = ? AND region = ?', (name, region))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return existing[0]
        
        cursor.execute('INSERT INTO locations (name, region, description) VALUES (?, ?, ?)', 
                      (name, region, description))
        location_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return location_id

    def link_pokemon_general_method(self, pokemon_id, hunt_method_id, conditions=None, notes=None):
        """Lie un Pokemon à une méthode GÉNÉRALE (ex: Masuda)."""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO pokemon_general_methods 
            (pokemon_id, hunt_method_id, conditions, notes)
            VALUES (?, ?, ?, ?)
        ''', (pokemon_id, hunt_method_id, conditions, notes))
        
        conn.commit()
        conn.close()

    def link_pokemon_specific_method(self, pokemon_id, hunt_method_id, game_id, location_id=None, 
                                   probability=None, conditions=None, notes=None):
        """Lie un Pokemon à une méthode SPÉCIFIQUE à un jeu/lieu."""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pokemon_specific_methods 
            (pokemon_id, hunt_method_id, game_id, location_id, probability, conditions, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (pokemon_id, hunt_method_id, game_id, location_id, probability, conditions, notes))
        
        conn.commit()
        conn.close()

    def get_pokemon_methods(self, pokemon_id):
        """Récupère toutes les méthodes d'un Pokemon (générales + spécifiques)."""
        conn = self.create_connection()
        cursor = conn.cursor()
        
        # Méthodes générales
        cursor.execute('''
            SELECT hm.name, hm.description, hm.category, pgm.conditions, pgm.notes
            FROM pokemon_general_methods pgm
            JOIN hunt_methods hm ON pgm.hunt_method_id = hm.id
            WHERE pgm.pokemon_id = ?
        ''', (pokemon_id,))
        general_methods = cursor.fetchall()
        
        # Méthodes spécifiques
        cursor.execute('''
            SELECT hm.name, hm.description, g.name as game, l.name as location, 
                   psm.probability, psm.conditions, psm.notes
            FROM pokemon_specific_methods psm
            JOIN hunt_methods hm ON psm.hunt_method_id = hm.id
            JOIN games g ON psm.game_id = g.id
            LEFT JOIN locations l ON psm.location_id = l.id
            WHERE psm.pokemon_id = ?
        ''', (pokemon_id,))
        specific_methods = cursor.fetchall()
        
        conn.close()
        return {
            'general': general_methods,
            'specific': specific_methods
        }

if __name__ == "__main__":
    # Test du nouveau schéma
    db = DatabaseManagerV2()
    print("🧪 Test du nouveau schéma BDD...")
    
    # Exemples de méthodes générales vs spécifiques
    general_methods = [
        ("Masuda", "Reproduction avec parents de nationalités différentes", True, "breeding"),
        ("Charme Chroma", "Augmente les chances de shiny", True, "general"),
        ("Combo SOS", "Appeler des alliés pour augmenter les chances", True, "encounter")
    ]
    
    specific_methods = [
        ("Reset", "Redémarrer le jeu pour obtenir un Pokemon fixe", False, "reset"),
        ("Rencontre sauvage", "Chercher dans les hautes herbes", False, "encounter"),
        ("Pêche", "Utiliser une canne à pêche", False, "encounter")
    ]
    
    print("✅ Nouveau schéma prêt !") 