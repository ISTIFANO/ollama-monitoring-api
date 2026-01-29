#!/usr/bin/env python3
"""
Script pour télécharger et optimiser le modèle Ollama
Gère le téléchargement du modèle avec vérification de la mémoire disponible
"""
import asyncio
import httpx
import sys


MODELS_INFO = {
    "qwen2.5:0.5b": {"size_gb": 0.5, "recommended": False, "description": "Petit modèle pour contraintes extrêmes"},
    "qwen2.5:1.5b": {"size_gb": 1.0, "recommended": False, "description": "Modèle léger"},
    "qwen2.5:3b": {"size_gb": 1.9, "recommended": False, "description": "Modèle intermédiaire"},
    "qwen2.5:7b-instruct-q4_0": {"size_gb": 4.4, "recommended": True, "description": "qwen-8b quantifié q4_0 - Recommandé pour 6GB"},
    "qwen2.5:7b-instruct-q4_K_M": {"size_gb": 4.7, "recommended": True, "description": "qwen-8b quantifié q4_K_M - Qualité supérieure"},
    "qwen2.5:7b-instruct-q5_K_M": {"size_gb": 5.4, "recommended": True, "description": "qwen-8b quantifié q5 - Meilleure qualité"},
}


async def check_ollama_service(url: str = "http://localhost:11434"):
    """Vérifier que le service Ollama est disponible"""
    print(f"🔍 Vérification du service Ollama sur {url}...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{url}/api/tags")
            if response.status_code == 200:
                print("✅ Service Ollama disponible")
                return True
            else:
                print(f"❌ Service Ollama répond avec le code: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Impossible de se connecter à Ollama: {str(e)}")
            print("💡 Assurez-vous que le container Ollama est démarré: docker-compose up -d ollama")
            return False


async def list_models(url: str = "http://localhost:11434"):
    """Lister les modèles déjà installés"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                if models:
                    print("\n📦 Modèles déjà installés:")
                    for model in models:
                        name = model.get("name", "Unknown")
                        size = model.get("size", 0) / (1024**3)  # Convert to GB
                        print(f"  - {name} ({size:.2f} GB)")
                else:
                    print("\n📦 Aucun modèle installé")
                return models
        except Exception as e:
            print(f"❌ Erreur lors de la liste des modèles: {str(e)}")
            return []


async def pull_model(model_name: str, url: str = "http://localhost:11434"):
    """Télécharger un modèle Ollama"""
    print(f"\n📥 Téléchargement du modèle: {model_name}")
    
    # Afficher les infos du modèle si disponibles
    if model_name in MODELS_INFO:
        info = MODELS_INFO[model_name]
        print(f"   Taille approximative: {info['size_gb']} GB")
        print(f"   Description: {info['description']}")
        if not info['recommended']:
            print("   ⚠️  ATTENTION: Ce modèle peut causer des problèmes avec 4GB RAM")
            response = input("   Voulez-vous continuer? (oui/non): ")
            if response.lower() not in ['oui', 'o', 'yes', 'y']:
                print("   ❌ Téléchargement annulé")
                return False
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            # Pull request avec streaming
            async with client.stream(
                'POST',
                f"{url}/api/pull",
                json={"name": model_name}
            ) as response:
                if response.status_code != 200:
                    print(f"❌ Erreur: {response.status_code}")
                    return False
                
                print("   Progression:")
                async for line in response.aiter_lines():
                    if line:
                        import json
                        try:
                            data = json.loads(line)
                            status = data.get("status", "")
                            if "completed" in data and "total" in data:
                                completed = data["completed"] / (1024**2)
                                total = data["total"] / (1024**2)
                                percent = (data["completed"] / data["total"]) * 100
                                print(f"   {status}: {completed:.1f}/{total:.1f} MB ({percent:.1f}%)", end='\r')
                            else:
                                print(f"   {status}")
                        except json.JSONDecodeError:
                            pass
                
                print("\n✅ Modèle téléchargé avec succès!")
                return True
                
        except Exception as e:
            print(f"\n❌ Erreur lors du téléchargement: {str(e)}")
            return False


async def verify_model(model_name: str, url: str = "http://localhost:11434"):
    """Vérifier qu'un modèle fonctionne correctement"""
    print(f"\n🧪 Test du modèle {model_name}...")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "Hello!",
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Modèle fonctionnel!")
                print(f"   Réponse: {data.get('response', '')[:100]}...")
                return True
            else:
                print(f"❌ Erreur: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du test: {str(e)}")
            return False


def print_recommendations():
    """Afficher les recommandations pour l'utilisation avec 6GB RAM"""
    print("\n" + "="*60)
    print("📋 RECOMMANDATIONS POUR 6GB RAM")
    print("="*60)
    print("\n✅ Modèles recommandés (qwen-8b quantifiés):")
    for model_name, info in MODELS_INFO.items():
        if info['recommended']:
            print(f"  • {model_name} - {info['size_gb']}GB")
            print(f"    {info['description']}")
    
    print("\n⚠️  Conseils d'optimisation:")
    print("  1. Utiliser OLLAMA_NUM_PARALLEL=1 (un seul modèle à la fois)")
    print("  2. Contexte adapté: MAX_CONTEXT_LENGTH=4096")
    print("  3. Streaming activé disponible avec 6GB")
    print("  4. Surveiller les métriques avec Grafana")
    print("  5. Configurer des alertes si RAM >90%")
    
    print("\n🔧 Variables d'environnement importantes:")
    print("  OLLAMA_NUM_PARALLEL=1")
    print("  OLLAMA_MAX_LOADED_MODELS=1")
    print("  OLLAMA_FLASH_ATTENTION=1")
    print("="*60 + "\n")


async def main():
    """Point d'entrée principal"""
    print("="*60)
    print("🚀 OLLAMA MODEL SETUP - Optimisé pour 6GB RAM")
    print("="*60)
    
    url = "http://localhost:11434"
    
    # Vérifier le service
    if not await check_ollama_service(url):
        sys.exit(1)
    
    # Lister les modèles existants
    await list_models(url)
    
    # Afficher les recommandations
    print_recommendations()
    
    # Demander quel modèle télécharger
    print("\n💡 Modèle par défaut recommandé: qwen2.5:7b-instruct-q4_0 (qwen-8b)")
    model_choice = input("Entrez le nom du modèle à télécharger (ou Enter pour qwen2.5:7b-instruct-q4_0): ").strip()
    
    if not model_choice:
        model_choice = "qwen2.5:7b-instruct-q4_0"
    
    # Télécharger le modèle
    success = await pull_model(model_choice, url)
    
    if success:
        # Vérifier le modèle
        await verify_model(model_choice, url)
        
        print(f"\n✅ Configuration terminée!")
        print(f"   Modèle installé: {model_choice}")
        print(f"   Mettez à jour le fichier .env avec: OLLAMA_MODEL={model_choice}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
