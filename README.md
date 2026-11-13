# BAROMETR 0.10

Účtová aplikace pro inventuru barů: 1 049 produktů, 1 231 doložených objemových variant a 10 kategorií.

[Otevřít aplikaci](https://barometr-app.onrender.com/)

## Aktuální funkce

- Serverové účty, pozvánky, oprávnění a administrátorský přehled aktivit.
- Katalog a knihovna lahví; ceny digitálního odemčení 0,39–0,99 €.
- 1 614 značkových a tematických balíčků v databázi, osm nabídek s obměnou každé pondělí podle Europe/Prague.
- Sekvenční inventura s měnitelným pořadím, celoobrazovková kamera, ukládání soukromých snímků a historie.
- Ruční odečet, kalibrované vážení a soukromé vícebodové profily pro konkrétní produkt a kapacitu.
- Volitelné napojení automatické AI analýzy. Bez serverové konfigurace se nespouští; přesnost na reálných lahvích zatím není ověřená.

**Platby nejsou spuštěné.** Běžní testovací uživatelé nabídky prohlížejí, administrátor odemyká zdarma. Odemykání neznamená vytvoření fyzické lahve ani ověřenou kalibraci všech hladin.

## Spuštění a ověření

Backend je Flask/PostgreSQL, zdroj `server/app.py`, frontend `server/web/`. Konfigurace účtů a lokálního SQLite testování: [README-ACCOUNTS.md](README-ACCOUNTS.md). V produkci je PostgreSQL povinný. Tajné hodnoty patří do prostředí, nikoli do repozitáře.

```sh
python -m pip install -r requirements.txt pytest
python -m pytest -q
node scripts/overit.cjs
node tests/scanner-math.cjs
```

Browser testy v `tests/` vyžadují Playwright a Chromium. Používají pouze vlastní lokální testovací účet a testovací data; nelze je spouštět proti produkčnímu účtu. Test AI používá simulované odpovědi a neměří skutečnou úspěšnost rozpoznávání.

Na Renderu běží `barometr-app` podle `render-auth.yaml`. Původní statický web v `aplikace/index.html` přesměrovává na účtovou aplikaci. Staré HTML ukázky a skripty ve `scripts/` nejsou aktuální produkční frontend.

## Dokumentace

- [Ceny, balíčky a týdenní rotace](dokumentace/KATALOG-A-CENY.md)
- [Skenování a omezení měření](dokumentace/SKENOVANI.md)
- [AI analýza: konfigurace a stav ověření](dokumentace/AUTOMATICKE-ROZPOZNANI.md)
- [Přidávání lahví](dokumentace/PRIDAVANI-LAHVI.md)
- [Zdroje původních fotografií](dokumentace/ZDROJE-OBRAZKU.md)
