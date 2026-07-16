# Dead by Daylight - Randomizer

Jednoduchá a přehledná desktopová aplikace napsaná v Pythonu, která slouží k náhodnému generování vybavení pro hru Dead by Daylight. Umožňuje hráčům vybrat si své vlastněné postavy a následně jim náhodně vygeneruje postavu, perky, offering, itemy a addony pro další hru.

Aplikace si navíc pamatuje, které postavy máte odemčené, takže to nemusíte při každém spuštění nastavovat znovu.

## Hlavní funkce

* **Podpora pro obě role:** Oddělené generování pro Survivory a Killery se specifickými pravidly (Killer má pouze addony, Survivor může mít i item).
* **Chytré filtry:** Addony se u Survivora vygenerují pouze v případě, že vygenerovaný item dává smysl. Generují se jen platné předměty a vynechávají se limitované (event) předměty.
* **Paměť nastavení:** Zaškrtnuté postavy se ukládají do lokálního souboru `user_settings.json`.

## Verze aplikace

Tento projekt obsahuje dvě verze kódu, aby si uživatel mohl vybrat, co mu více vyhovuje:

### 1. Online verze (API)
* **Popis:** Při spuštění automaticky stahuje nejnovější data o hře z veřejného API (Tricky.lol).
* **Výhody:** Aplikace je vždy aktuální bez nutnosti updatovat zdrojové soubory, když vyjde nová DBD kapitola. Výsledný `.exe` soubor je velmi malý.
* **Nevýhody:** Ke spuštění a běhu potřebuje funkční připojení k internetu (při startu chvilku trvá načtení dat).

### 2. Offline verze (JSON)
* **Popis:** Spoléhá se na lokální `.json` soubory (`survivor.json`, `killer.json`, `items.json`, atd.), které musí být stažené ve stejné složce.
* **Výhody:** Nevyžaduje připojení k internetu a zapíná se okamžitě.
* **Nevýhody:** Když vyjde nový Killer/Survivor, musíte manuálně aktualizovat.

## Požadavky a spuštění
Exe soubor pro spuštění se nachází v daných složkách verze v podsložce dist, stačí stáhnout pouze daný soubor.

Pokud chcete aplikaci spouštět ze zdrojového kódu (Python skriptu), musíte mít nainstalovaný Python a následující knihovny:

```bash
pip install customtkinter requests