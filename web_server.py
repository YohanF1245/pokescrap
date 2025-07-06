from flask import Flask, render_template, jsonify, request, send_from_directory
import sqlite3
import os
import json
from database_v2 import DatabaseManagerV2

# Importer le fichier de référence
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from regional_forms_reference import (
    is_regional_form, is_regional_evolution, 
    get_region_from_name, should_be_in_pokedex_tab,
    should_be_in_regional_tab, should_be_in_other_forms_tab
)

app = Flask(__name__)

# ✅ NOUVEAU : Utiliser DatabaseManagerV2
db = DatabaseManagerV2("pokemon_shasse.db")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pokemon')
def pokemon_list():
    """Liste tous les Pokemon avec leurs stats."""
    try:
        conn = db.create_connection()
        cursor = conn.cursor()
        
        # Récupérer tous les Pokemon avec leurs infos
        cursor.execute('''
            SELECT id, name, number, generation, sprite_url, is_shiny_lock, 
                   high_quality_image, description, created_at
            FROM pokemon 
            ORDER BY number, name
        ''')
        
        pokemons = []
        for row in cursor.fetchall():
            pokemon_id, name, number, generation, sprite_url, is_shiny_lock, high_quality_image, description, created_at = row
            
            # Compter les méthodes générales
            cursor.execute('SELECT COUNT(*) FROM pokemon_general_methods WHERE pokemon_id = ?', (pokemon_id,))
            general_methods_count = cursor.fetchone()[0]
            
            # Compter les méthodes spécifiques
            cursor.execute('SELECT COUNT(*) FROM pokemon_specific_methods WHERE pokemon_id = ?', (pokemon_id,))
            specific_methods_count = cursor.fetchone()[0]
            
            # Compter les jeux
            cursor.execute('SELECT COUNT(*) FROM pokemon_games WHERE pokemon_id = ?', (pokemon_id,))
            games_count = cursor.fetchone()[0]
            
            pokemons.append({
                'id': pokemon_id,
                'name': name,
                'number': number,
                'generation': generation,
                'sprite_url': sprite_url,
                'is_shiny_lock': bool(is_shiny_lock),
                'high_quality_image': high_quality_image,
                'description': description,
                'created_at': created_at,
                'general_methods_count': general_methods_count,
                'specific_methods_count': specific_methods_count,
                'games_count': games_count,
                'total_methods': general_methods_count + specific_methods_count
            })
        
        conn.close()
        return jsonify(pokemons)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/pokemon/<int:pokemon_id>')
