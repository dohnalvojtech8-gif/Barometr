# BAROMETR v0.3

Katalog a prototyp inventury pro české bary. **1 049 produktů, 1 231 doložených objemových variant, 10 kategorií.**

[Otevřít aplikaci](https://barometr-2.onrender.com/?v=0.3.0#catalog)

## Funkce

- Katalog se skutečnými produktovými fotografiemi, vyhledáváním, kategoriemi a stránkováním.
- Tři produkty zdarma podle vlastního výběru; ceny dalších 2–10 Kč.
- Potvrzení odemčení a samostatná knihovna „Moje lahve“.
- Majitelský vývojový náhled s ručním odemykáním za 0 Kč.
- Více fyzických lahví jednoho produktu, ruční objem v ml, přepočty na 20/40ml panáky.
- Prodeje, ostatní výdej, porovnání měření a místní historie s označením cyklu.

**Platby nejsou spuštěné. Automatické měření fotografií ani OCR váhy nejsou implementované.** Odemčení a kvóta jsou zatím místní stav prohlížeče, nikoli serverově ověřené licence nebo účty. Katalog je široký snapshot českého dodavatele, ne úplný seznam celého trhu.

## Spuštění a kontrola

```sh
python3 -m http.server 8080 --directory aplikace
node scripts/overit.cjs
node scripts/sestavit-nahledy.cjs
```

Otevřete `http://localhost:8080`. Bez instalačních závislostí. Skript sestavení vytváří `02-INTERAKTIVNI-APLIKACE.html`; fotografie nového katalogu vyžadují internet. Soubor `01-VSECHNY-OBRAZOVKY.html` je archivní statický design v0.2, nikoli aktuální katalog.

Na Renderu se používá Static Site bez build příkazu. Zdroj je v `aplikace/`; symbolický odkaz `Aplikace` zachovává kompatibilitu s existujícím nastavením služby.

## Dokumentace

- [Katalog, ceny, zdroje a omezení](dokumentace/KATALOG-A-CENY.md)
- [Přidávání lahví](dokumentace/PRIDAVANI-LAHVI.md)
- [Původní fotografie](dokumentace/ZDROJE-OBRAZKU.md)

Nové záznamy jsou v `aplikace/catalog-data.js`. U varianty jsou objem, fotografie a odkaz na zdroj. Cena produktu je pole `unlockPrice`. Před reálným prodejem je potřeba doplnit účty, platební bránu, serverová oprávnění a vyřešit práva k fotografiím. Před automatickým měřením kalibraci konkrétních obalů.

## Prohlížečové ověření

`scripts/test-browser.cjs` kontroluje tři zdarma, zablokovaný čtvrtý produkt, majitelský náhled, vyhledávání, kategorie, ukládání a historii. Vyžaduje Playwright a Chromium (`npm install --no-save playwright`, `npx playwright install chromium`). Cílovou adresu lze nastavit proměnnou `TEST_URL`, vlastní Chromium proměnnou `CHROMIUM_PATH`. Aktivační token pro test majitele se předává pouze bezpečnou proměnnou `BAROMETR_OWNER_PREVIEW_TOKEN`; nepatří do repozitáře. Testuje se v novém izolovaném profilu prohlížeče.
