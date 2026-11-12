# BAROMETR — účty a pozvánky

Aktuální server: Flask + PostgreSQL. `server/web/` obsahuje přihlašovací bránu a aplikaci, `aplikace/` sdílený katalog a obrázky. Původní samostatné HTML soubory jsou archivní prototyp, nikoli přihlášená aplikace.

Render Blueprint: `render-auth.yaml`. Bezplatný web a databáze ve Frankfurtu. DATABASE_URL se připojuje soukromě přes fromDatabase. Zadané administrátory založí při prvním startu ADMIN1_USERNAME, ADMIN1_PASSWORD, ADMIN2_USERNAME, ADMIN2_PASSWORD; hodnoty patří pouze do Render Environment. Existující hesla se při restartu nepřepisují.

Administrátoři mohou odemykat katalog zdarma, evidovat inventuru, vytvářet jednorázové nebo omezené pozvánky, sledovat aktivitu a blokovat či odstranit běžné účty. Běžné účty zatím nemohou odemykat ani měřit lahve. Oprávnění kontroluje server. Platby nejsou zapnuté. Automatické měření objemu z fotografie není implementované; inventura pracuje se zadaným množstvím.

Hesla: scrypt. Relace: náhodný token, hash v DB, Secure/HttpOnly/SameSite cookie; CSRF pro změny, omezení pokusů o přihlášení. Aktivita se uchovává 90 dní; mazání účtu odstraní jeho relace, inventuru a historii. Uživatelé jsou o evidenci aktivity informováni při registraci.

Testy: `pip install -r requirements.txt pytest` a `pytest -q tests/test_accounts.py`. Browser test vyžaduje Playwright a Chromium; TEST_URL, TEST_ADMIN1, TEST_PASSWORD1, TEST_ADMIN2, TEST_PASSWORD2 nastavte mimo zdrojový kód. SQLite funguje pouze při explicitním BAROMETR_TEST_DB pro testy; v produkci je povinná DATABASE_URL.

Dočasná bezplatná databáze vytvořená 12. 11. 2026 vyprší 12. 12. 2026. Před expirací je nutná migrace nebo změna plánu; nepředstavuje trvalé úložiště. Bezplatný web může po nečinnosti při prvním otevření chvíli startovat.
