# Postupné rozšiřování katalogu

Katalog je nyní v poli `products` na začátku `aplikace/app.js`. Cesty fotografií jsou v `bottleAssets`. Obrázky jsou ve složce `aplikace/assets`.

Pro další produkt bude potřeba přidat záznam s unikátním číselným ID, obrázek, kategorii, podporované varianty a ukázkové hodnoty. Současný prototyp používá ID také jako index pole. Filtry kategorií, volba vážení a objemové nabídky jsou zatím pevné; před rozšířením je potřeba je převést na vlastnosti produktu. Skript sestavení má seznam tří obrázků a ukázkových detailů, který je nutné rovněž rozšířit.

Před přidáním skutečného měření potřebuje každá varianta vlastní ID, objem, označení obalu, fotografii, ověřený obrys a kalibrační tabulku výška hladiny → ml. Pro vážení navíc ověřenou taru, její toleranci a hustotu kapaliny. Chybějící údaje nesmí být považovány za naměřené.

Po změnách spusťte `node scripts/overit.cjs` a `node scripts/sestavit-nahledy.cjs`.
