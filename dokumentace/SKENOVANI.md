# Skenování lahví

V účtové aplikaci otevřete odemčený produkt, vyberte skutečný objem a zvolte **Přidat lahev do inventury → Spustit skenování**. Existující fyzickou lahev měřte tlačítkem v její řádce inventury.

Průvodce ověří etiketu a objem, vysvětlí přípravu, otevře zadní kameru přes celou plochu a nabídne kontrolu výsledku. Použije Fullscreen API tam, kde je dostupné; jinak překryje celý viewport. Při zavření, navigaci nebo skrytí aplikace kameru vypne. Osvětlení a změny mezi snímky pomáhají uživateli stabilizovat obraz, ale nedokazují správné rozpoznání lahve či hladiny.

## Identita lahve

V prohlížečích s podporou BarcodeDetector se EAN/UPC načte automaticky z živého náhledu. Jinde lze kód opsat. Kontroluje se formát i kontrolní číslice. Po stisknutí Dohledat server vyhledá údaje v Open Food Facts. Nalezený název a objem musí uživatel porovnat s etiketou a vybraným produktem. Výsledek databáze automaticky nemění produkt a chybějící záznam nebrání měření. Kód neidentifikuje jednotlivou fyzickou lahev; tu rozlišuje řádek inventury.

Zdroj: [Open Food Facts API](https://openfoodfacts.github.io/openfoodfacts-server/api/tutorial-off-api/), data [ODbL](https://world.openfoodfacts.org/data). Náhledy kamery zůstávají na zařízení; server dostává pouze zadaný kód. Přístup k lookup endpointu vyžaduje přihlášení a má časový limit i omezení četnosti.

## Obsah lahve a přesnost

- **Kalibrované vážení:** `objem = kapacita × (aktuální hmotnost − prázdná) / (plná − prázdná)`. Uživatel zadává vlastní hmotnosti pro stejnou variantu, obsah, víčko a příslušenství. Nepoužívá se odhad hustoty podle procent alkoholu ani internetová hmotnost obecné lahve. Kalibrace se uloží k fyzické lahvi a nabídne při dalším měření. Tolerance není ověřena; závisí na váze, shodě táry a skutečném objemu při kalibraci.
- **Vizuální odečet:** uživatel označí na zastaveném náhledu plnou hladinu, současnou hladinu a vnitřní dno. Přepočet je použitelný jen pro stálý průřez a viditelnou hladinu, což musí potvrdit. Výsledek je orientační, zaokrouhlený na 10 ml. U ramen, tvarovaných lahví, tmavého skla a zakryté hladiny se má použít vážení. Nejde o automatické rozpoznávání hladiny ani kalibrovanou siluetu produktu.
- **Ruční údaj:** lze dál zapsat vlastní měření. Původ výsledku se zobrazuje v rozboru a historii.

Po kontrole průvodce následuje samostatné potvrzení uložení do inventury. Neúspěšné uložení nehlásí úspěch a obnoví předchozí místní stav.

## Ověření

`node tests/scanner-math.cjs` ověřuje checksum a výpočet hmotnosti včetně hraničních a neplatných vstupů. `python -m pytest -q` ověřuje účty a API včetně online lookupu s řízenými odpověďmi. Mobilní browser test používá simulovanou kameru Chromium; reálná optická přesnost a chování fyzických kamer iOS/Android musí být ověřeny na zařízeních a známých objemech.
