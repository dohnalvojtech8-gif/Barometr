# Stav v0.3

Implementováno: katalog 1 049 produktů, 1 231 variant, 10 kategorií, vyhledávání bez ohledu na diakritiku, stránkování, lokální odemykání se třemi bezplatnými produkty, majitelský náhled, knihovna odemčených produktů a více samostatných fyzických lahví. Ručně zadaná měření, přepočty na porce 20/40 ml, prodeje a ostatní výdej, rozdíl zásob a historie měření s cyklem a obdobím.

Prototyp zatím nemá skutečné oddělené uzávěrky období. Počáteční stav fyzické lahve je její první měření; následná měření aktualizují aktuální stav. Historie ukládá jednotlivá měření s obdobím, ne neměnné účetní uzávěrky.

Neimplementováno: platební brána a účtování, serverové účty a oprávnění, OCR váhy, hustoty a tary lahví, kalibrace a rozpoznávání hladiny, automatické uzávěrky, příjmy a přesuny, integrace s pokladnou. Konec provozního dne je zatím uložená preference.

Majitelský náhled je demonstrační lokální režim bez autentizace. Ceny 2–10 Kč jsou připravené a čtvrtý produkt se běžnému náhledu bez platby neodemkne; žádná platba se neprovádí. Stav v localStorage není vhodný pro produkční placené licence.

Původní data v klíči barometr-v1 se nemažou, v0.3 má nový samostatný klíč barometr-v3. Staré záznamy nejsou automaticky migrované do nového modelu více fyzických lahví.
