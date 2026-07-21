import customtkinter as ctk
import random
import json
import os
import time
import sys
import requests

class DbdApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Nastavení ikonky okna
        icon_path = os.path.join(self.get_base_path(), "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
            
        self.title("Dead by Daylight - Randomizer")
        self.geometry("600x850")
        
        # --- OPRAVA UKLÁDÁNÍ PRO .EXE ---
        if getattr(sys, 'frozen', False):
            exe_folder = os.path.dirname(sys.executable)
            self.settings_file = os.path.join(exe_folder, "user_settings.json")
        else:
            self.settings_file = os.path.join(self.get_base_path(), "user_settings.json")
        # --------------------------------
        
        # Načtení a zpracování dat
        self.data = self.load_data()
        self.parse_perks()
        self.settings = self.load_settings()
        
        # Uložená velikost písma pro výsledek (výchozí 12)
        self.result_font_size = self.settings.get("result_font_size", 12)
        
        self.init_variables()

        # Tvorba záložek
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_gen = self.tabview.add("Generování")
        self.tab_set = self.tabview.add("Postavy")
        self.tab_perks = self.tabview.add("Perky")
        self.tab_setts = self.tabview.add("Nastavení") 

        self.setup_generator()
        self.setup_characters()
        self.setup_perks()
        self.setup_settings() 

    def get_base_path(self):
        # Spolehlivé určení cesty (oprava pro Linux/WSL i pro zabalené .exe)
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return os.path.dirname(os.path.abspath(__file__))

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f: return json.load(f)
            except: pass
        return {"survivors": {}, "killers": {}, "perks": {"survivor": {}, "killer": {}}, "result_font_size": 12}

    def save_settings(self):
        settings = {
            "survivors": {name: var.get() for name, var in self.owned_survivors.items()},
            "killers": {name: var.get() for name, var in self.owned_killers.items()},
            "perks": {
                "survivor": {p_name: var.get() for p_name, var in self.perk_vars["survivor"].items()},
                "killer": {p_name: var.get() for p_name, var in self.perk_vars["killer"].items()}
            },
            "result_font_size": self.result_font_size 
        }
        with open(self.settings_file, 'w') as f: json.dump(settings, f)

    def load_data(self):
        def get_api(url):
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"Chyba při stahování API {url}: {e}")
                return {}

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

        s_raw = get_api(API_URLS["survivor"])
        k_raw = get_api(API_URLS["killer"])
        p_surv = get_api(API_URLS["perk_survivor"])
        p_kill = get_api(API_URLS["perk_killer"])
        off_surv = get_api(API_URLS["survivor_offering"])
        off_kill = get_api(API_URLS["killer_offering"])
        items_raw = get_api(API_URLS["items"])
        addons_surv = get_api(API_URLS["survivor_addons"])
        addons_kill = get_api(API_URLS["killer_addons"])

        def get_vals(data):
            return list(data.values()) if isinstance(data, dict) else data

        return {
            "survivors_raw": get_vals(s_raw),
            "survivors": [s["name"] for s in get_vals(s_raw) if isinstance(s, dict) and "name" in s],
            "killers": get_vals(k_raw),
            "perks_raw": {
                "survivor": p_surv if isinstance(p_surv, dict) else {},
                "killer": p_kill if isinstance(p_kill, dict) else {}
            },
            "perks": {
                "survivor": [item["name"] for item in get_vals(p_surv) if isinstance(item, dict) and "name" in item],
                "killer": [item["name"] for item in get_vals(p_kill) if isinstance(item, dict) and "name" in item]
            },
            "offerings": {
                "survivor": [item["name"] for item in get_vals(off_surv) if isinstance(item, dict) and "name" in item],
                "killer": [item["name"] for item in get_vals(off_kill) if isinstance(item, dict) and "name" in item]
            },
            "items": [
                {"name": val["name"], "item_type": val.get("item_type")} 
                for val in get_vals(items_raw) 
                if isinstance(val, dict) and val.get("type") == "item" and val.get("role") == "survivor" and "/Limited/" not in val.get("image", "")
            ],
            "addons_survivor": [
                {"name": val["name"], "item_type": val.get("item_type")}
                for val in get_vals(addons_surv) if isinstance(val, dict) and "name" in val
            ],
            "addons_killer": get_vals(addons_kill) 
        }

    def parse_perks(self):
        """Roztřídí perky na 'General' a ty, které patří jednotlivým postavám."""
        self.perks_by_char = {"survivor": {}, "killer": {}}
        self.general_perks = {"survivor": [], "killer": []}

        for role in ["survivor", "killer"]:
            assigned_perk_names = set()
            raw_chars = self.data["survivors_raw"] if role == "survivor" else self.data["killers"]
            raw_perks = self.data["perks_raw"][role]

            for char in raw_chars:
                if not isinstance(char, dict) or "name" not in char: continue
                char_name = char["name"]
                char_perk_keys = char.get("perks", [])
                char_perk_names = []
                for p_key in char_perk_keys:
                    if p_key in raw_perks and "name" in raw_perks[p_key]:
                        p_name = raw_perks[p_key]["name"]
                        char_perk_names.append(p_name)
                        assigned_perk_names.add(p_name)
                self.perks_by_char[role][char_name] = char_perk_names

            # Perky, které nepatří žádné postavě, jsou General
            for p_key, p_data in raw_perks.items():
                if isinstance(p_data, dict) and "name" in p_data:
                    p_name = p_data["name"]
                    if p_name not in assigned_perk_names:
                        self.general_perks[role].append(p_name)
                        
            self.general_perks[role].sort()

    def init_variables(self):
        """Příprava všech Boolean proměnných pro Checkboxy."""
        self.owned_survivors = {name: ctk.BooleanVar(value=self.settings.get("survivors", {}).get(name, False)) 
                                for name in self.data["survivors"]}
        self.owned_killers = {obj["name"]: ctk.BooleanVar(value=self.settings.get("killers", {}).get(obj["name"], False)) 
                              for obj in self.data["killers"]}

        self.perk_vars = {"survivor": {}, "killer": {}}
        saved_perks = self.settings.get("perks", {"survivor": {}, "killer": {}})
        
        for role in ["survivor", "killer"]:
            # General perky jsou automaticky True (pokud si je uživatel už ručně nevypnul)
            for p_name in self.general_perks[role]:
                val = saved_perks.get(role, {}).get(p_name, True)
                self.perk_vars[role][p_name] = ctk.BooleanVar(value=val)
                
            # Perky postav kopírují to, zda postavu vlastníme (pokud není uložen ruční zásah)
            for char_name, p_names in self.perks_by_char[role].items():
                is_owned = self.owned_survivors[char_name].get() if role == "survivor" else self.owned_killers[char_name].get()
                for p_name in p_names:
                    if role in saved_perks and p_name in saved_perks[role]:
                        val = saved_perks[role][p_name]
                    else:
                        val = is_owned
                    self.perk_vars[role][p_name] = ctk.BooleanVar(value=val)

    def toggle_character(self, role, char_name):
        """Zavolá se při kliknutí na postavu - synchronizuje její 3 perky."""
        is_owned = self.owned_survivors[char_name].get() if role == "survivor" else self.owned_killers[char_name].get()
        # Automatické označení/odoznačení jejích 3 perků
        for p_name in self.perks_by_char[role].get(char_name, []):
            self.perk_vars[role][p_name].set(is_owned)
        self.save_settings()

    def toggle_all_characters(self, role, state):
        """Zavolá se při kliknutí na tlačítka Vše/Nic."""
        char_dict = self.owned_survivors if role == "survivor" else self.owned_killers
        for char_name, var in char_dict.items():
            var.set(state)
            # Upravit i perky
            for p_name in self.perks_by_char[role].get(char_name, []):
                self.perk_vars[role][p_name].set(state)
        self.save_settings()

    def setup_generator(self):
        self.role_var = ctk.StringVar(value="Survivor")
        self.role_switch = ctk.CTkSegmentedButton(self.tab_gen, values=["Survivor", "Killer"], 
                                                variable=self.role_var, command=self.update_ui)
        self.role_switch.pack(pady=10)
        
        ctk.CTkLabel(self.tab_gen, text="Počet perků (0-4):").pack()
        self.perk_slider = ctk.CTkSlider(self.tab_gen, from_=0, to=4, number_of_steps=4)
        self.perk_slider.set(4)
        self.perk_slider.pack(pady=10)
        
        self.options_frame = ctk.CTkFrame(self.tab_gen, fg_color="transparent")
        self.options_frame.pack(pady=15)
        
        self.check_offering = ctk.CTkCheckBox(self.options_frame, text="Zahrnout Offering")
        self.check_offering.pack(side="left", padx=10)
        
        self.check_item = ctk.CTkCheckBox(self.options_frame, text="Zahrnout Item", command=self.toggle_addon_visibility)
        self.check_item.pack(side="left", padx=10)
        
        self.check_addons = ctk.CTkCheckBox(self.options_frame, text="Zahrnout Addony")
        
        self.check_custom = ctk.CTkCheckBox(self.options_frame, text="Custom Game")
        self.check_custom.pack(side="left", padx=10)
        
        ctk.CTkButton(self.tab_gen, text="Generovat", command=self.generate).pack(pady=20)
        
        self.result_label = ctk.CTkLabel(self.tab_gen, text="Zde se zobrazí výsledek", font=("Arial", self.result_font_size), justify="left")
        self.result_label.pack()

    def setup_settings(self):
        ctk.CTkLabel(self.tab_setts, text="Velikost textu výsledku:", font=("Arial", 13, "bold")).pack(pady=20)
        
        self.result_font_slider = ctk.CTkSlider(self.tab_setts, from_=10, to=28, number_of_steps=18, command=self.update_result_font)
        self.result_font_slider.set(self.result_font_size)
        self.result_font_slider.pack(pady=10)
        
        ctk.CTkLabel(self.tab_setts, text="(Změna se projeví okamžitě u vygenerovaného textu)", font=("Arial", 11)).pack(pady=10)

    def update_result_font(self, value):
        self.result_font_size = int(value)
        self.result_label.configure(font=("Arial", self.result_font_size))
        self.save_settings()

    def toggle_addon_visibility(self):
        if self.role_var.get() == "Survivor":
            if self.check_item.get():
                self.check_addons.pack(side="left", padx=10) 
            else:
                self.check_addons.pack_forget()
                self.check_addons.deselect()

    def update_ui(self, role):
        self.check_item.pack_forget()
        self.check_addons.pack_forget()
        
        if role == "Killer": 
            self.check_addons.pack(side="left", padx=10)
        else: 
            self.check_item.pack(side="left", padx=10)
            self.toggle_addon_visibility()

    def setup_characters(self):
        container = ctk.CTkFrame(self.tab_set, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        col_s = ctk.CTkScrollableFrame(container, label_text="Survivors")
        col_s.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkButton(col_s, text="Vše", width=60, command=lambda: self.toggle_all_characters("survivor", True)).pack()
        ctk.CTkButton(col_s, text="Nic", width=60, command=lambda: self.toggle_all_characters("survivor", False)).pack()
        for name in self.data["survivors"]:
            ctk.CTkCheckBox(col_s, text=name, variable=self.owned_survivors[name], 
                            command=lambda r="survivor", c=name: self.toggle_character(r, c)).pack(anchor="w", padx=10, pady=2)
            
        col_k = ctk.CTkScrollableFrame(container, label_text="Killers")
        col_k.pack(side="right", fill="both", expand=True, padx=5)
        ctk.CTkButton(col_k, text="Vše", width=60, command=lambda: self.toggle_all_characters("killer", True)).pack()
        ctk.CTkButton(col_k, text="Nic", width=60, command=lambda: self.toggle_all_characters("killer", False)).pack()
        for obj in self.data["killers"]:
            k_name = obj["name"]
            ctk.CTkCheckBox(col_k, text=k_name, variable=self.owned_killers[k_name], 
                            command=lambda r="killer", c=k_name: self.toggle_character(r, c)).pack(anchor="w", padx=10, pady=2)

    def setup_perks(self):
        """Vygenerování vizuálu pro třetí záložku 'Perky'."""
        container = ctk.CTkFrame(self.tab_perks, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        col_s = ctk.CTkScrollableFrame(container, label_text="Survivor Perky")
        col_s.pack(side="left", fill="both", expand=True, padx=5)
        
        col_k = ctk.CTkScrollableFrame(container, label_text="Killer Perky")
        col_k.pack(side="right", fill="both", expand=True, padx=5)
        
        for role, col in [("survivor", col_s), ("killer", col_k)]:
            # 1. Nejdříve vykreslíme General perky
            if self.general_perks[role]:
                # Nadpis sekce General
                lbl = ctk.CTkLabel(col, text="General", font=("Arial", 13, "bold"), text_color=("gray10", "gray90"))
                lbl.pack(anchor="w", pady=(10, 0))
                for p_name in self.general_perks[role]:
                    ctk.CTkCheckBox(col, text=p_name, variable=self.perk_vars[role][p_name], 
                                    command=self.save_settings).pack(anchor="w", padx=10, pady=2)
            
            # 2. Vykreslíme perky sdružené pod jednotlivými postavami
            char_list = self.data["survivors"] if role == "survivor" else [k["name"] for k in self.data["killers"]]
            for char_name in char_list:
                p_names = self.perks_by_char[role].get(char_name, [])
                if p_names:
                    # Nadpis jména postavy
                    lbl = ctk.CTkLabel(col, text=char_name, font=("Arial", 13, "bold"), text_color=("gray10", "gray90"))
                    lbl.pack(anchor="w", pady=(10, 0))
                    # 3 Checkboxy Perkủ pro danou postavu
                    for p_name in p_names:
                        ctk.CTkCheckBox(col, text=p_name, variable=self.perk_vars[role][p_name], 
                                        command=self.save_settings).pack(anchor="w", padx=10, pady=2)

    def generate(self):
        random.seed(time.time_ns())
        role = self.role_var.get()
        num_perks = int(self.perk_slider.get())
        
        if role == "Survivor": choices_objs = [name for name, var in self.owned_survivors.items() if var.get()]
        else: choices_objs = [obj for obj in self.data["killers"] if self.owned_killers.get(obj["name"], ctk.BooleanVar()).get()]
        
        if not choices_objs:
            self.result_label.configure(text="Neoznačil jsi žádnou postavu!")
            return
            
        chosen_char_name = random.choice(choices_objs) if role == "Survivor" else random.choice(choices_objs)["name"]
        
        # --- LOGIKA VÝBĚRU PERKŮ (Custom Game vs Omezený výběr) ---
        if self.check_custom.get():
            pool = list(self.data["perks"].get(role.lower(), []))
        else:
            pool = [p_name for p_name, var in self.perk_vars[role.lower()].items() if var.get()]
        # ---------------------------------------------------------
        
        random.shuffle(pool) 
        perks_text = "\n".join([f"• {p}" for p in pool[:num_perks]])
        if not perks_text:
            perks_text = "Žádné perky nebyly nalezeny (všechny jsi odškrtl)!"
        
        offering_text = f"\nOffering: {random.choice(self.data['offerings'].get(role.lower(), ['Žádný']))}" if self.check_offering.get() else ""
        
        item_text = ""
        if self.check_item.get() or self.check_addons.get():
            if role == "Survivor":
                valid_items = [i for i in self.data["items"] if i.get("item_type") is not None]
                if valid_items:
                    chosen_item = random.choice(valid_items)
                    item_text = f"\nItem: {chosen_item['name']}" if self.check_item.get() else ""
                    if self.check_addons.get():
                        addons_pool = [a['name'] for a in self.data["addons_survivor"] if a.get('item_type') == chosen_item.get('item_type')]
                        if addons_pool:
                            sampled = random.sample(addons_pool, min(2, len(addons_pool)))
                            if len(sampled) == 2:
                                item_text += f"\nAddony: {sampled[0]}\n              {sampled[1]}"
                            else:
                                item_text += f"\nAddony: {sampled[0]}"
                        else:
                            item_text += "\nAddony: Žádné"
            elif self.check_addons.get():
                killer_item_id = next((obj["item"] for obj in self.data["killers"] if obj["name"] == chosen_char_name), None)
                if killer_item_id:
                    addons_pool = [a['name'] for a in self.data["addons_killer"] if killer_item_id in a.get("parents", [])]
                    if addons_pool:
                        sampled = random.sample(addons_pool, min(2, len(addons_pool)))
                        if len(sampled) == 2:
                            item_text = f"\nAddony: {sampled[0]}\n              {sampled[1]}"
                        else:
                            item_text = f"\nAddony: {sampled[0]}"
                    else:
                        item_text = "\nAddony: Žádné"

        self.result_label.configure(text=f"Postava: {chosen_char_name}{offering_text}{item_text}\n\nVybrané perky:\n{perks_text}")

if __name__ == "__main__":
    app = DbdApp()
    app.mainloop()