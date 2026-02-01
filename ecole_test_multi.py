#!/usr/bin/env python3
"""
Test automatisé pour l'API École Jeanne d'Arc
Teste les réponses de l'assistant avec validation automatique
"""

import requests
import csv
import time
import json
import argparse
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass
from colorama import init, Fore, Style
import sys

# Initialisation pour les couleurs en console
init(autoreset=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = "http://localhost:8000/chat"
MODEL = "qwen2.5:7b-instruct-q4_0"
TIMEOUT = 30  # secondes

SYSTEM_CONTEXT = """École Jeanne d'Arc - Informations

INFOS:
- Âges: 14 mois-18 ans (Crèche→Collège)
- Contact: 05 22 22 01 70
- Inscription: https://jeannedarc.ma/inscription2026_2027/4/
- Services: Cantine, Transport, Activités (Sports/Arts)
- Devise: "Être - Grandir - Réussir"
- Enseignants: Équipe marocaine et internationale
- Facilités de paiement pour 3+ enfants

RÈGLES: Réponse courte (1-2 phrases). Si info manquante → "Contactez 05 22 22 01 70"
"""

# Questions de test avec catégories et réponses attendues pour validation
QUESTIONS = [
    {
        "question": "Do you have a nursery?",
        "category": "services",
        "lang": "en",
        "expected_keywords": ["crèche", "nursery", "14 months", "2 years", "3 years"],
        "strict_validation": False
    },
    {
        "question": "Quels sont les horaires de l'école?",
        "category": "information",
        "lang": "fr",
        "expected_keywords": ["contactez", "05 22 22 01 70"],
        "strict_validation": True
    },
    {
        "question": "What are the tuition fees?",
        "category": "fees",
        "lang": "en",
        "expected_keywords": ["contact", "on site", "05 22 22 01 70"],
        "strict_validation": True
    },
    {
        "question": "Est-ce que vous avez une cantine?",
        "category": "services",
        "lang": "fr",
        "expected_keywords": ["cantine", "restaurant scolaire", "oui"],
        "strict_validation": True
    },
    {
        "question": "How can I enroll my child?",
        "category": "enrollment",
        "lang": "en",
        "expected_keywords": ["formulaire", "inscription", "https://jeannedarc.ma"],
        "strict_validation": True
    },
    {
        "question": "Avez-vous un service de transport?",
        "category": "services",
        "lang": "fr",
        "expected_keywords": ["transport", "oui", "service"],
        "strict_validation": True
    },
    {
        "question": "What is your school motto?",
        "category": "identity",
        "lang": "en",
        "expected_keywords": ["Être", "Grandir", "Réussir", "motto"],
        "strict_validation": True
    },
    {
        "question": "Quelles activités proposez-vous?",
        "category": "activities",
        "lang": "fr",
        "expected_keywords": ["sportives", "culturelles", "football", "théâtre", "arts"],
        "strict_validation": True
    },
    {
        "question": "Do you have international teachers?",
        "category": "staff",
        "lang": "en",
        "expected_keywords": ["international", "teachers", "marocains", "qualifiés"],
        "strict_validation": True
    },
    {
        "question": "Y a-t-il des réductions pour les fratries?",
        "category": "fees",
        "lang": "fr",
        "expected_keywords": ["fratries", "venir", "école", "détails", "facilités"],
        "strict_validation": True
    },
    {
        "question": "What ages do you accept?",
        "category": "admission",
        "lang": "en",
        "expected_keywords": ["14 months", "18 years", "âge", "crèche", "collège"],
        "strict_validation": True
    },
    {
        "question": "Comment vous contacter?",
        "category": "contact",
        "lang": "fr",
        "expected_keywords": ["05 22 22 01 70", "contacter", "contact"],
        "strict_validation": True
    },
    {
        "question": "Do you offer sports activities?",
        "category": "activities",
        "lang": "en",
        "expected_keywords": ["sports", "football", "basketball", "judo", "activités"],
        "strict_validation": True
    },
    {
        "question": "Quelle est votre devise?",
        "category": "identity",
        "lang": "fr",
        "expected_keywords": ["Être", "Grandir", "Réussir", "devise"],
        "strict_validation": True
    },
    {
        "question": "What languages do you teach?",
        "category": "curriculum",
        "lang": "en",
        "expected_keywords": ["français", "arabe", "anglais", "languages"],
        "strict_validation": True
    },
    {
        "question": "Avez-vous une psychologue?",
        "category": "services",
        "lang": "fr",
        "expected_keywords": ["psychopédagogue", "équipe", "soutien"],
        "strict_validation": True
    },
    {
        "question": "Do you have a library?",
        "category": "facilities",
        "lang": "en",
        "expected_keywords": ["bibliothèque", "library", "infrastructure"],
        "strict_validation": True
    },
    {
        "question": "Quels sont les niveaux disponibles?",
        "category": "admission",
        "lang": "fr",
        "expected_keywords": ["crèche", "maternelle", "élémentaire", "collège", "niveaux"],
        "strict_validation": True
    },
    {
        "question": "What makes your school special?",
        "category": "identity",
        "lang": "en",
        "expected_keywords": ["enfant", "prioritaire", "qualité", "projet éducatif"],
        "strict_validation": False
    },
    {
        "question": "Est-ce que vous acceptez les bébés?",
        "category": "admission",
        "lang": "fr",
        "expected_keywords": ["14 mois", "crèche", "bébés", "oui"],
        "strict_validation": True
    }
]

# ============================================================================
# CLASSES ET FONCTIONS
# ============================================================================

@dataclass
class TestResult:
    """Stockage des résultats d'un test"""
    question: str
    category: str
    language: str
    response: str
    duration: float
    status: str
    validation: str = "not_validated"
    validation_score: int = 0
    expected_keywords: List[str] = None
    found_keywords: List[str] = None

class APITester:
    """Classe principale pour tester l'API"""
    
    def __init__(self, api_url: str, model: str, system_context: str):
        self.api_url = api_url
        self.model = model
        self.system_context = system_context
        self.results: List[TestResult] = []
        self.stats = {
            "total": 0,
            "success": 0,
            "errors": 0,
            "validation_passed": 0,
            "validation_failed": 0,
            "total_duration": 0
        }
    
    def validate_response(self, response: str, expected_keywords: List[str], strict: bool = True) -> Tuple[str, int, List[str]]:
        """Valide une réponse par rapport aux mots-clés attendus"""
        response_lower = response.lower()
        found_keywords = []
        
        for keyword in expected_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in response_lower:
                found_keywords.append(keyword)
        
        score = len(found_keywords)
        
        if strict:
            # En mode strict, on veut au moins un mot-clé
            if score > 0:
                return "passed", score, found_keywords
            else:
                return "failed", score, found_keywords
        else:
            # En mode non strict, on accepte même si aucun mot-clé n'est trouvé
            if score >= len(expected_keywords) // 2:
                return "passed", score, found_keywords
            else:
                return "partial", score, found_keywords
    
    def send_request(self, question_data: Dict) -> TestResult:
        """Envoie une requête à l'API et retourne le résultat"""
        prompt = f"{self.system_context}\n\nQuestion: {question_data['question']}\nRéponse:"
        
        data = {
            "prompt": prompt,
            "model": self.model,
            "stream": False
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                self.api_url, 
                json=data, 
                timeout=TIMEOUT,
                headers={"Content-Type": "application/json"}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                response_text = response.json().get("response", "").strip()
                
                # Validation de la réponse
                validation_status, score, found_keywords = self.validate_response(
                    response_text,
                    question_data["expected_keywords"],
                    question_data["strict_validation"]
                )
                
                return TestResult(
                    question=question_data["question"],
                    category=question_data["category"],
                    language=question_data["lang"],
                    response=response_text,
                    duration=duration,
                    status="success",
                    validation=validation_status,
                    validation_score=score,
                    expected_keywords=question_data["expected_keywords"],
                    found_keywords=found_keywords
                )
            else:
                return TestResult(
                    question=question_data["question"],
                    category=question_data["category"],
                    language=question_data["lang"],
                    response=f"HTTP {response.status_code}: {response.text}",
                    duration=time.time() - start_time,
                    status=f"error_{response.status_code}",
                    expected_keywords=question_data["expected_keywords"]
                )
                
        except requests.exceptions.Timeout:
            return TestResult(
                question=question_data["question"],
                category=question_data["category"],
                language=question_data["lang"],
                response="Timeout",
                duration=TIMEOUT,
                status="timeout",
                expected_keywords=question_data["expected_keywords"]
            )
        except requests.exceptions.ConnectionError:
            return TestResult(
                question=question_data["question"],
                category=question_data["category"],
                language=question_data["lang"],
                response="Connection Error",
                duration=0,
                status="connection_error",
                expected_keywords=question_data["expected_keywords"]
            )
        except Exception as e:
            return TestResult(
                question=question_data["question"],
                category=question_data["category"],
                language=question_data["lang"],
                response=str(e),
                duration=time.time() - start_time,
                status="exception",
                expected_keywords=question_data["expected_keywords"]
            )
    
    def run_tests(self, questions: List[Dict], delay: float = 0.5) -> None:
        """Exécute tous les tests"""
        self.stats["total"] = len(questions)
        
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}  ÉCOLE JEANNE D'ARC - TEST AUTOMATISÉ COMPLET")
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.YELLOW}Modèle: {self.model}")
        print(f"{Fore.YELLOW}Questions: {len(questions)}")
        print(f"{Fore.YELLOW}Début: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{Fore.CYAN}{'-'*70}\n")
        
        for i, question_data in enumerate(questions, 1):
            # Affichage de la progression
            progress = f"[{i}/{len(questions)}]"
            category = f"[{question_data['category']}]"
            lang = f"[{question_data['lang'].upper()}]"
            
            print(f"{Fore.WHITE}{progress} {Fore.GREEN}{category} {Fore.BLUE}{lang} {Fore.WHITE}{question_data['question']}")
            
            # Envoi de la requête
            result = self.send_request(question_data)
            self.results.append(result)
            
            # Mise à jour des statistiques
            self.stats["total_duration"] += result.duration
            
            if result.status == "success":
                self.stats["success"] += 1
                
                # Validation
                if result.validation == "passed":
                    self.stats["validation_passed"] += 1
                    validation_indicator = f"{Fore.GREEN}✓"
                elif result.validation == "partial":
                    self.stats["validation_passed"] += 1  # On compte partial comme passed
                    validation_indicator = f"{Fore.YELLOW}⚠"
                else:
                    self.stats["validation_failed"] += 1
                    validation_indicator = f"{Fore.RED}✗"
            else:
                self.stats["errors"] += 1
                validation_indicator = f"{Fore.RED}✗"
            
            # Affichage du résultat
            if result.status == "success":
                # Tronquer la réponse si trop longue
                response_preview = result.response
                if len(response_preview) > 100:
                    response_preview = response_preview[:97] + "..."
                
                print(f"  {validation_indicator} {Fore.WHITE}{response_preview}")
                print(f"  {Fore.CYAN}⏱ {result.duration:.3f}s | "
                      f"{Fore.YELLOW}Score: {result.validation_score}/{len(result.expected_keywords)} | "
                      f"{Fore.MAGENTA}Keywords: {', '.join(result.found_keywords) if result.found_keywords else 'none'}")
            else:
                print(f"  {validation_indicator} {Fore.RED}{result.status}: {result.response}")
            
            print()
            
            # Pause entre les requêtes
            if i < len(questions):
                time.sleep(delay)
    
    def generate_report(self) -> Dict:
        """Génère un rapport détaillé des tests"""
        if not self.results:
            return {}
        
        # Calculs statistiques
        avg_duration = self.stats["total_duration"] / self.stats["success"] if self.stats["success"] > 0 else 0
        success_rate = (self.stats["success"] / self.stats["total"]) * 100 if self.stats["total"] > 0 else 0
        validation_rate = (self.stats["validation_passed"] / self.stats["success"]) * 100 if self.stats["success"] > 0 else 0
        
        # Analyse par catégorie
        category_stats = {}
        for result in self.results:
            if result.category not in category_stats:
                category_stats[result.category] = {"total": 0, "success": 0, "passed": 0}
            
            category_stats[result.category]["total"] += 1
            if result.status == "success":
                category_stats[result.category]["success"] += 1
                if result.validation == "passed" or result.validation == "partial":
                    category_stats[result.category]["passed"] += 1
        
        return {
            "summary": {
                "total_questions": self.stats["total"],
                "successful_responses": self.stats["success"],
                "failed_responses": self.stats["errors"],
                "success_rate": round(success_rate, 1),
                "validation_passed": self.stats["validation_passed"],
                "validation_failed": self.stats["validation_failed"],
                "validation_rate": round(validation_rate, 1),
                "average_duration": round(avg_duration, 3),
                "total_duration": round(self.stats["total_duration"], 2)
            },
            "category_stats": category_stats,
            "timestamp": datetime.now().isoformat(),
            "model": self.model
        }
    
    def save_results(self, filename: str = None) -> str:
        """Sauvegarde les résultats dans un fichier CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ecole_test_results_{timestamp}.csv"
        
        # Fichier CSV principal
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["question", "category", "language", "response", "duration", 
                         "status", "validation", "validation_score", "found_keywords"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                writer.writerow({
                    "question": result.question,
                    "category": result.category,
                    "language": result.language,
                    "response": result.response,
                    "duration": round(result.duration, 3),
                    "status": result.status,
                    "validation": result.validation,
                    "validation_score": result.validation_score,
                    "found_keywords": ", ".join(result.found_keywords) if result.found_keywords else ""
                })
        
        # Fichier JSON avec le rapport
        report = self.generate_report()
        json_filename = filename.replace('.csv', '_report.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return filename, json_filename

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Test automatisé de l'API École Jeanne d'Arc")
    parser.add_argument("--url", default=API_URL, help="URL de l'API")
    parser.add_argument("--model", default=MODEL, help="Modèle à utiliser")
    parser.add_argument("--delay", type=float, default=0.3, help="Délai entre les requêtes")
    parser.add_argument("--output", help="Nom du fichier de sortie (sans extension)")
    args = parser.parse_args()
    
    try:
        # Initialisation du testeur
        tester = APITester(args.url, args.model, SYSTEM_CONTEXT)
        
        # Exécution des tests
        tester.run_tests(QUESTIONS, args.delay)
        
        # Génération du rapport
        report = tester.generate_report()
        
        # Sauvegarde des résultats
        if args.output:
            csv_file = f"{args.output}.csv"
            json_file = f"{args.output}_report.json"
        else:
            csv_file, json_file = tester.save_results()
        
        # Affichage du résumé
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}  RAPPORT FINAL")
        print(f"{Fore.CYAN}{'='*70}")
        
        summary = report["summary"]
        print(f"{Fore.GREEN}✓ Questions totales: {summary['total_questions']}")
        print(f"{Fore.GREEN}✓ Réponses réussies: {summary['successful_responses']} ({summary['success_rate']}%)")
        print(f"{Fore.GREEN}✓ Validations passées: {summary['validation_passed']} ({summary['validation_rate']}%)")
        print(f"{Fore.RED}✗ Réponses échouées: {summary['failed_responses']}")
        print(f"{Fore.RED}✗ Validations échouées: {summary['validation_failed']}")
        print(f"{Fore.YELLOW}⏱ Durée moyenne: {summary['average_duration']}s")
        print(f"{Fore.YELLOW}⏱ Durée totale: {summary['total_duration']}s")
        
        print(f"\n{Fore.CYAN}{'-'*70}")
        print(f"{Fore.CYAN}  STATISTIQUES PAR CATÉGORIE")
        print(f"{Fore.CYAN}{'-'*70}")
        
        for category, stats in report["category_stats"].items():
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            validation_rate = (stats["passed"] / stats["success"]) * 100 if stats["success"] > 0 else 0
            print(f"{Fore.WHITE}{category:15} | "
                  f"{Fore.GREEN}Total: {stats['total']:2} | "
                  f"{Fore.CYAN}Succès: {stats['success']:2} ({success_rate:5.1f}%) | "
                  f"{Fore.YELLOW}Validation: {stats['passed']:2} ({validation_rate:5.1f}%)")
        
        print(f"\n{Fore.GREEN}✅ Fichiers sauvegardés:")
        print(f"   {Fore.WHITE}• {csv_file}")
        print(f"   {Fore.WHITE}• {json_file}")
        print(f"\n{Fore.CYAN}Test terminé à {datetime.now().strftime('%H:%M:%S')}")
        
        # Code de retour
        if summary["success_rate"] < 80 or summary["validation_rate"] < 80:
            print(f"\n{Fore.RED}⚠️  Attention: Taux de succès ou validation bas!")
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠  Test interrompu par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Fore.RED}✗ Erreur critique: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()