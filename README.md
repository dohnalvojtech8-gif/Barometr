# BAROMETR

Interaktivní prototyp aplikace pro inventuru baru. Aktuální katalog: **Amundsen, Captain Morgan a Jägermeister**, včetně produktových fotografií uložených lokálně.

## Otevření

Stáhněte repozitář přes **Code → Download ZIP** a rozbalte jej.

- `01-VSECHNY-OBRAZOVKY.html`: všech 9 návrhů pod sebou, funguje offline i bez JavaScriptu.
- `02-INTERAKTIVNI-APLIKACE.html`: ovladatelná aplikace v jediném souboru. Otevřete v běžném prohlížeči; náhled souborů na telefonu nemusí spouštět JavaScript.
- `aplikace/`: oddělený zdrojový kód a fotografie.

## Vývoj

Bez instalačních závislostí. Pro ověření a sestavení samostatných HTML potřebujete Node.js:

```sh
node scripts/overit.cjs
node scripts/sestavit-nahledy.cjs
```

Lokální server s Pythonem:

```sh
python3 -m http.server 8080 --directory aplikace
```

Otevřete `http://localhost:8080`.

## Stav

Funguje navigace, ukázkové inventury, katalog, volba demonstračního objemu, ruční zadání ml, přepočet na 20/40ml panáky, úprava prodejů a místní ukládání. Fotoaparát lze zapnout podle oprávnění prohlížeče.

**Automatické měření z fotografií ani OCR váhy nejsou implementované.** Archivní inventury a ceny jsou demonstrační. Účty, databáze, platby, skutečné uzávěrky a více fyzických lahví stejného produktu jsou další fáze vývoje.

## Další lahve

Postup a současná omezení katalogu popisuje [PRIDAVANI-LAHVI.md](dokumentace/PRIDAVANI-LAHVI.md). Přehled funkcí je v [FUNKCE-A-DALSI-VYVOJ.md](dokumentace/FUNKCE-A-DALSI-VYVOJ.md).

Fotografie mají uvedené [zdroje](dokumentace/ZDROJE-OBRAZKU.md); práva k nim zůstávají držitelům, licence pro další komerční distribuci nebyla ověřena.
