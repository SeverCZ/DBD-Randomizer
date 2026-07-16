import requests
import json
import os

# Konfigurace endpointů
API_URLS = {
    "perk_survivor": "https://dbd.tricky.lol/api/perks?role=survivor",
    "perk_killer": "https://dbd.tricky.lol/api/perks?role=killer",
    "survivor": "https://dbd.tricky.lol/api/characters?role=survivor",
    "killer": "https://dbd.tricky.lol/api/characters?role=killer",
    "survivor_offering": "https://dbd.tricky.lol/api/offerings?role=survivor",
    "killer_offering": "https://dbd.tricky.lol/api/offerings?role=killer",
    "items": "https://dbd.tricky.lol/api/items",
    "survivor_addons": "https://dbd.tricky.lol/api/addons?role=survivor",
    "killer_addons": "https://dbd.tricky.lol/api/addons?role=killer"
}

def update_database():
    print("Spouštím aktualizaci databáze (10 souborů)...")
    
    for name, url in API_URLS.items():
        filename = f"{name}.json"
        try:
            print(f"Stahuji: {name}...")
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Uložíme stažená data
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"OK: {filename} uložen.")
            else:
                print(f"CHYBA: Server vrátil kód {response.status_code} pro {name}")
                
        except Exception as e:
            print(f"CHYBA: Nepodařilo se stáhnout {name}. Důvod: {e}")

    print("\nAktualizace všech dat dokončena!")

if __name__ == "__main__":
    update_database()