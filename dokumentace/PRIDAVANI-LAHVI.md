# Přidávání lahví v0.3

Katalog je `aplikace/catalog-data.js`, objekt `window.BAROMETR_CATALOG` s polem `products`.

Každý produkt má stabilní unikátní `id`, název `name`, kategorii `category`, sílu `abv`, cenu odemčení `unlockPrice`, hlavní obrázek `image` a pole `variants`. Každá varianta obsahuje `ml`, `image`, `source` a `sourceName`. Nepřidávejte objemy bez doloženého zdroje. Nový tvar obalu může vyžadovat samostatnou budoucí kalibraci.

Cena odemčení musí být jedna z hodnot 0,39 / 0,49 / 0,59 / 0,69 / 0,79 / 0,89 / 0,99 €; nejvyšší hladina je vyhrazená explicitně vybraným špičkovým položkám, viz KATALOG-A-CENY.md. Pokrývá všechny uvedené velikosti produktu. Cizí příchutě nebo odlišný obsah alkoholu nepřidávejte jako pouhý objem.

Produkty lze doplňovat bez změn logiky kategorií, stránek nebo knihovny. Zachovávejte ID stávajících produktů kvůli historii a odemčením. Fotografie nepředstavují ověřené kalibrační podklady.

Kontrola: `node scripts/overit.cjs`. Sestavení samostatné aplikace: `node scripts/sestavit-nahledy.cjs`.
