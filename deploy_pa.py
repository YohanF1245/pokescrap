#!/usr/bin/env python3
"""
Script de déploiement PythonAnywhere pour Pokemon Shasse Dashboard
"""

import requests
import os
import json
from pathlib import Path

def main():
    """Fonction principale de déploiement."""
    
    # Configuration depuis les variables d'environnement
    username = os.environ.get('PA_USERNAME')
    api_token = os.environ.get('PA_API_TOKEN')
    
    if not username or not api_token:
        print("❌ Variables d'environnement manquantes: PA_USERNAME et PA_API_TOKEN")
        return False
    
    domain_name = f"{username}.pythonanywhere.com"
    
    # Headers pour l'API
    headers = {'Authorization': f'Token {api_token}'}
    
    print("🚀 Déploiement sur PythonAnywhere...")
    print(f"👤 Utilisateur: {username}")
    print(f"🌐 Domaine: {domain_name}")
    
    # 1. Créer l'application web si elle n'existe pas
    print("\n📝 Configuration de l'application web...")
    
    webapps_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/webapps/"
    response = requests.get(webapps_url, headers=headers)
    
    webapp_exists = False
    if response.status_code == 200:
        webapps = response.json()
        for webapp in webapps:
            if webapp['domain_name'] == domain_name:
                webapp_exists = True
                print(f"✅ Application web existante trouvée: {domain_name}")
                break
    
    if not webapp_exists:
        print(f"🆕 Création de l'application web: {domain_name}")
        webapp_data = {
            'domain_name': domain_name,
            'python_version': 'python39',
            'source_directory': f'/home/{username}/pokescrap',
            'virtualenv_path': f'/home/{username}/.virtualenvs/pokescrap'
        }
        
        response = requests.post(webapps_url, json=webapp_data, headers=headers)
        if response.status_code == 201:
            print("✅ Application web créée avec succès")
        else:
            print(f"❌ Erreur lors de la création: {response.status_code}")
            print(response.text)
    
    # 2. Créer le virtualenv si nécessaire
    print("\n🐍 Configuration de l'environnement virtuel...")
    
    virtualenv_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/virtualenvs/"
    virtualenv_data = {
        'virtualenv_path': f'/home/{username}/.virtualenvs/pokescrap',
        'python_version': 'python3.9'
    }
    
    response = requests.post(virtualenv_url, json=virtualenv_data, headers=headers)
    if response.status_code == 201:
        print("✅ Environnement virtuel créé")
    elif response.status_code == 400 and "already exists" in response.text:
        print("✅ Environnement virtuel existant")
    else:
        print(f"⚠️ Réponse virtualenv: {response.status_code}")
    
    # 3. Upload des fichiers
    print("\n📁 Upload des fichiers...")
    
    files_to_upload = [
        'web_server.py',
        'database_v2.py', 
        'pokemon_shasse.db',
        'requirements.txt'
    ]
    
    # Upload des fichiers individuels
    for file_path in files_to_upload:
        if os.path.exists(file_path):
            print(f"📤 Upload: {file_path}")
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            files_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/files/path/home/{username}/pokescrap/{file_path}"
            
            response = requests.post(
                files_url,
                files={'content': file_content},
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ {file_path} uploadé")
            else:
                print(f"❌ Erreur upload {file_path}: {response.status_code}")
        else:
            print(f"⚠️ Fichier non trouvé: {file_path}")
    
    # 4. Upload des dossiers (templates, static, assets)
    folders_to_upload = ['templates', 'static', 'assets']
    
    for folder_name in folders_to_upload:
        if os.path.exists(folder_name):
            print(f"📁 Upload dossier: {folder_name}")
            
            # Créer le dossier sur PA
            folder_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/files/path/home/{username}/pokescrap/{folder_name}/"
            response = requests.post(folder_url, headers=headers)
            
            # Upload des fichiers du dossier
            for file_path in Path(folder_name).rglob('*'):
                if file_path.is_file():
                    relative_path = str(file_path).replace('\\', '/')
                    print(f"  📤 {relative_path}")
                    
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    file_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/files/path/home/{username}/pokescrap/{relative_path}"
                    
                    response = requests.post(
                        file_url,
                        files={'content': file_content},
                        headers=headers
                    )
                    
                    if response.status_code in [200, 201]:
                        print(f"    ✅ {relative_path}")
                    else:
                        print(f"    ❌ Erreur {relative_path}: {response.status_code}")
    
    # 5. Créer le fichier WSGI
    print("\n🔧 Configuration WSGI...")
    
    wsgi_content = f"""import sys
import os

# Ajouter le répertoire de l'application au path
path = '/home/{username}/pokescrap'
if path not in sys.path:
    sys.path.insert(0, path)

# Importer l'application Flask
from web_server import app as application

if __name__ == "__main__":
    application.run()
"""
    
    wsgi_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/files/path/home/{username}/pokescrap/flask_app.py"
    
    response = requests.post(
        wsgi_url,
        files={'content': wsgi_content.encode('utf-8')},
        headers=headers
    )
    
    if response.status_code in [200, 201]:
        print("✅ Fichier WSGI créé")
    else:
        print(f"❌ Erreur WSGI: {response.status_code}")
    
    # 6. Configurer l'application web
    print("\n⚙️ Configuration de l'application...")
    
    webapp_config_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain_name}/"
    webapp_config = {
        'source_directory': f'/home/{username}/pokescrap',
        'virtualenv_path': f'/home/{username}/.virtualenvs/pokescrap',
        'python_version': 'python39'
    }
    
    response = requests.patch(webapp_config_url, json=webapp_config, headers=headers)
    if response.status_code == 200:
        print("✅ Configuration mise à jour")
    else:
        print(f"⚠️ Config response: {response.status_code}")
    
    # 7. Installer les dépendances
    print("\n📦 Installation des dépendances...")
    
    console_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/consoles/"
    console_data = {
        'executable': 'bash',
        'arguments': [],
        'working_directory': f'/home/{username}/pokescrap'
    }
    
    response = requests.post(console_url, json=console_data, headers=headers)
    if response.status_code == 201:
        console_id = response.json()['id']
        print(f"✅ Console créée: {console_id}")
        
        # Installer les dépendances
        install_cmd = f"/home/{username}/.virtualenvs/pokescrap/bin/pip install -r requirements.txt"
        
        console_input_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/consoles/{console_id}/send_input/"
        
        response = requests.post(
            console_input_url,
            json={'input': install_cmd + '\n'},
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Dépendances installées")
        else:
            print(f"⚠️ Install response: {response.status_code}")
    
    # 8. Recharger l'application web
    print("\n🔄 Rechargement de l'application...")
    
    reload_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain_name}/reload/"
    
    response = requests.post(reload_url, headers=headers)
    if response.status_code == 200:
        print("✅ Application rechargée avec succès")
    else:
        print(f"⚠️ Reload response: {response.status_code}")
    
    print(f"\n🎉 Déploiement terminé !")
    print(f"🌐 Votre application est disponible sur: https://{domain_name}")
    print(f"📊 Dashboard Pokemon Shasse: https://{domain_name}/")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 