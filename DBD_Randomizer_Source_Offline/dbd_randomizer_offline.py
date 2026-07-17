import customtkinter as ctk
import random
import json
import os
import time
import sys

class DbdApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Nastavení ikonky okna (očekává app_icon.ico přibalený v exe)
        icon_path = os.path.join(self.get_base_path(), "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
            
        self.title("Dead by Daylight - Randomizer")
        self.geometry("600x850")
        
        self.settings_file = os.path.join(os.path.abspath("."), "user_settings.json")
        
        self.data = self.load_data()
        self.settings = self.load_settings()

        self.owned_survivors = {name: ctk.BooleanVar(value=self.settings.get("survivors", {}).get(name, False)) 
                                for name in self.data["survivors"]}
        self.owned_killers = {obj["name"]: ctk.BooleanVar(value=self.settings.get("killers", {}).get(obj["name"], False)) 
                              for obj in self.data["killers"]}

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_gen = self.tabview.add("Generování")
        self.tab_set = self.tabview.add("Postavy")

        self.setup_generator()
        self.setup_characters()

    def get_base_path(self):
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return os.path.abspath(".")

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f: return json.load(f)
            except: pass
        return {"survivors": {}, "killers": {}}

    def save_settings(self):
        settings = {
            "survivors": {name: var.get() for name, var in self.owned_survivors.items()},
            "killers": {name: var.get() for name, var in self.owned_killers.items()}
        }
        with open(self.settings_file, 'w') as f: json.dump(settings, f)

    def load_data(self):
        base_path = self.get_base_path()
        def get_json(filename):
            filepath = os.path.join(base_path, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
            else:
                print(f"CHYBA: Nemohu najít soubor na cestě -> {filepath}")
            return {}

        s_raw = get_json("survivor.json")
        k_raw = get_json("killer.json")
        p_surv = get_json("perk_survivor.json")
        p_kill = get_json("perk_killer.json")
        off_surv = get_json("survivor_offering.json")
        off_kill = get_json("killer_offering.json")
        items_raw = get_json("items.json")
        addons_surv = get_json("survivor_addons.json")
        addons_kill = get_json("killer_addons.json")

        # Pomocná funkce pro bezpečné vytažení hodnot (pokud JSON vrátí dict)
        def get_vals(data):
            return list(data.values()) if isinstance(data, dict) else data

        return {
            "survivors_raw": get_vals(s_raw), # Uchování celých objektů přeživších kvůli perkům
            "survivors": [s["name"] for s in get_vals(s_raw) if isinstance(s, dict) and "name" in s],
            "killers": get_vals(k_raw),
            "perks_raw": { # Uchování surových slovníků s vazbami na postavy (character ID / null)
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
        
        # Checkbox pro Custom Game
        self.check_custom = ctk.CTkCheckBox(self.options_frame, text="Custom Game")
        self.check_custom.pack(side="left", padx=10)
        
        ctk.CTkButton(self.tab_gen, text="Generovat", command=self.generate).pack(pady=20)
        self.result_label = ctk.CTkLabel(self.tab_gen, text="Zde se zobrazí výsledek", font=("Arial", 12), justify="left")
        self.result_label.pack()

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

    def toggle_all(self, var_dict, state):
        for var in var_dict.values(): var.set(state)
        self.save_settings()

    def setup_characters(self):
        container = ctk.CTkFrame(self.tab_set, fg_color="transparent")
        container.pack(fill="both", expand=True)
        col_s = ctk.CTkScrollableFrame(container, label_text="Survivors")
        col_s.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkButton(col_s, text="Vše", width=60, command=lambda: self.toggle_all(self.owned_survivors, True)).pack()
        ctk.CTkButton(col_s, text="Nic", width=60, command=lambda: self.toggle_all(self.owned_survivors, False)).pack()
        for name in self.data["survivors"]:
            ctk.CTkCheckBox(col_s, text=name, variable=self.owned_survivors[name], command=self.save_settings).pack(anchor="w", padx=10, pady=2)
        col_k = ctk.CTkScrollableFrame(container, label_text="Killers")
        col_k.pack(side="right", fill="both", expand=True, padx=5)
        ctk.CTkButton(col_k, text="Vše", width=60, command=lambda: self.toggle_all(self.owned_killers, True)).pack()
        ctk.CTkButton(col_k, text="Nic", width=60, command=lambda: self.toggle_all(self.owned_killers, False)).pack()
        for obj in self.data["killers"]:
            ctk.CTkCheckBox(col_k, text=obj["name"], variable=self.owned_killers[obj["name"]], command=self.save_settings).pack(anchor="w", padx=10, pady=2)

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
        
        # --- LOGIKA VÝBĚRU PERKŮ PODLE CUSTOM GAME ---
        if self.check_custom.get():
            # Pokud je Custom Game aktivní, bere se kompletně celý pool bez omezení
            pool = list(self.data["perks"].get(role.lower(), []))
        else:
            # Pokud Custom Game aktivní NENÍ, filtrujeme perky podle označených postav
            selected_perk_keys = set()
            if role == "Survivor":
                for s in self.data.get("survivors_raw", []):
                    if isinstance(s, dict) and s.get("name") in choices_objs:
                        for p_key in s.get("perks", []):
                            selected_perk_keys.add(p_key)
            else:
                for k in choices_objs:
                    if isinstance(k, dict):
                        for p_key in k.get("perks", []):
                            selected_perk_keys.add(p_key)
            
            pool = []
            perks_dict = self.data.get("perks_raw", {}).get(role.lower(), {})
            for p_key, p_info in perks_dict.items():
                if isinstance(p_info, dict):
                    # Podmínka: buď je perk obecný (character: null) nebo patří k označené postavě
                    if p_info.get("character") is None or p_key in selected_perk_keys:
                        pool.append(p_info["name"])
        # ---------------------------------------------
        
        random.shuffle(pool) 
        perks_text = "\n".join([f"• {p}" for p in pool[:num_perks]])
        
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
                        item_text += f"\nAddony: {', '.join(random.sample(addons_pool, min(2, len(addons_pool))))}" if addons_pool else "\nAddony: Žádné"
            elif self.check_addons.get():
                killer_item_id = next((obj["item"] for obj in self.data["killers"] if obj["name"] == chosen_char_name), None)
                if killer_item_id:
                    addons_pool = [a['name'] for a in self.data["addons_killer"] if killer_item_id in a.get("parents", [])]
                    item_text = f"\nAddony: {', '.join(random.sample(addons_pool, min(2, len(addons_pool))))}" if addons_pool else "\nAddony: Žádné"

        self.result_label.configure(text=f"Postava: {chosen_char_name}{offering_text}{item_text}\n\nVybrané perky:\n{perks_text}")

if __name__ == "__main__":
    app = DbdApp()
    app.mainloop()