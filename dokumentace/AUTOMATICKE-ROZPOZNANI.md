# Automatické rozpoznávání hladiny — integrace 0.9

## Co je hotové a co zatím ověřené není

Kód umí odebrat dva po sobě jdoucí snímky ze stabilního náhledu, poslat je do nakonfigurovaného vision modelu a zpracovat odpověď bez ručního označování hladiny. Po přijetí výsledku se použije dosavadní uložení snímku a měření a otevře se další lahev. Před další automatickou analýzou musí uživatel odstranit předchozí lahev ze záběru a vložit další. Tím se omezuje automatické opakované započtení statického obrazu.

**Nejde o hotový a na reálných lahvích validovaný měřicí systém.** Automatické čtení není v produkci aktivní, dokud není připojený a výslovně povolený model. Provedené testy používají simulovanou kameru a naprogramované odpovědi poskytovatele. Ověřují API a průchod aplikací, nikoli skutečnou přesnost AI. Dosud nebyla stanovena přesnost, pokrytí značek ani spolehlivost odlišení etikety od menisku. Shoda dvou snímků nedokazuje správnost odhadu.

## Připojení na Renderu

V službě `barometr-app`, v sekci **Environment**, nastavte bezpečně:

- `OPENAI_API_KEY`: klíč projektu OpenAI API s příslušným oprávněním a dostupným kreditem. Nepatří do chatu ani GitHubu.
- `BAROMETR_AUTO_LEVEL_ENABLED`: `0` nebo vynechat pro vypnutí; `1` pro výslovné povolení analýzy.
- `BAROMETR_VISION_MODEL`: volitelně model podporující obrazové vstupy a strict JSON schema; výchozí je `gpt-4.1`.

Změny vyžadují nasazení s novými proměnnými. Stav v nastavení aplikace a `/api/vision/status` potvrzuje pouze přítomnost konfigurace a příznaku povolení. Neověřuje platnost klíče, kredit ani přesnost modelu; to se prověří skutečným požadavkem. `/healthz` zobrazuje pouze boolean `automaticLevelEnabled`, nikdy hodnotu klíče.

Nejprve proveďte řízené testy se známými objemy mimo provozní inventuru. Nastavte rozpočtový limit API projektu. Analýza je placená služba oddělená od přihlášení do ChatGPT. Bez konfigurace nic nevydává síťové požadavky poskytovateli a automatické uložení neproběhne. Ruční odečet a vážení zůstávají výslovně volitelné alternativy.

## Zpracování

1. Kontrola světla, stability a případně náklonu zůstává lokální.
2. Dva záběry s odstupem 650 ms používají stejný viditelný výřez jako celoobrazovkový náhled. Další kontrola rozdílu pixelů brání odeslání zřetelně pohnutého obrazu.
3. Zmenšené JPEG se odesílají přes autentizovaný serverový endpoint `/api/vision/analyze` do OpenAI Responses API. Klíč zůstává na serveru a nastavuje se `store: false`. Živý video stream se neodesílá. Uživatel dostává tuto informaci přímo ve skeneru.
4. Model má vrátit počet lahví, shodu produktu, viditelnost hladiny, viditelnost celého těla, vhodnost průřezu a tři normalizované souřadnice pro každý snímek. Nesmí nahrazovat hladinu etiketou a má odmítnout skrytou hladinu i nejasné reference. Server ověřuje typy, rozsahy, pořadí referencí a shodu obou záběrů.
5. U přijatého obrazu se z výšky pro stálý průřez vypočítá **orientační** objem zaokrouhlený na 10 ml. Souřadnice ani průřez nejsou fyzickou kalibrací. Záznam nese `method: vision-estimate`, `calibrated: false` a viditelný popis neověřené přesnosti.
6. Nečitelné, rozporné, neprůhledné, tvarované nebo chybně identifikované lahve se nemají uložit automaticky. Neurčené či neplatné reference se odmítají. Zcela plná nebo prázdná lahev bez zřetelného menisku se tímto režimem automaticky nevyhodnocuje.
7. Po odmítnutí nebo chybě se další placený požadavek nespouští ve smyčce. Uživatel musí po změně záběru zvolit nový pokus. Server omezuje počet pokusů na účet. Zavření nebo změna režimu zruší čekající klientský požadavek; nelze tím zaručit zrušení už zahájeného zpracování u poskytovatele.

## Hranice současného řešení

Výstup obecného vision modelu může být chybný i při splnění všech kontrol. Modelové flagy nejsou nezávislé důkazy a nepoužívá se z nich vymyšlené procento přesnosti. Současná geometrie vyžaduje stálý průřez a čitelné reference; neřeší všechny běžné barové lahve. Pro tvarované lahve a důvěryhodné ml je nutná ověřená kalibrace variant nebo vážení. Rozpoznání hladiny a přesný převod na objem jsou odlišné úlohy.

## Ověření před provozem

Potřebujeme skutečné fotografie několika známých objemů každé podporované varianty, různé telefony, úhly, pozadí a světelné podmínky. Zvlášť je nutné zahrnout negativní příklady: etikety na úrovni hladiny, tmavé sklo, prázdné/plné lahve, dvě lahve v záběru, odlesky a nevhodný produkt. Měřit se má chybná akceptace, odmítání a chyba v ml vůči referenci; současné kontraktové testy tyto metriky neposkytují.

## Reference

- [OpenAI: obrazové vstupy a omezení](https://developers.openai.com/api/docs/guides/images-vision)
- [OpenAI: strukturované odpovědi](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Render: proměnné prostředí a tajné údaje](https://render.com/docs/configure-environment-variables)
- [Vector-LabPics: výzkum segmentace materiálů v nádobách](https://pmc.ncbi.nlm.nih.gov/articles/PMC7596871/) — příklad potřebných trénovacích a validačních dat; v tomto projektu se tento model ani dataset nepoužívá.
