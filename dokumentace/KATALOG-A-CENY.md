# Katalog a odemykání v0.3

Snapshot 12. 11. 2026: 1 049 produktů a 1 231 objemových variant. Sortiment je převzat jako faktické názvy, objemy, obsah alkoholu a odkazy z veřejných kategorií L & M nápoje (https://www.lmnapoje.cz/alko/). Původní tři produkty mají navíc původní zdroje 700ml balení. Nejde o záruku úplného seznamu všech produktů dostupných v české gastronomii ani aktuální skladovou dostupnost.

Katalog pokrývá vodku, rumy, whisky, giny, tequily, likéry, pálenky a další lihoviny, brandy a koňaky, aperitivy a absinth. Nezahrnuje kompletní sortiment piva a vína. Záznamy jsou seskupeny podle názvu a obsahu alkoholu; jiné příchutě a síly mají samostatné položky. U každého objemu je zdrojový název, URL a produktová fotografie. Balíčky s příslušenstvím se při importu odfiltrovaly, ale některé obchodní varianty mohou zůstat jako samostatné položky. Data vyžadují průběžnou redakční kontrolu.

## Cena odemčení

Cena je za jeden katalogový produkt se všemi aktuálně uvedenými velikostmi, ne za každý objem zvlášť. Jde o cenu digitálního odemčení, nikoli cenu alkoholu.

- 2 Kč: vybrané běžné domácí lihoviny (např. Božkov, Hanácká, Fernet Stock).
- 4 Kč: základní vodky, likéry, aperitivy a pálenky.
- 5 Kč: základní giny a absinth.
- 6 Kč: základní rumy, whisky a tequily.
- 8 Kč: vybrané prémiové značky a brandy/koňaky.
- 10 Kč: vybrané luxusní řady (např. XO, Zacapa, Don Julio).

Finální přiřazení ceny každé položce je explicitní pole `unlockPrice` v katalogu. Ceny jsou produktové rozhodnutí pro tento prototyp, nikoli ověřené náklady na kalibraci.

## Tři zdarma

V zákaznickém náhledu jsou tři bezplatná odemčení podle vlastního výběru. Odemčení vyžaduje potvrzení. Čtvrtý a další produkt se bez platby neodemkne; dokud není platební brána, ukáže se vysvětlení a žádná platba se neprovede.

## Majitelský náhled

Majitel dostane aktivační odkaz. Token se neukládá do GitHubu, v aplikaci je pouze jeho SHA-256 otisk. Aktivace nabídne všechna odemčení za 0 Kč; musí se jednotlivě potvrdit. Odemčení neznamená přidání fyzické lahve do inventury.

Toto je lokální vývojový režim bez serverové autentizace. Stav lze v prohlížeči změnit a token není náhrada přihlášení. Nelze jej používat pro skutečně placené licence. Před produkčním prodejem je nutné přidat účty, serverová oprávnění, evidenci plateb a ověřené webhooky. Nový prohlížeč má vlastní lokální kvótu, nikoli celosvětově sdílený zákaznický limit.

## Měření

Žádná nově přidaná varianta nemá ověřenou kalibraci automatického měření. K dispozici je ruční zadání ml a aritmetické přepočty. Fotografie produktu není přesná silueta ani kalibrační tabulka.

## Fotografie

Tři původní fotografie jsou lokální soubory. Nový katalog načítá produktové fotografie ze zdrojových veřejných CDN adres; vyžadují internet a zdroj je může změnit. Při chybě se zobrazí zástupný stav. Práva k fotografiím zůstávají držitelům a licence pro komerční distribuci nebyla ověřena.

U 11 variant zdroj neměl produktovou fotografii; v aplikaci jsou výslovně označené „Fotografii doplníme“ a nepoužívá se fotografie jiného produktu.