def pokemon_detail(pokemon_id):
    """Récupère les détails d'un Pokemon avec méthodes triées par jeux."""
    try:
        conn = db.create_connection()
        cursor = conn.cursor()
        
        # Récupérer les infos du Pokemon
        cursor.execute('''
            SELECT id, name, number, generation, sprite_url, is_shiny_lock, 
                   high_quality_image, description, created_at
            FROM pokemon 
            WHERE id = ?
        ''', (pokemon_id,))
        
        pokemon_row = cursor.fetchone()
        if not pokemon_row:
            return jsonify({'error': 'Pokemon not found'}), 404
        
        pokemon_id, name, number, generation, sprite_url, is_shiny_lock, high_quality_image, description, created_at = pokemon_row
        
        # ✅ NOUVEAU : Récupérer les méthodes avec le nouveau modèle
        methods_data = db.get_pokemon_methods(pokemon_id)
        
        # Organiser les méthodes générales
        general_methods = []
        for method in methods_data['general']:
            method_name, method_description, category, conditions, notes = method
            general_methods.append({
                'name': method_name,
                'description': method_description,
                'category': category,
                'conditions': conditions,
                'notes': notes
            })
        
        # ✅ NOUVEAU : Organiser les méthodes spécifiques PAR JEUX
        games_with_methods = {}
        for method in methods_data['specific']:
            method_name, method_description, game, location, probability, conditions, notes = method
            
            if game not in games_with_methods:
                games_with_methods[game] = {
                    'name': game,
                    'methods': []
                }
            
            games_with_methods[game]['methods'].append({
                'name': method_name,
                'description': method_description,
                'location': location,
                'probability': probability,
                'conditions': conditions,
                'notes': notes
            })
        
        # Convertir en liste triée par nom de jeu
        games_list = sorted(games_with_methods.values(), key=lambda x: x['name'])
        
        # Récupérer tous les jeux du Pokemon (même sans méthodes)
        cursor.execute('''
            SELECT g.name, g.generation, pg.availability
            FROM pokemon_games pg
            JOIN games g ON pg.game_id = g.id
            WHERE pg.pokemon_id = ?
            ORDER BY g.name
        ''', (pokemon_id,))
        
        all_games = []
        for row in cursor.fetchall():
            game_name, game_generation, availability = row
            all_games.append({
                'name': game_name,
                'generation': game_generation,
                'availability': availability
            })
        
        # Construire la réponse
        pokemon_detail = {
            'id': pokemon_id,
            'name': name,
            'number': number,
            'generation': generation,
            'sprite_url': sprite_url,
            'is_shiny_lock': bool(is_shiny_lock),
            'high_quality_image': high_quality_image,
            'description': description,
            'created_at': created_at,
            'general_methods': general_methods,
            'games_with_methods': games_list,  # ✅ NOUVEAU : Triées par jeux
            'all_games': all_games
        }
        
        conn.close()
        return jsonify(pokemon_detail)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def stats():
    """Statistiques générales de la base de données."""
    try:
        conn = db.create_connection()
        cursor = conn.cursor()
        
        # Pokemon stats
        cursor.execute('SELECT COUNT(*) FROM pokemon')
        total_pokemon = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM pokemon WHERE is_shiny_lock = 1')
        shiny_locked = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT generation) FROM pokemon')
        generations = cursor.fetchone()[0]
        
        # Methods stats
        cursor.execute('SELECT COUNT(*) FROM hunt_methods')
        total_methods = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM hunt_methods WHERE is_general = 1')
        general_methods = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM hunt_methods WHERE is_general = 0')
        specific_methods = cursor.fetchone()[0]
        
        # Games stats
        cursor.execute('SELECT COUNT(*) FROM games')
        total_games = cursor.fetchone()[0]
        
        # Locations stats
        cursor.execute('SELECT COUNT(*) FROM locations')
        total_locations = cursor.fetchone()[0]
        
        # Pokemon par génération
        cursor.execute('''
            SELECT generation, COUNT(*) as count
            FROM pokemon 
            GROUP BY generation 
            ORDER BY generation
        ''')
        pokemon_by_generation = [{'generation': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Méthodes les plus utilisées
        cursor.execute('''
            SELECT hm.name, hm.category, COUNT(*) as usage_count
            FROM (
                SELECT hunt_method_id FROM pokemon_general_methods
                UNION ALL
                SELECT hunt_method_id FROM pokemon_specific_methods
            ) methods
            JOIN hunt_methods hm ON methods.hunt_method_id = hm.id
            GROUP BY hm.name, hm.category
            ORDER BY usage_count DESC
            LIMIT 10
        ''')
        popular_methods = []
        for row in cursor.fetchall():
            method_name, category, usage_count = row
            popular_methods.append({
                'name': method_name,
                'category': category,
                'usage_count': usage_count
            })
        
        conn.close()
        
        return jsonify({
            'pokemon': {
                'total': total_pokemon,
                'shiny_locked': shiny_locked,
                'shiny_available': total_pokemon - shiny_locked,
                'generations': generations,
                'by_generation': pokemon_by_generation
            },
            'methods': {
                'total': total_methods,
                'general': general_methods,
                'specific': specific_methods,
                'popular': popular_methods
            },
            'games': {
                'total': total_games
            },
            'locations': {
                'total': total_locations
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generations')
def generations():
    """Liste les générations avec leurs Pokemon."""
    try:
        conn = db.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT generation, COUNT(*) as pokemon_count
            FROM pokemon 
            GROUP BY generation 
            ORDER BY generation
        ''')
        
        generations_data = []
        for row in cursor.fetchall():
            generation, pokemon_count = row
            generations_data.append({
                'generation': generation,
                'pokemon_count': pokemon_count
            })
        
        conn.close()
        return jsonify(generations_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search')
def search():
    """Recherche de Pokemon par nom."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    try:
        conn = db.create_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, number, generation, sprite_url, is_shiny_lock
            FROM pokemon 
            WHERE name LIKE ? OR CAST(number AS TEXT) LIKE ?
            ORDER BY name
            LIMIT 20
        ''', (f'%{query}%', f'%{query}%'))
        
        results = []
        for row in cursor.fetchall():
            pokemon_id, name, number, generation, sprite_url, is_shiny_lock = row
            results.append({
                'id': pokemon_id,
                'name': name,
                'number': number,
                'generation': generation,
                'sprite_url': sprite_url,
                'is_shiny_lock': bool(is_shiny_lock)
            })
        
        conn.close()
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Sert les fichiers statiques (sprites, images)."""
    return send_from_directory('assets', filename)

# ✅ NOUVELLE ROUTE : Page détaillée d'un Pokemon
@app.route('/poke/<pokemon_name>')
def pokemon_detail_page(pokemon_name):
    """Affiche la page détaillée d'un Pokemon avec sprites, jeux et méthodes."""
    try:
        conn = db.create_connection()
        cursor = conn.cursor()
        
        # Chercher le Pokemon par nom (cas insensible)
        cursor.execute('''
            SELECT id, name, number, generation, sprite_url, is_shiny_lock, 
                   high_quality_image, description, created_at
            FROM pokemon 
            WHERE LOWER(name) = LOWER(?)
            ORDER BY generation
        ''', (pokemon_name,))
        
        pokemon_variants = cursor.fetchall()
        
        if not pokemon_variants:
            return render_template('pokemon_not_found.html', pokemon_name=pokemon_name), 404
        
        # Si plusieurs variants (formes régionales), prendre le premier
        pokemon_data = pokemon_variants[0]
        pokemon_id, name, number, generation, sprite_url, is_shiny_lock, high_quality_image, description, created_at = pokemon_data
        
        # Récupérer les méthodes avec le nouveau modèle V2
        methods_data = db.get_pokemon_methods(pokemon_id)
        
        # Organiser les méthodes générales
        general_methods = []
        for method in methods_data['general']:
            method_name, method_description, category, conditions, notes = method
            general_methods.append({
                'name': method_name,
                'description': method_description,
                'category': category,
                'conditions': conditions or '',
                'notes': notes or ''
            })
        
        # Organiser les méthodes spécifiques par jeu ET par génération
        specific_methods = []
        games_by_generation = {}
        
        for method in methods_data['specific']:
            method_name, method_description, game, location, probability, conditions, notes = method
            
            # Récupérer la génération du jeu
            cursor.execute('SELECT generation FROM games WHERE name = ?', (game,))
            game_gen_row = cursor.fetchone()
            game_generation = game_gen_row[0] if game_gen_row else generation
            
            method_info = {
                'name': method_name,
                'description': method_description,
                'game': game,
                'location': location or 'Non spécifié',
                'probability': probability or 'Non spécifié',
                'conditions': conditions or '',
                'notes': notes or '',
                'generation': game_generation
            }
            
            specific_methods.append(method_info)
            
            # Organiser par génération
            if game_generation not in games_by_generation:
                games_by_generation[game_generation] = []
            
            games_by_generation[game_generation].append(method_info)
        
        # Récupérer tous les jeux du Pokemon
        cursor.execute('''
            SELECT DISTINCT g.name, g.generation
            FROM games g
            JOIN pokemon_specific_methods psm ON g.id = psm.game_id
            WHERE psm.pokemon_id = ?
            ORDER BY g.generation, g.name
        ''', (pokemon_id,))
        
        all_games = []
        for row in cursor.fetchall():
            game_name, game_generation = row
            all_games.append({
                'name': game_name,
                'generation': game_generation
            })
        
        # Organiser les jeux par génération
        games_by_gen = {}
        for game in all_games:
            gen = game['generation']
            if gen not in games_by_gen:
                games_by_gen[gen] = []
            games_by_gen[gen].append(game)
        
        conn.close()
        
        # Préparer les données pour le template
        pokemon_info = {
            'id': pokemon_id,
            'name': name,
            'number': number,
            'generation': generation,
            'sprite_url': sprite_url,
            'is_shiny_lock': bool(is_shiny_lock),
            'high_quality_image': high_quality_image,
            'description': description or f"Informations sur {name}",
            'created_at': created_at,
            'general_methods': general_methods,
            'specific_methods': specific_methods,
            'games_by_generation': games_by_generation,
            'all_games': all_games,
            'games_by_gen': games_by_gen,
            'variants': pokemon_variants  # Toutes les formes du Pokemon
        }
        
        return render_template('pokemon_detail.html', pokemon=pokemon_info)
        
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

# ✅ NOUVELLES ROUTES API POUR LE FRONT

@app.route('/api/stats')
def api_stats():
    """API pour les statistiques (appelée par le JavaScript)."""
    try:
        conn = db.create_connection()
        cursor = conn.cursor()
        
        # Pokemon stats de base
        cursor.execute('SELECT COUNT(*) FROM pokemon')
        total_pokemon = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM pokemon WHERE sprite_url IS NOT NULL')
        sprites_downloaded = cursor.fetchone()[0]
        
        # Calcul du pourcentage de progression (sprites téléchargés)
        download_percentage = (sprites_downloaded / total_pokemon * 100) if total_pokemon > 0 else 0
        
        # Total des formes (pour l'instant = total Pokemon)
        cursor.execute('SELECT COUNT(DISTINCT name) FROM pokemon')
        total_forms = cursor.fetchone()[0]
        
        # Statistiques par génération pour les barres de progression
        cursor.execute('''
            SELECT generation, 
                   COUNT(*) as total,
                   COUNT(CASE WHEN sprite_url IS NOT NULL THEN 1 END) as with_sprites
            FROM pokemon 
            GROUP BY generation 
            ORDER BY generation
        ''')
        generation_stats = []
        for row in cursor.fetchall():
            generation, total, with_sprites = row
            generation_stats.append([generation, total, with_sprites])
        
        # Top formes (ici on utilise les générations comme "formes")
        cursor.execute('''
            SELECT 'Génération ' || generation as form_name, COUNT(*) as count
            FROM pokemon 
            GROUP BY generation 
            ORDER BY count DESC
            LIMIT 5
        ''')
        top_forms = []
        for row in cursor.fetchall():
            form_name, count = row
            top_forms.append([form_name, count])
        
        # Pokemon récents (derniers ajoutés)
        cursor.execute('''
            SELECT name, generation, sprite_url
            FROM pokemon 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        recent_pokemon = []
        for row in cursor.fetchall():
            name, generation, sprite_path = row
            # Nettoyer le chemin pour l'affichage web
            clean_sprite_path = None
            if sprite_path:
                clean_sprite_path = sprite_path.replace('assets/', '').replace('assets\\', '').replace('\\', '/')
            recent_pokemon.append([name, generation, clean_sprite_path])
        
        conn.close()
        
        # Retourner dans le format attendu par le JavaScript
        return jsonify({
            'total_pokemon': total_pokemon,
            'sprites_downloaded': sprites_downloaded,
            'download_percentage': round(download_percentage, 1),
            'total_forms': total_forms,
            'generation_stats': generation_stats,
            'top_forms': top_forms,
            'recent_pokemon': recent_pokemon
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sprites')
def api_sprites():
    """API pour les sprites organisés par génération."""
    try:
        conn = db.create_connection()
        cursor = conn.cursor()
        
        # Récupérer tous les Pokemon avec leurs sprites
        cursor.execute('''
            SELECT name, number, generation, sprite_url, is_shiny_lock, created_at
            FROM pokemon 
            WHERE sprite_url IS NOT NULL AND sprite_url != ''
            ORDER BY generation, number
        ''')
        
        pokemon_data = cursor.fetchall()
        
        # Organiser par génération
        generations = {}
        for pokemon in pokemon_data:
            name, number, gen, sprite_url, is_shiny_lock, created_at = pokemon
            
            if gen not in generations:
                generations[gen] = {
                    'name': f'Génération {gen}',
                    'sprites': []
                }
            
            # Nettoyer l'URL du sprite
            clean_sprite_url = None
            if sprite_url:
                clean_sprite_url = sprite_url.replace('assets/', '').replace('assets\\', '').replace('\\', '/')
            
            generations[gen]['sprites'].append({
                'name': name,
                'number': number,
                'sprite_url': clean_sprite_url,
                'is_shiny_lock': is_shiny_lock,
                'created_at': created_at,
                'generation': gen  # Ajouter la génération pour le JavaScript
            })
        
        conn.close()
        
        return jsonify({
            'generations': generations,
            'regional_forms': {},  # TODO: Implémenter si nécessaire
            'other_forms': {}      # TODO: Implémenter si nécessaire
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pokemon/details/<pokemon_name>/<int:generation>')
def api_pokemon_details(pokemon_name, generation):
    """API pour les détails d'un Pokemon (appelée par le JavaScript)."""
    try:
        conn = db.create_connection()
        cursor = conn.cursor()
        
        # Récupérer le Pokemon
        cursor.execute('''
            SELECT id, name, number, generation, sprite_url, is_shiny_lock, 
                   high_quality_image, description, created_at
            FROM pokemon 
            WHERE name = ? AND generation = ?
        ''', (pokemon_name, generation))
        
        pokemon = cursor.fetchone()
        if not pokemon:
            return jsonify({'error': 'Pokemon non trouvé'}), 404
        
        pokemon_id = pokemon[0]
        
        # Récupérer les méthodes générales et spécifiques
        methods = db.get_pokemon_methods(pokemon_id)
        
        # Récupérer les jeux
        cursor.execute('''
            SELECT DISTINCT g.name, g.generation
            FROM games g
            JOIN pokemon_specific_methods psm ON g.id = psm.game_id
            WHERE psm.pokemon_id = ?
        ''', (pokemon_id,))
        
        games = cursor.fetchall()
        
        # Récupérer les localisations
        cursor.execute('''
            SELECT DISTINCT l.name, l.region
            FROM locations l
            JOIN pokemon_specific_methods psm ON l.id = psm.location_id
            WHERE psm.pokemon_id = ?
        ''', (pokemon_id,))
        
        locations = cursor.fetchall()
        
        return jsonify({
            'id': pokemon[0],
            'name': pokemon[1],
            'number': pokemon[2],
            'generation': pokemon[3],
            'sprite_url': pokemon[4],
            'is_shiny_lock': pokemon[5],
            'high_quality_image': pokemon[6],
            'description': pokemon[7],
            'created_at': pokemon[8],
            'general_methods': [{'name': m[0], 'category': m[1], 'description': m[2]} for m in methods['general']],
            'specific_methods': [{'name': m[0], 'category': m[1], 'game': m[2], 'location': m[3]} for m in methods['specific']],
            'games': [{'name': g[0], 'generation': g[1]} for g in games],
            'locations': [{'name': l[0], 'region': l[1]} for l in locations]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/missing/<int:generation>')
def api_missing_pokemon(generation):
    """API pour les Pokemon manquants d'une génération."""
    try:
        conn = db.create_connection()
        cursor = conn.cursor()
        
        # Récupérer tous les Pokemon de cette génération
        cursor.execute('''
            SELECT name, number, sprite_url, is_shiny_lock
            FROM pokemon 
            WHERE generation = ?
            ORDER BY number
        ''', (generation,))
        
        pokemon_data = cursor.fetchall()
        
        # Identifier les Pokemon sans sprite
        missing_pokemon = []
        for pokemon in pokemon_data:
            name, number, sprite_url, is_shiny_lock = pokemon
            if not sprite_url or not os.path.exists(sprite_url):
                missing_pokemon.append({
                    'name': name,
                    'number': number,
                    'sprite_url': sprite_url,
                    'is_shiny_lock': is_shiny_lock
                })
        
        return jsonify({
            'generation': generation,
            'missing_pokemon': missing_pokemon,
            'total_pokemon': len(pokemon_data),
            'missing_count': len(missing_pokemon)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌟 Démarrage du serveur Pokemon Dashboard...")
    print("📊 Accédez au dashboard sur: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 