# QR Sample Tracker — Projectoverzicht (stand van zaken: 5 augustus 2026)

## Doel

Een webapp (Streamlit + Supabase) die in een labo-omgeving bijhoudt welke stalen
binnenkomen, ze een uniek volgnummer + QR-code geeft, en optioneel koppelt aan
een werkaanvraag. Gestart als MVP met nepdata op de eigen computer van de
bedenker (weinig programmeerervaring), met als einddoel: dit ooit verkopen aan
of aanpassen voor andere bedrijven.

## De echte werkwijze (dit is de kern — wijkt af van het allereerste idee)

1. **Stalen komen binnen en worden als eerste ingelogd** — niet de werkaanvraag.
   Het gebeurt geregeld dat er nog geen werkaanvraag bestaat op het moment dat
   stalen toekomen.
2. Elk staal krijgt automatisch een uniek nummer: `YY-Naam-NNN-II`
   (bv. `26-Stijn-001-01`, `26-Stijn-001-02` als er meerdere stalen tegelijk
   binnenkomen onder hetzelfde intake-moment). Het volgnummer (`NNN`) telt op
   per jaar en begint elk jaar opnieuw bij 001.
3. **Pas nadien, en niet altijd**, wordt er een werkaanvraag aangemaakt en
   worden stalen daaraan gekoppeld — soms stalen uit één intake-moment, soms
   stalen die op verschillende momenten zijn binnengekomen maar tot hetzelfde
   project/dezelfde vraag horen.
4. De werkaanvraag krijgt ook een eigen, automatisch nummer: `YY-SNNN`
   (bv. `26-S001`). Dit nummer is bewerkbaar bij het aanmaken: vul je een
   *bestaand* nummer in, dan koppelt de app nieuwe stalen aan die bestaande
   werkaanvraag in plaats van een nieuwe te maken.
5. Scannen van de QR-code (of manueel het staal- of werkaanvraagnummer
   intypen) toont de bijhorende info: klant, status, categorie, data, en de
   gekoppelde werkaanvraag (indien aanwezig).

## Datamodel (Supabase/PostgreSQL, huidige versie)

- **`sample_intakes`** — het moment dat 1 of meerdere stalen tegelijk
  binnenkomen. Velden: batch-code, klant, status (ongoing/complete),
  categorie (quality control / complaint / process monitoring), datum
  binnengekomen, datum voltooid (auto ingevuld zodra status → complete),
  beschrijving.
- **`samples`** — elk individueel staal, hoort bij een intake, **optioneel**
  gekoppeld aan een `work_request`.
- **`work_requests`** — uniek nummer + korte beschrijving + aanvrager. Geen
  eigen status (die zit op de stalen/intake, bewuste keuze).

Row Level Security staat momenteel uit (geen login in deze fase — bewust
uitgesteld, zie verderop).

## Wat er vandaag al werkt (gebouwd en getest)

1. Stalen inloggen (met automatisch voorgesteld volgnummer, QR-code per staal)
2. Werkaanvraag aanmaken — nieuw óf koppelen aan bestaand nummer
3. Opzoeken via QR-code, staalnummer, of werkaanvraagnummer
4. Overzicht met filters (status, categorie) en zoekfunctie, incl. status
   bijwerken (met automatische einddatum)

Alle bovenstaande stappen zijn stuk voor stuk getest in de browser met
nepdata. Bekende, inmiddels opgeloste bugs: het voorgestelde volgnummer bleef
soms hangen na aanmaak (opgelost), en de zoekpagina herkende enkel de interne
ID, niet de leesbare nummers (opgelost).

## Bekend openstaand technisch punt

QR-scannen met een telefoon gaf "can't find page" tijdens lokaal testen — de
link wijst naar `localhost`, wat vanaf een telefoon naar de telefoon zelf
verwijst, niet naar de PC waarop de app draait. Voor lokaal testen op het
eigen WiFi-netwerk is de oplossing: `APP_BASE_URL` instellen op het LAN-IP-adres
van de PC. Voor een echte bedrijfsdeployment lost dit zich vanzelf op zodra de
app op een centraal bereikbaar adres draait (zie hieronder).

## Bewust uitgesteld tot nu (MVP-scope)

- Login/authenticatie
- Beperking tot bedrijfs-WiFi/VPN
- E-mailintegratie
- Koppeling met interne bedrijfssystemen (ERP/LIMS/SharePoint)
- Instelbare velden/categorieën per klant (multi-klant-configuratielaag)
- Echte bedrijfsdata (nu uitsluitend nepdata)

## Waar een vervolggesprek (niet-technisch) op verder kan bouwen

Er is al een verkennend gesprek geweest over hoe dit project bij een échte
nieuwe klant ingevoerd zou worden, met een uitgewerkt Word-document
("Implementatieplan: QR Sample Tracker invoeren bij een nieuw bedrijf",
5 augustus 2026) dat onder andere behandelt:

- **Architectuurkeuze**: eigen bedrijfsserver + eigen SQL-database
  ("Pad A", beter voor IT-goedkeuring/security, vraagt eigen server) versus
  een gehoste/managed oplossing ("Pad B", geen eigen server nodig, klein
  maandbedrag, minder eigen onderhoud).
- **GitHub is geen harde vereiste** om de app te laten draaien — enkel nodig
  als specifiek gekozen wordt voor Streamlit Community Cloud.
- **Zonder eigen server**: managed database (Supabase betaald, Neon, Azure,
  AWS RDS) + managed hosting (Render, Railway, een kleine VPS).
- **Duurzaamheid/onderhoud**: "voor altijd zonder enige tussenkomst" is niet
  realistisch — wel haalbaar: managed diensten + monitoring (bv. UptimeRobot)
  + een kort draaiboek + één duidelijke verantwoordelijke bij het bedrijf.
- Een kostenraming en behoefteanalyse-stappenplan (welke velden/categorieën/
  rollen/compliance-eisen per klant) zit ook in dat document.

Onderwerpen die zich lenen voor verdere verdieping in een nieuw, niet-code-
gericht gesprek: prijszetting/verdienmodel (eenmalig vs abonnement), hoe de
"multi-klant-configuratielaag" concreet aangeboden wordt (zelfbedieningsportaal
vs manuele setup per klant), positionering/concurrentie tegenover bestaande
LIMS-systemen, GDPR/dataverwerkersovereenkomsten bij een managed-cloudkeuze,
en een concreet stappenplan om de eerste betalende klant te vinden.

## Praktische context

- Projectmap: `C:\Users\verhe\Documents\Python\QR_Tracker`
- Stack: Streamlit (Python) + Supabase (PostgreSQL via API)
- Bekende valkuil op deze machine: Norton Antivirus breekt de Supabase-
  connectie door SSL-scanning; opgelost via het `truststore`-package in
  `db.py` (gebruikt de Windows-certificatenopslag i.p.v. Python's eigen lijst).
- Testaanpak: stap voor stap bouwen, telkens testen in de browser, database
  leegmaken tussen testsessies, nooit echte bedrijfsdata gebruiken.
