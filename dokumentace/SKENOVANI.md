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

## Sekvenční inventura (0.6)

**Pořadí skenování** umožňuje přidat jednotlivé fyzické lahve včetně opakovaných produktů, zvolit objemy a místa nebo převzít existující řádky inventury. Šipkami lze pořadí měnit kdykoliv; z kamery tlačítkem **Změnit pořadí**. Plán, stav dokončení a vazby na fyzické lahve jsou uložené u účtu. Po návratu lze pokračovat zbývajícími lahvemi nebo začít nové kolo. Přeskočenou položku lze vrátit do fronty.

V režimu inventury se kamera otevírá rovnou pro další očekávanou lahev a ukazuje její název, objem, místo a následující produkt. Uživatel označí aktuální hladinu v živém obrazu a ověří horní a spodní referenci. **Skenovat, uložit a další** pořídí JPEG, vypočítá orientační objem, uloží snímek a měření a automaticky otevře další lahev. Nepoužívá se automatická detekce hladiny ani univerzální kalibrace tvaru. Při selhání ukládání zůstane stejná lahev otevřená a lze zkusit uložení znovu. ID snímku i měření je odvozené od kola a položky, aby opakování nepřidávalo duplicitní měření.

Snímky sekvenční inventury jsou oproti samostatnému skenu výslovně ukládané na serveru do databáze. V historii je odkaz na fotografii; endpoint ověřuje vlastníka účtu a neumožní jinému účtu snímek zobrazit ani přepsat. JPEG se na zařízení zmenšuje a komprimuje; jeho velikost kontroluje server. Když kamera není dostupná, vážení může uložit výsledek bez fotografie. Samostatný sken zůstává beze změny a nic neodesílá automaticky.

Živé vedení kontroluje světlost, stabilitu obrazu a na jednolitém kontrastním pozadí heuristicky odhaduje obrys a dává pokyny k vzdálenosti a vystředění. Když se obrys nedaří určit, nabídne ruční zarovnání. Tento odhad není identifikace produktu ani detekce hladiny. Volitelné vedení náklonu využívá DeviceOrientation po povolení uživatelem; bez podpory pokračuje ruční zarovnání. Barevný rámeček znamená vhodné podmínky náhledu, nikoliv ověřenou přesnost objemu.
