# Prövning av reell kompetens för antagning till kurs DV058G (anmälningskod MIU-K3752) 

Denna repository utgör underlag för bedömning av reell kompetens motsvarande kravet _minst en grundläggande kurs i objektorienterad programmering_ för behörighet till kurs med benämning _Datavetenskap GR (B) XML_ (kurskod DV058G) för vårterminen 2027.

Filen models.py är ett utdrag av ett större projekt - ett system för hantering av träningsdata kopplat mot en cloudbaserad databastjänst (Supabase). Eftersom det är just ett utdrag så förekommer beroenden på moduler (_moduler.dates_, _moduler.supabasestuff_ osv.) som jag av bland annat säkerhets- och läsbarhetsskäl ej funnit lämpligt eller nödvändigt att inkludera här. Baserat på mejlkontakt med ämnesansvarig för datavetenskap vid Mittuniversitetet kring vilka moment som förväntas behandlas i behörighetsgivande kurs så tror jag dock att detta utdrag bör vara nog för att visa att jag har de förkunskaper som krävs. Samtlig kod inkluderad här är skriven av mig själv och jag har försökt förklara så tydligt som möjligt delar som är relevanta för er bedömning.

---

### 1. Klasser och objekt
Hela filen är uppbyggd kring objektorienterade datamodeller där klasser agerar mallar för systemets data.
* **Definition av klasser:** Jag definierar tydliga klasser med dedikerade instansvariabler för olika typer av träningsdata, exempelvis `WoInst` (rad 142) och `BioData` (rad 185).
* **Instantiering:** Jag anropar klasserna jag definierat - exempel på detta finns på rad 505. Utöver detta så har jag definierade klassmetoder som kan skapa objekt dynamiskt, exempelvis `unpack_obj()` (rad 34), där funktionen själv skapar en instans av rätt subklasstyp av `DbObject` utifrån vilka nyckelord dictionary:n (objektet) innehåller.

### 2. Inkapsling
* **Privata variabler:** Egentligen så används ju inte privata variabler i Python på riktigt samma sätt som exempelvis i Java, men Pythons närmaste motsvarighet, variabler med understreck, demonstreras i min klass `WoInst` (rad 142 och framåt). Här döljs instansvariabeln `_instDatetime` från extern åtkomst, och setter-metoden (rad 162) blir det enda sättet `_instDatetime` kan modifieras. Detta säkerställer att rätt datatyp alltid lagras i objektet, vilket är särskilt viktigt då det rör sig om en tidsstämpel som förekommer som både en isosträng och ett datetime-objekt beroende på var datan hämtas från (från databasen, från Garmin-API:n osv).
* **Kontrollerad modifiering:** Basklassen `DbObject` har exempelvis metoden `update_attr()` (rad 67), vilket demonstrerar kontrollerad modifiering av objektets variabler. Den itererar över en dictionary av nya värden men uppdaterar enbart objektet om attributet faktiskt redan existerar (`if hasattr(self, key)`), vilket skyddar objektet från felaktig manipulation utifrån.
* **Intern logik:** Min användning av @property och .setter i `WoInst` gör att datatransformering hanteras internt i objektet utan att resten av programmet "ser" detta. Om klassen instantieras med tidsstämpeln i strängformat så omvandlas den automatiskt till ett datetime-objekt, och om argumentet är ogiltigt så resulterar detta i ett felmeddelande istället för att ett objekt skapas med variabler av fel datatyp.

### 3. Arv
Arv används genomgående för att skapa en struktur som är kompatibel med de ändamål programmet är avsett för - att hämta, formattera, modifiera och presentera data - på ett sätt som är så logiskt som möjligt och minimerar upprepning. Två exempel:
* **Databasobjekt:** En gemensam superklass `DbObject` (rad 26) representerar rader i databasen och definierar grundläggande attribut (`rowAdded`, `rowUpdated`) och metoder (`to_dict`, `compare_objs`) som är gemensamma för samtliga. Subklasserna, exempelvis `WoType` (rad 133), `BioData` (rad 185) och `StrExercise` (rad 209) har sina egna specifika attribut men ärver även de attribut och metoder som `DbObject` har.
* **Statistikobjekt:** Samma hierarkiska struktur används för klasser avsedda för att organisera och presentera datan på olika sätt - `PeriodStats` (rad 268) är superklassen, och underklasser som `DayStats` (rad 475) och `WeekStats` (rad 484) bygger vidare på den med sina egna specifika attribut och (i dagsläget endast tilltänkta) metoder.

### 4. Polymorfism
I min kod används polymorfism för att låta metoder hantera objekt oberoende av deras specifika subklass:
* **Dynamisk hantering:** Metoden `unpack_obj()` (rad 34) i superklassen tar en dictionary och loopar igenom alla subklasser (`cls.__subclasses__()`). Den kan därmed identifiera vilken typ av objekt det rör sig om och returnera rätt typ av objekt (t.ex. ett `WoInst`- eller `BioData`-objekt) genom samma funktion.
* **Objektjämförelse:** Metoden `compare_objs()` (rad 78) låter vilket objekt som helst jämföras med ett annat (`other`). Beroende på vilka två specifika typer av subklasser som möts, anpassar funktionen automatiskt sin logik för hur jämförelsen ska gå till (där den jämför olika attribut beroende på vilka objekttyper som jämförs - exempelvis så jämförs ett `BioData`-objekt och ett `WoInst`-objekt genom det gemensamma attributet `instId`.)  

### 5. Abstrakta klasser och gränssnitt
Även om formella `ABC`-moduler inte importeras i skriptet så använder jag samma typ av principer för abstrakta klasser och gränssnitt (vilket är lite mer naturligt eftersom det i detta fallet rör sig om Python).

`DbObject` agerar som en abstrakt modell för hantering av datan. Klassen är inte avsedd att instantieras som ett objekt utan som en fast struktur på vilken att bygga subklasserna. I och med att de mer specifika datamodellerna ärver från `DbObject` så säkerställs att alla objekten kan hanteras på ett liknande sätt, till exempel så har alla subklasserna tillgång till `to_dict()` (rad 60) och `update_attr()` (rad 67) oavsett vilken tabell raden tillhör.

### 6. Objektinteraktion
Systemet bygger på att fristående objekt samverkar och utbyter information för att utföra komplexa uppgifter. Exempel:
* I `PeriodStats.unpack_objs()` (rad 283) tar emot en "rå" lista av osorterade databasobjekt (tabellrader). Objekten samverkar genom att metoden jämför deras identifierande attribut, hittar felaktiga referenser/saknade objekt ("orphans") och strukturerar objekten till ett `PeriodStats`-objekt.
* I `to_dataframe()` (rad 401) interagerar en instans av `PeriodStats` med listor av andra objekt (`WoInst` och `BioData`). Den itererar över dessa externa objekt, anropar deras `to_dict()`-metoder och sammanfogar deras data till en enda, gemensam datastruktur.

