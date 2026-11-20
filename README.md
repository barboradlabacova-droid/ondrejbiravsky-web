# ondrejbiravsky.cz

Web Ondřeje Biravského. Vlastníkem webu, hostingu i domény je Ondřej.

- **Úpravy textů:** https://ondrejbiravsky.cz/admin (přihlášení e-mailem)
- **Hosting:** Netlify, účet Ondřeje
- **Zdrojové soubory:** GitHub (veřejný repozitář)
- **Zálohy:** automaticky 1. den v měsíci (ZIP v GitHub Releases + e-mail)

---

## Pro Ondřeje: jak upravit web

1. Otevřete **ondrejbiravsky.cz/admin** a přihlaste se svým e-mailem.
2. Vlevo vyberte, co chcete upravit:
   - **Články**: nový článek přidáte tlačítkem „Nový Článek“.
   - **Obsah webu → Reference**: novou referenci přidáte tlačítkem „Přidat“, objeví se nahoře.
   - **Obsah webu → Prodané nemovitosti**: fotka, název, popis, typ.
   - **Obsah webu → O mně**: text o vás.
   - **Obsah webu → Kontakty, čísla a ocenění**: telefon, e-mail, sítě, čísla na úvodu, ocenění, tým.
3. Klikněte **Publikovat → Publikovat teď**.
4. Zhruba za minutu je změna na webu.

Nic nemůžete rozbít natrvalo. Každá změna se ukládá jako verze, takže jde kdykoli vrátit.

**Nabídka nemovitostí** se zatím aktualizuje ručně ze systému Igluu (soubor `content/igluu.json`). Až bude k dispozici Igluu API, bude se brát automaticky.
Fotky nabídky si web sám stahuje k sobě (GitHub Action „Fotky z Igluu“, při změně nabídky a každé pondělí), takže nezmizí, ani když je Igluu po prodeji smaže.

---

## Fáze 1: náhled pod zámkem (než se web předá Ondřejovi)

1. Repozitář na GitHubu Barbory, Netlify projekt na účtu Barbory (bezplatný stačí).
2. Netlify → Site configuration → **Environment variables** → přidat `NAHLED_HESLO` (scope: Functions) s heslem pro náhled.
   Celý web včetně `/admin` pak chce jméno (libovolné) a toto heslo. Vyhledávače ho neindexují.
3. Adresa náhledu: `nazev.netlify.app` (Site configuration → Change project name).
4. Na Akce GitHubu: spustit ručně **Fotky z Igluu** (Actions → Fotky z Igluu → Run workflow), ať se stáhnou fotky.

**Předání Ondřejovi:** GitHub umí repozitář převést na jiný účet (Settings → Transfer ownership), historie zůstane.
Na Ondřejově Netlify se pak repozitář jen znovu připojí podle kroků níže. Před spuštěním ostrého webu smazat
`netlify/edge-functions/zamek.js`.

**Pozor na kredity:** bezplatný Netlify má 300 kreditů měsíčně a každé publikování (uložení v editoru,
nové fotky z Igluu) stojí 15 kreditů, tedy zhruba 20 publikování za měsíc. Když kredity dojdou, Netlify
projekt do konce měsíce pozastaví. Pro ostrý web proto doporučujeme tarif Personal (9 USD měsíčně, 1 000 kreditů).

## Nasazení (jednorázově, dělá Barbora)

### 1. GitHub
1. Vytvořte **veřejný** repozitář, např. `ondrejbiravsky-web`. Veřejný proto, aby na bezplatném Netlify mohlo do webu publikovat víc lidí. Ve zdrojácích nejsou žádná hesla.
2. Nahrajte do něj obsah této složky (bez `dist/`).
3. Ondřeje přidejte jako správce: Settings → Collaborators → Admin.

### 2. Netlify (účet Ondřeje)
1. Na netlify.com založte účet na e-mail Ondřeje (ondrej.biravsky@century21.cz).
2. **Add new site → Import from Git → GitHub →** vyberte repozitář.
3. Build command `python3 build.py`, publish directory `dist`. Obojí se načte z `netlify.toml` automaticky.
4. Po prvním nasazení web běží na adrese typu `nazev.netlify.app`. Tam ho celý projděte.

### 3. Editor (Netlify Identity)
1. Site configuration → **Identity → Enable Identity**.
2. Registration: **Invite only**.
3. Services → **Git Gateway → Enable**.
4. Identity → **Invite users**: Ondřej a Barbora.
5. Pozvánka přijde e-mailem. Odkaz otevře `/admin`, kde si člověk nastaví heslo.

### 4. Formuláře
Site configuration → **Forms → Form notifications → Email notification** na ondrej.biravsky@century21.cz.
Formuláře na webu: `poptavka`, `ebook`, `odhad`, `hlidani`.

### 5. Doména
1. Domain management → **Add domain** → `ondrejbiravsky.cz`.
2. U registrátora domény nastavte DNS podle pokynů Netlify (A záznam + CNAME pro www), nebo přepněte nameservery na Netlify.
3. HTTPS se zapne samo, do hodiny.
4. Staré adresy z původního webu se přesměrují samy (viz `netlify.toml`).
5. Až nový web poběží, zrušte starý hosting.

### 6. Zálohy e-mailem (volitelné)
ZIP se každý měsíc uloží do GitHub Releases vždycky. Aby chodil i e-mailem, přidejte v GitHubu Settings → Secrets and variables → Actions tyto secrets:

| Secret | Příklad |
|---|---|
| `SMTP_SERVER` | smtp.gmail.com |
| `SMTP_PORT` | 465 |
| `SMTP_USER` | adresa, ze které se posílá |
| `SMTP_PASSWORD` | heslo aplikace (ne běžné heslo) |
| `ZALOHA_PRIJEMCE` | ondrej.biravsky@century21.cz |

Ručně jde záloha spustit přes Actions → Měsíční záloha → Run workflow.

---

## Technika (pro vývojáře)

- Statický web generuje `build.py` (Python 3, `markdown`, `PyYAML`) z `content/`, `templates/` a `static/` do `dist/`.
- Lokálně: `pip install -r requirements.txt && python3 build.py`.
- Editor: Decap CMS 3 (`static/admin/`). Lokální test: `npx decap-server` v kořeni repozitáře a otevřít `/admin`.
- Obrázky nahrané přes editor jdou do `static/assets/img/uploads/`.
