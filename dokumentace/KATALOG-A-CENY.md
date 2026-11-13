# Katalog, ceny a týdenní balíčky (0.10)

Katalog obsahuje 1 049 produktů a jejich doložené objemové varianty, převážně ze sortimentu [L & M nápoje](https://www.lmnapoje.cz/alko/). Jde o digitální odemčení produktu se všemi jeho uvedenými objemy, nikoliv o prodej alkoholu nebo příslib ověřené kalibrace všech hladin.

## Individuální ceny

Cenové hladiny jsou 0,39 / 0,49 / 0,59 / 0,69 / 0,79 / 0,89 / 0,99 €. Nejvyšší cena 0,99 € je redakčně vyhrazená pouze těmto třem položkám:

- Hennessy XO
- Remy Martin XO Excellence Cognac
- Zacapa rum XO

Nejde o objektivní žebříček kvality alkoholu. Ostatních 1 046 produktů má nižší cenu. Aktuální explicitní cena je v poli `unlockPrice` katalogu a měna v kořenovém poli `currency: EUR`.

## Balíčky uložené v databázi

Aplikace při nasazení vygeneruje a idempotentně uloží 1 614 jedinečných sad do tabulky `shop_bundles`. Výběry jsou značkové (společný název značky) nebo tematické podle skutečné kategorie. Každá sada má stabilní identifikátor odvozený od produktů; duplicitní sady se nevytvářejí. Seed používá dávkové inserty. Týdenní API používá nabídky načtené z této databáze při startu služby.

Zvláštní startovní nabídka **Jägermeister + Orange — všechny objemy** stojí 0,49 €. Obsahuje klasický Jägermeister a obě samostatné katalogové položky Orange (33 % a 35 %), aby pokryla všechny jejich evidované velikosti. Nabídka je součástí první týdenní sady, nikoliv trvalá akce. Uvedená procenta a varianty jsou převzaté z katalogových zdrojů; případnou redakční opravu produktu je nutné provést podle etikety a dodavatele.

Větší sady mají podle počtu produktů absolutní slevu:

- od 8 produktů: 2 €,
- od 12 produktů: 3 €,
- od 18 produktů: 4 €,
- od 24 produktů: 5 €.

Výsledná cena nesmí být záporná, nulová ani vyšší než součet položek. Generují se pouze platné sady s minimální cenou 0,39 €. Menší značkové sady mají přiměřenou nižší slevu nebo výslovně určenou akční cenu. Všechny peněžní operace probíhají v celých eurocentech.

## Týdenní obměna

Každé pondělí v 00:00 v časovém pásmu Europe/Prague se automaticky vyberou 2 menší nabídky a 6 větších kolekcí. Výběr je deterministický podle týdne a společný pro všechny účty; zohledňuje změny roku i letního času. Frontend ukazuje platnost a po vypršení nabídky obnoví. Není potřeba cron ani zásah do zdrojových souborů každý týden.

API při potvrzení kontroluje aktuální týden i dostupnost balíčku; stará či neplatná nabídka vrací HTTP 409. Už odemčené produkty se znovu nezapočítávají do osobní ceny. Při částečném vlastnictví se cena poměrně sníží, s minimem nepřesahujícím cenu zbývajících položek; při úplném odemčení je nula.

## Odemčení a platby

Platební brána zůstává vypnutá. Běžný testovací účet může nabídky prohlížet, ale nemůže nakupovat ani odemykat. Administrátor může balíček potvrdit zdarma. Všechny položky se odemknou jednou databázovou transakcí a opakované potvrzení nevytváří duplicitní odemčení. Balíček nezakládá fyzické lahve ani záznamy inventury.

## Kalibrace

Nový soukromý profil se váže na účet, produkt a konkrétní kapacitu. Uživatel zadává nejméně pět skutečně změřených bodů, včetně prázdné a plné lahve. Mezilehlé body se nepředvyplňují odhadem. Po validaci se uloží do `bottle_calibrations`; ve výpočtu se použije po částech lineární interpolace mezi body. Díky tomu nemusí být výška hladiny přímo úměrná objemu.

Profil zlepšuje převod výšky na objem, ale nezaručuje správnost zadaných referencí, detekce hladiny nebo shodu provedení fyzické lahve. Přesnost na reálných lahvích není tímto výpočetním testem ověřená. V záznamech zůstává `accuracyVerified: false`. AI služba se touto změnou sama nezapíná.
