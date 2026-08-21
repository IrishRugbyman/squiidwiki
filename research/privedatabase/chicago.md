# Chicago - privedatabase pages

The Chicago slice of privedatabase.wordpress.com. **Out of scope for the Detroit universe** -
kept separate so it cannot leak into Detroit seeding.

**448 pages.** 156 carry a set bio; 218 carry structured member blocks.
Extracted: **335 ally links**, **497 enemy links**, **24 former alliances**, **726 members**, **586 bodies**, **3469 shootings**, **515 assists**.

**Nothing here has been written to the database.**

## How this was extracted

Two different jobs, done two different ways.

**Member blocks were parsed.** `FUSILLADES IMPORTANTES:` / `CORPS:` / `ASSISTANCE(S):` are
clean newline-separated lists of `Name (Set)` entries, so a parser handles them reliably.
Each entry names a target *and* the target's own set, which makes these **directed edges
between sets**, not prose - the most directly seedable material on the site.

**Bios were read, not parsed.** The opening paragraph of each set page is irregular French
prose and regex mangled it. These fields come from reading each bio and deciding. The
normalisation applied:

| French | Meaning | Mapped to |
|---|---|---|
| `fusionnés avec` | merged with | **allies** |
| `alliés avec`, `cools avec`, `en bonne entente avec` | allied / on good terms | **allies** |
| `ennemis avec`, `ennemis directs avec` | enemies | **enemies** (one list, no direct/indirect split) |
| `en guerre contre`, `en embrouille avec` | at war / in a recent beef | **enemies** |
| `étaient autrefois alliés`, `mais ne le sont plus` | formerly allied, no longer | **former_allies** |

Merges are folded into allies deliberately: the wiki has one ally relationship, not a
separate merge concept. The `former_allies` split is kept because collapsing it would assert
live alliances that ended - 800 Young Money *was* merged with 051 Young Money and is not any
more, with only the Mickey Cobra OGs still linked across both.

Nation names are expanded where the author elided: "un set de Gangster et Black Disciples"
means Gangster **Disciples** and Black Disciples.

---

## Sets

### 051 YOUNG MONEY

`https://privedatabase.wordpress.com/051-young-money/` · page 286 · FCK HEAD$HOT · 2020-03-27

- **Nations:** Mickey Cobras, Black P.Stones
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Originally a Gangster Disciples set in the 2000s; in that era they formed one of the most powerful alliances in South Chicago with MetBoyz.

- **Members listed:** AeroAndrillaArioBoom (décédé), Kiddo Da DrillaLil Marc (décédé), Lil MickMelly (décédé), MillzMontanaOochiePriboyRockoRoséSlyTristoWooChopPDKeysoLil Chief (décédé), KeKeTonyRemyJamesB.A.YonnieKeysoKJNewMoneyLawLeakLieemyMatt MoneyLil AntManeskiKellzDJ MoneyKoroKymeon T-LoweLil JoshWackoKD FreekyLil Danny MarcusParisPooh ManWhite MikeShannoHassanJ.RockTwilla No THFMallyBig NoahArrionPolo (décédé), Shawt Mac (décédé), Big Freaky (décédé), Cornbread (décédé), Wank (décédé), T-Berg (décédé), Frump (décédé), T-Streetz (décédé), Big Lonnie (décédé), Los (décédé), Lance (décédé), Big A (décédée), Fathead (décédé), Bankroll Q (décédé), Zeko (décédé)

- **Bodies attributed to the set:** Lex (GuttaVille), Mike (GuttaVille), Quint (THF 46), Black (THF 46), OTF Chino (THF 46), Raheem (THF 46), Trevon (THF 46), Bob-O (THF 46), Dae Dae (THF 44), Stephon (Welch World), KD (Welch World), Wayne (BlackGate), Kedron (Dell Mobb), Shaq (600), Trixx (600), L'A Capone (600), Lil Boo (600), Lil Rob (Lamron), Corey (400E Murda Drive), OTF Nuski (FaceWorld 079), Lil Bit (OBN), Big Moe (DrexSide), Aaron (P-Block), Lil Dell (GGE), Draco (MurdaTown), Terry (MurdaTown), TWhy (GGE), Michael (DrexSide), OTF Baby D (Central City), Lil Tim (Welch World), Tyjuan (THF 46), Richie Jerk (Tyquan World)

### 051 YOUNG MONEY

`https://privedatabase.wordpress.com/051-young-money-2/` · page 7494 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Mickey Cobras, Black P.Stones
- **Also known as:** Loose Skrewz, LCMG, Fatz Gang, Streetz Ville, Marc Block, Lance Land, Los City, Zeko World
- **Allies:** Jaro City, SuWu TTB, 757, MuBu, Geo Drive, MetBoyz, STL/EBT, TYMB (part)
- **Enemies:** THF 46, OBN, 600, GuttaVille, BlackGate, Welch World, Dell Mob, THF 44, MoeTown, MurdaTown, DrexSide, O'Block, Faceworld, Lamron, 400E Murda Drive, 5th Ward, AAB, Tyquan World (some), TYMB (part), Doggpound, 800, Risky Road
- **Notes:** Originally a Gangster Disciples set in the 2000s.

- **Bodies attributed to the set:** Lex (GuttaVille), Mike (GuttaVille), Quint (THF 46), Black (THF 46), OTF Chino (THF 46), Raheem (THF 46), Trevon (THF 46), Bob-O (THF 46), Dae Dae (THF 44), Stephon (Welch World), KD (Welch World), Wayne (BlackGate), Kedron (Dell Mobb), Shaq (600), Trixx (600), L'A Capone (600), Lil Boo (600), Lil Rob (Lamron), Corey (400E Murda Drive), OTF Nuski (FaceWorld), Lil Bit (OBN), Big Moe (DrexSide), Aaron (P-Block), Lil Dell (MoeTown), Draco (MurdaTown, tué en 2018), Terry (MurdaTown, tué en 2018), TWhy (MoeTown, tué en 2018), Michael (DrexSide, tué en 2019), OTF Baby D (Central City), Lil Tim (Welch World), Tyjuan (THF 46)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Aero |  | Black P.Stone |  | Y | Lil Rob (Lamron); Tyjuan (THF 46) | Gino (THF 46); Westbrook (THF 46); Dre Money (THF 46); John John (Dell Mob); Tino (GuttaVille); M-Thang (600); Cdai (600); Inky D (600); Young Famous (600); Lil Jay (STL/EBT); E-Dogg (O'Block); Kiddo (AAB); CoKilla (MoeTown) | OTF Chino (THF 46); Lil Boo (600) |
| Andrilla |  | Mickey Cobra |  |  | OTF Nuski (FaceWorld); Big Moe (DrexSide); Dae Dae (THF 44) | Kushton (THF 46); Mooda (THF 46); Dolpho (THF 46); T-Money (THF 46); Twin (THF 46); RondoNumba9 (600); FatBoyChubbz (Lamron); Racks Rude (Risky Road); Moochie (OBN); Jacari (AAB); Mooda Baybee (DrexSide); Poppie (Tyquan World); G Mouma (MoeTown) | Lil Boo (600); Bob-O (THF46); TWhy (MoeTown) |
| Ario | Stunna | Black P.Stone |  | Y |  | B.A. (THF 46); Bart (THF 46); Philly (THF 46); BuckDilla (THF 46); Space (THF 46); Tay600 (600); Trell (600); BossMoo (600); Chief Diddy (MoeTown) | Raheem (THF 46) |
| Boom |  | Mickey Cobra | Y |  | KD (Welch World) | Simms (GuttaVille); Tay Savage (Welch World) |  |
| Kiddo Da Drilla |  | Mickey Cobra |  | Y | Shaq (600); Trixx (600) | Dinkey (THF 46); Lil Ant (THF 46); SaSa (THF 46); Tay Savage (Welch World); M-Thang (600); Murda Mill (BlackGate); EDai (600); S.Dot (600); T-Roy (O'Block); KD (O'Block); EBK Glock (TYMB); Hell-Rell (Lamron); Booka (600); JB Bin Laden (400E Murda Drive); Maine (OBN); Peter (OBN); Rusty (Beam Team) |  |
| Lil Marc |  | Mickey Cobra | Y |  | Stephon (Welch World) | Villie (GuttaVille); Chally (GuttaVille); Snooch (GuttaVille); Twilla (THF 46); Space (THF 46); J Dog (THF 46); Philly (THF 46); Lil Durk (Lamron); Edai (600) |  |
| Lil Mick |  | Mickey Cobra |  | Y | Black (THF 46); L'A Capone (600) | Uly (THF 46); BoodaMane (THF 46); BuckDilla (THF 46); CapFck12 (600); D Money (600); BlastHisAss (600); Billionaire Black (STL/EBT); Rico (STL/EBT); Lil Cothee (Risky Road) | Trixx (600) |
| Melly | The Grave Digger, The Devil (le Démon) | Black Disciple |  |  | Shaq (600); OTF Nuski (FaceWorld); OTF Chino (THF 46); Raheem (THF 46); Lil Dell (MoeTown); Trayvon (THF 46); TWhy (MoeTown/GGE, tué en 2018); OTF Baby D (Central City, tué en 2018) | Bart (THF 46); Rome (THF 46); TP (THF 46); Twin (THF 46); E Dogg (THF 46); Ikey Mikey (Dell Mob); Beski (Lamron); PT (Lamron); Twin (Lamron); Emily (PNP, set de fille); Hannah (PNP, set de fille); M-Thang (600); D.Rose (600); Cdai (600); Memo (600); Manny (600); Spoon (STL/EBT); Ivery (TYMB); OTF D-Thang (Doggpound); OTF Ikey (O'Block); 50Shot Mall (MoeTown); Khalil (MoeTown); MoneyMan (MoeTown); Deega (MoeTown); Scale (MoeTown); Chief Diddy (MoeTown); Nardo (BlackGate) | Lil Boo (600); Draco (MurdaTown); Terry (MurdaTown) |
| Millz |  | Black P.Stone |  | Y |  | Dinkey (600); KTK (600); Lil Ant (600); Jusblow (600); Lil Dee (STL/EBT); Spoon (STL/EBT); Johnny Dang (400E Murda Drive); Scoota (OBN); Tez (TYMB) | Trixx (600) |
| Montana | Lil Tony“, “Tony Montana“, «FatzTana, Mr.46K | Black P.Stone |  |  | Mike (GutaVille); Quint (THF 46); Bob-O (THF 46) | Head (5th Ward); Puncho (THF 46); Twilla (THF 46); Buckey (THF 46); Tay Tay (THF 46); Bruh Bruh (O'Block/THF 46); Lil Gudda (THF 46); Rioo (THF 46); Scoobs (THF 46); Toine (THF 46); Boona (Lamron); Doody (Welch World); Billionaire Black (STL/EBT); Rio (GuttaVille); Hamma (GuttaVille); Simms (GuttaVille); AK (Brick City/600) | Lex (GuttaVille) |
| Oochie | Xotic Wop | Black P.Stone |  | Y | Lil Boo (600) | TMac (THF 46); D-Wade (THF 46); G-Baby (THF 46); Moe Gotti (THF 46); Memo (600); CapFck12 (600); Caddy Mac (MoeTown); O Dogg (MoeTown); Chief Diddy (MoeTown); Scale (MoeTown); Dot (DrexSide); Ray Bands (No Luv City); Lil Varney (Lamron) | Lil Bit (OBN); Dae Dae (THF 44) |
| Priboy |  | Mickey Cobra |  |  | OTF Nuski (FaceWorld); Aaron (P-Block) | Lil Dee (600); Jusblow (600); Ky (THF 46); Dre Money (THF 46); King Von (O'Block); Lil Fay Fay (TYMB); Filly (400E Murda Drive); 300OJ (Lamron) | Lil Rob (Lamron) |
| Rocko | Rockhead, Spot Em Got Em | Mickey Cobra |  | Y | Lex (GuttaVille); Black (THF 46); Wayne (BlackGate) | Rio (GuttaVille); Scronnie (GuttaVille); J-Hov (BlackGate); Denno (BlackGate); DMan (BlackGate); BenzZoe (BlackGate); Ty (BlackGate); Choppa Da Goon (Welch World); Bayzoo (THF 46); B.A. (THF 46); KTK (THF 46); Bayzoo (THF 46); Ky (THF 46); J Dog (THF 46); Cas (5th Ward); Byrdie (Lamron); Lil Reese (Lamron); Chief Wuk (Lamron); D.Rose (600); BiteDown (600); T-Roy (O'Block); G Mouma (MoeTown); Big Swirl (Risky Road); Lil Jay (STL/EBT); Trigga (TYB); Aero (051 Young Money, accident) | Mike (GuttaVille); Marvin (THF 46); L'A Capone (600); Lil Tim (Welch World) |
| Rosé | Lil Ricky | Mickey Cobra |  |  | Kedron (Dell Mobb) | Ronscoe (GuttaVille); Tay Savage (Welch World); SaSa (THF 46); BuckDilla (THF 46); Tracey (THF 46); Blue (Dell Mob); FaceSixO (600); S.Dot (600); BoBo (MurdaTown) |  |
| Sly | Slizzy La'Flare | Mickey Cobra |  |  | Corey (400E Murda Drive) | King Melo (THF 46); Fat Boi (THF 46); Trell (600); Mikey (OBN); Lil Flex (OBN); G Polo (DrexSide) | OTF Nuski (FaceWorld); Lil Boo (600); Big Moe (DrexSide); Bob-O (THF 46) |
| Tristo |  | Black P.Stone |  |  |  | Lil Ant (THF 46); Puncho (THF 46); Tracy (THF 46); Gino (THF 46); Manny (600); Booka (600); D-Wade (OBN); BossTop (O'Block) | Trayvon (THF 46) |
| Woo |  | Black Disciple |  | Y | Lil Bit (OBN) | Crack (THF 46); Westbrook (THF 46); Billa (THF 46); Cdai (600); D Money (600); Hamma (GuttaVille); Lil Durk (Lamron); Rio (OBN) | Dae Dae (THF 44) |
| Chop |  | Mickey Cobra |  |  |  |  | Bob-O (THF 46) |
| PD |  | Mickey Cobra |  |  | Michael (DrexSide) |  | TWhy (MoeTown) |
| Lil Chief |  | Mickey Cobra | Y |  |  |  | KD (Welch World) |
| Los |  | Mickey Cobra | Y |  |  |  | KD (Welch World) |
| Fathead | Fatz World | Black P.Stone | Y |  |  |  | Lil Tim (Welch World) |
| Keyso |  | Black P.Stone |  |  | Draco (MurdaTown); Terry (MurdaTown) |  |  |

### 1200

`https://privedatabase.wordpress.com/1200-2/` · page 287 · FCK HEAD$HOT · 2020-03-27

- **Members listed:** CORPS:

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Lil Harry (SuWu Mobb)Lucky (SuWu Mobb)Jay Jay (SuWu Mobb)D N |  |  |  |  |  |  |  |

### 1200

`https://privedatabase.wordpress.com/1200-2-2/` · page 8291 · FCK HEAD$HOT · 2020-03-10

- **Nations:** Gangster Disciples
- **Allies:** OTE, AMM, OTA, Murda Mafia City, E-Way, Sac Boyz
- **Enemies:** OTS, SuWu Mobb, BuckTown, BTBG

- **Bodies attributed to the set:** Lil Harry (SuWu Mobb), Lucky (SuWu Mobb), Jay Jay (SuWu Mobb), D Nice (SuWu Mobb), FIO (SuWu Mobb), Cat (SuWu Mobb)

### 400E MURDA DRIVE

`https://privedatabase.wordpress.com/400e-murda-drive-2/` · page 7893 · FCK HEAD$HOT · 2019-11-19

- **Nations:** Black Disciples
- **Also known as:** Taliban
- **Allies:** Chris World, DOD, BashVille
- **Enemies:** E-Block, Gotti World, 757, 051 Young Money
- **Notes:** Rapper L'A Capone of the 600 was very close to this set and its members, including JB Bin Laden. They represent the "L'A Gang" for the killed L'A Capone of the 600, and the "Pluto Gang" for a killed Lamron member.

- **Bodies attributed to the set:** Chris (8X13), PopaDot (E-Block), Fella (E-Block), Lil Mike (E-Block), Fame (8X13), Hadi (E-Block)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| JB Bin Laden |  | Black Disciple |  |  |  | Lil Ant (051 Young Money); Matt Money (051 Young Money); Babo (8×13); Blow (8×13); E-Thang (E-Block); Butha (E-Block); Lawskii (E-Block) |  |
| Nano |  | Black Disciple |  |  |  | Meech (8×13); HardBody (8×13); Nello (E-Block); 757Wooski (757); Devo (757) |  |

### 400E MURDA DRIVE

`https://privedatabase.wordpress.com/400e-murda-drive/` · page 288 · FCK HEAD$HOT · 2020-03-27

- **Members listed:** JB Bin LadenNanoHell Rell (décédé), Johnny DangBig JEliChrisFaceOmarlyRashard (décédé), Sharman (décédé), D-NyceBeanzRonKelsYon YonGussiMacG-CraneSantanaYoungMoneyDeonte (décédé), WeedyJohnny JacketDominique (décédé), DookChina White (décédé), Kool-Aid (décédé), Lil DirkMan Man (décédé), Corey (décédé), Ant (décédé), Slip (décédé)

- **Bodies attributed to the set:** Chris (8X13), PopaDot (E-Block), Fella (E-Block), Lil Mike (E-Block), Fame (8X13), Hadi (E-Block)

### 50 STRONG

`https://privedatabase.wordpress.com/50-strong/` · page 290 · FCK HEAD$HOT · 2020-03-27

- **Nations:** Gangster Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** A few years ago they expanded their territory by taking two blocks from FollyBoyz.

- **Members listed:** CEOKiarKing GregBig Meech (décédé), Dell (décédé), Dougo (décédé), DellstroBraboySlickTaeDoggSolo (décédé), Boss Veze JamesManyNamesTriggah900 Tyree Quise King MurdaBig Squad Boss BullyLil Duwuap Solution Loko YC Big Folks DJJuiceSouljaChief RellTemmo (décédé)

- **Bodies attributed to the set:** Zack (FollyBoyz), Lil Derrick (FollyBoyz), B-Luv-It (FollyBoyz), T-Mac (FollyBoyz), Zio (FollyBoyz), Mazi (FollyBoyz), Scrap (FollyBoyz), Molly (FollyBoyz), Banks (FollyBoyz), Jareem (No Limit 087), Kirby (REC City)

### 50 STRONG

`https://privedatabase.wordpress.com/50-strong-2/` · page 7889 · FCK HEAD$HOT · 2019-11-19

- **Nations:** Gangster Disciples
- **Also known as:** Dell World, Doug Gang, DWDG, WeAllWeGot, Opp Boyz, Da We'zz, Double D'z, OBE
- **Allies:** DamenVille, CMB, Brick$quad 069, JJ Gang, No Luv City, Dumpstreet
- **Enemies:** MoeTown, REC City, No Limit 087

- **Bodies attributed to the set:** Terrance (MoeTown), Beek (MoeTown), T-Mac (MoeTown), Zio(MoeTown), Kamikaze Mazi (MoeTown), Scrap (MoeTown), Lil Derrick (MoeTown), Zack (MoeTown), Banks (MoeTown), Molly (MoeTown), Jareem (No Limit 087), Kirby (REC City), Crack (MoeTown), B-Luv-It (MoeTown), Crack (MoeTown), Slow Moe (MoeTown)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| CEO | Woo Skee | Gangster Disciple |  |  | Terrance (MoeTown); T-Mac (MoeTown); Molly (MoeTown); Scrap (MoeTown) | 50Shot Mall (MoeTown); Choppa (Lamron) |  |
| Kiar |  | Gangster Disciple |  | Y | Zack (MoeTown) |  |  |
| King Greg | KG Da Shooter | Gangster Disciple |  |  | Lil Derrick (MoeTown); Molly (MoeTown) | Truth (MoeTown); Chief Diddy (MoeTown); Five Star (MoeTown); Scale (MoeTown); O Dogg (MoeTown); Maintain (MoeTown); Deega (MoeTown); Goonie Looney (No Limit 087); Money Man (TYMB); D.Rose (600) | Scrap (MoeTown) |
| Dell |  | Gangster Disciple | Y |  | Zio (MoeTown); Kamikazi Mazi (MoeTown) |  |  |
| Dougo |  | Gangster Disciple | Y |  |  |  |  |
| Soulja |  | Gangster Disciple |  |  |  |  | Molly (MoeTown) |
| Boss Veze |  | Gangster Disciple |  |  | B-Luv-It (MoeTown) | Bobby (MoeTown); Freddy Mac (MoeTown); Swaka (MoeTown); Plies (MoeTown); Wooh (MoeTown); Vell (MoeTown); Almighty Auto (MoeTown) |  |
| James |  | Gangster Disciple |  |  |  |  | Zack (MoeTown) |

### 50Shot Mall

`https://privedatabase.wordpress.com/50shot-mall/` · page 3797 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Earl (No Luv City)Peanut (Shields) |  |  |  |  |  | Kiar (50 Strong); Loko (50 Strong); Chief Rell (50 Strong); CEO (50 Strong); Chief Rell (50 Strong); Zo (Landlord COV); Rambo (No Luv City); Bootz (No Luv City); Killa Kellz (Brick$quad 069); Strizzy (Dumpstreet); PD (051 Young Money); Lil Danny (051 Young Money); Kymeon (051 Young Money); Maneski (051 Young Money); G-Rayski (GeoDrive); G-Mally (GeoDrive) | Lil Doc (No Luv City); Wally (No Luv City); Temmo (50 Strong) |

### 5TH WARD

`https://privedatabase.wordpress.com/5th-ward-2/` · page 7909 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Black Disciples
- **Allies:** THF 46
- **Enemies:** _none_
- **Former allies:** 051 Young Money
- **Notes:** They represent "Quint City" and "Gudda World" in tribute to deceased THF 46 members. Rapper Lil Jay is originally from this set.

- **Members listed:** Paris est un Black Disciple. Il est actuellement incarcéré pour le meurtre de Boom. Il sortira de prison en 2022.

- **Bodies attributed to the set:** Boom (051 Young Money)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Boom (051 Young Money) |  |  |  |  |  |  |  |
| EightBallTay'DSavageMikeTrellDevonteAce BoogieRoc (décédé)LP |  |  | Y |  |  |  |  |

### 5TH WARD

`https://privedatabase.wordpress.com/5th-ward/` · page 289 · FCK HEAD$HOT · 2020-03-27

- **Members listed:** ManManEightBall RedTay'D Savage Mike Trell Devonte Nappe Ace Boogie Roc (décédé)

- **Bodies attributed to the set:** Boom (051 Young Money)

### 5TH WARD LIFE

`https://privedatabase.wordpress.com/5th-ward-life/` · page 1767 · FCK HEAD$HOT · 2020-04-10

- **Nations:** Conservative Vice Lords
- **Also known as:** Tyto Land
- **Allies:** LordsVille
- **Enemies:** LOC City, DamenVille, W.B 057
- **Notes:** Engaged in a long-running war against these enemies.

- **Members listed:** Tyto (décédé), Jilla (décédé), JonJon (décédé), Stephon (décédé), Jugg (décédé), Big Lord (décédé), Cadarro (décédé)

- **Bodies attributed to the set:** Tuta (DamenVille), Steveo (DamenVille), Tra'Don (LOC City BotY), Mon (DamenVille)

### 600

`https://privedatabase.wordpress.com/600-2/` · page 227 · FCK HEAD$HOT · 2020-03-26

- **Nations:** Black Disciples
- **Also known as:** Brick City
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Founded by D-Thang and Lil Boo with help from Baldy, in mid-2010; Lamron had to validate their integration into the 300 alliance.

- **Members listed:** 600BreezyBiteDownBlastHisAssCapFck12Inky DJusblowLil DeeStello (décédé), Waldo (décédé), MakadoBookaCdaiD.RoseD-Thang (décédé), L'A Capone (décédé), Lil Boo (décédé), MannyMemoM-ThangRondoNumba9Tay600BossMooTriggaBaldy (décédé), Lil Steve (décédé), FaceSixOYoung FamousEdaiTacoBoowopPorkeyDro PhillyDutchBeans JRD-MoneyTrellDomoManeskiTanoMookRioDutchKGHuncho HoodoLowS.Dot Shaq (décédé), Trixx (décédé), Burger (décédé)

- **Bodies attributed to the set:** Hottie (Jaro City), Corey (Jaro City), Sammy Lo (Jaro City), TuTu (Jaro City), Derrick (Jaro City), Marlon (Jaro City), Kristle (innocente), Lil Scrapp (MOB), BayBay (MOB), Jamo (MOB), T-Streetz (051 Young Money), Fathead (051 Young Money), Polo (051 Young Money), Lil Marc (051 Young Money), Dale (STL/EBT), Odey (E-Spot), Charles (M-Town), James (M-Town), Javan (Innocent), ChinaOMan (Sirconn City Gangsters), Big V (Tyquan World), Doc (Landlord COV), Michael (Bully Gang), MoeJoe (ChiefTown), Gary (ChiefTown), Inconnu (ChiefTown), Wookie (Geo Drive), BT (Risky Road), Travis (Jaro City), Cousin de Lil Zay Osama (BSC), Innocente (cousine de Lil Zay Osama), Washington (Innocente), Dowell (Innocente)

### 600Breezy

`https://privedatabase.wordpress.com/600breezy/` · page 4743 · FCK HEAD$HOT · 2020-05-10

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Hottie (Jaro City)Michael (Bully Gang)ChinaOMan (Sirconn Cit |  |  |  |  |  | B-Sko (Jaro City); Lil Joe (Jaro City); James (Jaro City); Dome (Jaro City); Flock (Jaro City); Rell Rell (Jaro City); Travo (Jaro City); EBoi (MOB); Lil G (MOB); Tank Montana (Drill City); Mr Man (Drill City); Fatz Mack (Drill City); Tino (Drill City); Ronald (Drill City); Reggie Baybee (CMB); Tristo (051 Young Money); Millz (051 Young Money); Lil Jay (STL/EBT); Lil Reggie (Brick$quad 069) |  |

### 6Shots

`https://privedatabase.wordpress.com/6shots/` · page 4114 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Buddha (Lamron)Boonie Moe (Lamron)Lil Durk (Lamron) |  |  |  |  |  |  |  |

### 757

`https://privedatabase.wordpress.com/757-2-2/` · page 7891 · FCK HEAD$HOT · 2019-11-19

- **Nations:** Gangster Disciples, Black Disciples, Black P.Stones
- **Allies:** Geo Drive, SKD, 051 Young Money, Tyquan World, STL/EBT, Stony Spot, Jaro City, MOB
- **Enemies:** Welch World, MurdaTown, OBN, THF 46, FreeSmoke, Kimo Gang, O'Block, SuWu TTB

- **Bodies attributed to the set:** ? (SCN), Welch (So Icy), Gerrod (Welch World), Stanley (Welch World), Shannon (Welch World), Jaunce (Welch World), Lodii Bey (Welch World), Chuck (MurdaTown), Millie (MurdaTown), Kimo (MurdaTown), Nity (MurdaTown), Doe Boy (MurdaTown), Merch Money (MurdaTown), Bay Bay (FreeSmoke), BeBe (FreeSmoke), Gotti (FreeSmoke), Scoota (OBN), Boss Rell (OBN), Gucci (TouchMoney), Lil Red (Dearborn), Faheem (THF 46), Loco (THF 46, tué en 2018), ??? (Welch World)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| 757Wooski |  | Gangster Disciple |  | Y |  | Mikey (OBN); Resko (FreeSmoke); Bravo (FreeSmoke); Fat Shorty (THF 46); Bill (MurdaTown); Lochi (MurdaTown); Boss Wooh (MurdaTown) | Millie (MurdaTown); BeBe (FreeSmoke); Loco (THF 46) |
| Lil Fresh |  | Gangster Disciple |  |  |  | Peter (OBN); Santana (OBN); King Molo (OBN); Creezy (MurdaTown); Boss Wooh (MurdaTown); Westbrook (THF 46) | Scoota (OBN) |
| Neef |  | Gangster Disciple | Y |  | ? (SCN); Welch (So Icy) | Flock (Welch World); King MTG (MurdaTown); Millie (MurdaTown) |  |
| Cess | Princess | Black Disciple | Y |  |  |  | ? (SCN); Welch (So Icy) |
| Devo |  | Gangster Disciple |  |  | Scoota (OBN) | VinDog (OBN); Gino (OBN); D-Wade (OBN); Maine (OBN); Moochie (OBN); Mooda (THF 46) |  |
| Sonny | Sonno | Gangster Disciple | Y |  | Boss Rell (OBN) |  |  |
| AP | Big AP | Black Disciple |  |  | Loco (THF 46, tué en 2018) |  |  |
| BA |  | Black Disciple |  |  | ??? (Welch World) | Stank (OBN); CJ (OBN); Peter (OBN); Timo (MurdaTown); Puncho (THF 46); Twin (THF 46) |  |
| Boss Muno |  | Black P.Stone |  |  |  | Big Naz (OBN); Smiley (OBN) |  |
| Lil James |  | Black Disciple |  |  |  |  | Boss Rell (OBN) |

### 800 YOUNG MONEY

`https://privedatabase.wordpress.com/800-young-money/` · page 344 · FCK HEAD$HOT · 2020-03-27

- **Nations:** Mickey Cobras
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Created after the death of Diddy Grove of CrankTown.

- **Members listed:** AboCeaseLil JockLil NukeLil PrincePo LoRe-UpTrueyVago Lil FatzWonnoOld Head (décédé), Lil Boss (décédé), Damien (décédé), Boss SmoothSkoPyro (décédé)

- **Bodies attributed to the set:** Vic (Roc Creek), Skinz (Roc Creek), Fish (Roc Creek), Boobie (Jaro City), DJ (STL/EBT), Antoinette (051 Young Money)

### 800 YOUNG MONEY

`https://privedatabase.wordpress.com/800-young-money-2/` · page 7890 · FCK HEAD$HOT · 2019-11-19

- **Nations:** Mickey Cobras
- **Allies:** CrankTown
- **Enemies:** Roc Creek, Tyquan World, E-Block, Jaro City, MOB, Dro City, TYMB, STL/EBT, 600
- **Former allies:** 051 Young Money
- **Notes:** Formed as an offshoot of CrankTown after the death of Diddy Grove; only the Mickey Cobra OGs who belong to both 051 and 800 are still connected.

- **Bodies attributed to the set:** Vic (Roc Creek), Skinz (Roc Creek), Fish (Roc Creek), Boobie (Jaro City), DJ (Tyquan World/E-Block), Antoinette (051 Young Money)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Lil Fatz |  | Mickey Cobra |  |  | Antoinette (soeur de 051 Montana et Fathead, 051 Young Money, tué en 2019) |  | Boobie (Jaro City); DJ (Tyquan World/E-Block, tué en 2018) |
| Wopo |  | Mickey Cobra |  |  | DJ (Tyquan World/E-Block, tué en 2018) |  |  |
| Big Mike |  | Mickey Cobra |  |  | Skinz (Roc Creek) | Boss Juan (Roc Creek); Woodie (Roc Creek); Ruga (Roc Creek); Lil Duke (Roc Creek); Snika Bar (TYMB); Deskoo (TYMB); FBG Duck (STL/EBT); FBG Young (STL/EBT); TB (Tyquan World); Poppie (Tyquan World) | Vic (Roc Creek) |
| Pyro |  | Mickey Cobra | Y |  | Vic (Roc Creek); Fish (Roc Creek) | Lil D (Roc Creek); Greg (Roc Creek); Do Ho (Roc Creek); Kecey (TYMB); Zero (TYMB); Mechie Boy (TYMB); Twin (THF 46) | Skinz (Roc Creek) |
| Sko |  | Mickey Cobra |  |  |  | Tank (Roc Creek); Pookie (Roc Creek); Mikey Gotti (Roc Creek); Lil Kevin (Roc Creek); Drohon (Dro City); Money Man (TYMB); Boss Shawn (TYMB) | Fish (Roc Creek) |
| Boss Smooth |  | Mickey Cobra |  |  |  | Lil J (Roc Creek); Ole Man (Roc Creek); FBG Duck (STL/EBT); Dion (TYMB); Rerock (TYMB); Tyler (Tyquan World) |  |
| Chief C |  | Mickey Cobra |  |  | Boobie (Jaro City) |  |  |

### 808

`https://privedatabase.wordpress.com/808-2/` · page 855 · FCK HEAD$HOT · 2020-03-28

- **Members listed:** Murda Mal

### 8TRE MOBB

`https://privedatabase.wordpress.com/8tre-mobb/` · page 345 · FCK HEAD$HOT · 2020-03-27

- **Members listed:** Don Darius (décédé), Murda Mal KennethYoung ChopTayRuga Teddy Lil Moe Mannie (décédé), Shoota Shoota Neko James Lil Jay Lil Scan Pablo KenKen J Moe Lil Edward Jalil Cliff (décédé), Rico Kavontae CT (décédé), KD Poka Marley (décédé)

- **Bodies attributed to the set:** Roc (Whiz City), Blake (MTV), Lil Dejuan (Whiz City)

### 8TRE MOBB

`https://privedatabase.wordpress.com/8tre-mobb-2/` · page 7910 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Producer and rapper Young Chop is originally from this set.

- **Members listed:** Don Darius (décédé), Young ChopMurda MalKennethTayRugaTeddyLil MoeMannie (décédé), Shoota ShootaNekoJamesLil JayLil ScanPabloJ MoeLil EdwardCliff (décédé), JalilCT (décédé), KavontaeMarley (décédé)

- **Bodies attributed to the set:** Roc (Whiz City), Lil Dejuan (Whiz City), Blake (MTV)

### 8X13

`https://privedatabase.wordpress.com/8x13-2/` · page 7911 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Also known as:** Gotti World, Cash Addict Cartel
- **Allies:** THF 46, Tyquan World
- **Enemies:** _none_

- **Members listed:** ELow est un Gangster Disciple.

- **Bodies attributed to the set:** Reggis (DOD), Antonio (DOD), Christian (DOD), Raphael (DOD), Lil Rickey (KTS), Raymond (Lakeside), Rashard (400E Murda Drive), Sharman (400E Murda Drive), Deonte (400E Murda Drive)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Lil Rickey (KTS) |  |  |  |  |  | Vinnie (KTS) |  |
| Gotti (décédé)Mike (décédé)Sherm (décédé)Jon Jon (décédé)Chr |  |  | Y |  |  |  |  |

### 8X13

`https://privedatabase.wordpress.com/8x13/` · page 346 · FCK HEAD$HOT · 2020-03-27

- **Members listed:** ELowJeff Gotti (décédé), Dee Santana Mike (décédé), Carlton Meech Sherm (décédé), Lil Duke Osuma Jon Jon (décédé), Chris (décédé), T-Stunna P-Nut Fame (décédé), Alex (décédé), Babo Johnny (décédé)

- **Bodies attributed to the set:** Reggis (DOD), Antonio (DOD), Christian (DOD), Raphael (DOD), Lil Rickey (KTS), Raymond (Lakeside), Rashard (400E Murda Drive), Sharman (400E Murda Drive), Deonte (400E Murda Drive)

### AAB

`https://privedatabase.wordpress.com/aab-2/` · page 7975 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Gangster Disciples, Black Disciples
- **Allies:** _none_
- **Enemies:** Stony Spot

- **Members listed:** JuMoney ou «JuJu» était un Black Disciple. Il est décédé.

- **Bodies attributed to the set:** Pooh (Stony Spot)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Pooh (Stony Spot) |  |  |  |  |  |  |  |
| HellaBandz |  | Black Disciple | Y |  | Christopher Hooper |  |  |
| CeeJayJay GuwapCMoneyLil BoatQuellRickZayDreMoneyNate MoneyM |  |  | Y |  |  |  |  |

### ABG-CPT

`https://privedatabase.wordpress.com/abg-cpt/` · page 977 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Gangster Disciples
- **Allies:** No Luv City
- **Enemies:** _none_

- **Members listed:** KT RastaABG Skeeter

### ABK

`https://privedatabase.wordpress.com/abk/` · page 277 · FCK HEAD$HOT · 2020-03-27

- **Nations:** Renegade Black P.Stones
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** ABK stands for "Anybody Killer".

- **Members listed:** T-GlizzyYogi (décédé), Puff Diddy Bop (décédé), BobO (décédé), Rio (décédé), DeDe (décédé), Joc (décédé), Pacman (décédé), Lil Fame (décédé), Jermaine (décédé)

- **Bodies attributed to the set:** Rhonell (BlackMobb), Melvin (BlackMobb), Deo (BlackMobb), Sheldo (BlackMobb), King Scoobz (BlackMobb), Boss Gee (PocketTown), Shoota Shellz (BlackMobb), Black (BlackMobb)

### ABK

`https://privedatabase.wordpress.com/abk-2/` · page 7912 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Renegade Black P.Stones
- **Allies:** NLMB
- **Enemies:** BlackMobb
- **Former allies:** BlackMobb
- **Former enemies:** NLMB
- **Notes:** ABK stands for "Anybody Killer". Around 2010-2011, seeking glory, ABK turned on BlackMobb and allied with NLMB.

- **Members listed:** Yogi était un Renegade Black P.Stone. Il est décédé.

- **Bodies attributed to the set:** Rhonell (BlackMobb), Melvin (BlackMobb), Deo (BlackMobb), Sheldo (BlackMobb), King Scoobz (BlackMobb), Boss Gee (PocketTown), Shoota Shellz (BlackMobb)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| King Scoobz (BlackMobb) |  |  |  |  |  |  |  |
| T-GlizzyDiddy Bop (décédé)Joc (décédé)PuffGullaSosaRandellDe |  |  | Y |  |  |  |  |

### ABM

`https://privedatabase.wordpress.com/abm-2/` · page 7950 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Gangster Disciples
- **Allies:** TaeTown
- **Enemies:** _none_
- **Notes:** Based in Evanston.

- **Members listed:** Lil MoeStar (décédé), G-BabyMinkMurdaManRell RellTerranceD-GlockOsama (décédé), DontrealTony (décédé), Birdie (décédé), White Boi (décédé), Kapo (décédé), Lil Greg (décédé)

- **Bodies attributed to the set:** Jamison (Insane Block), Bang (Insane Block), Phil (Insane Block), Jamo (Insane Block)

### AMG

`https://privedatabase.wordpress.com/amg-2/` · page 7913 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Black Disciples
- **Allies:** SMB
- **Enemies:** Lowelife
- **Former allies:** Lowelife
- **Notes:** Part of the "300" movement.

- **Members listed:** J-Money est un Black Disciple.

- **Bodies attributed to the set:** Andre (TunechiVille), Crazy (CMB), TJ (Brick$quad 069), Ward (Brick$quad 069), Theodore (BlockBurna), Christopher (CMB), Marcus (CMB), Nate (CMB), Big Josh (Brick$quad 069), Taedoe (Lowelife), Deyski (Lowelife)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Big Josh (Brick$quad 069) |  |  |  |  |  | BDK Kevo (Brick$quad 069); Boss Tony (Brick$quad 069); Main (Brick$quad 069); Reese (CMB); D-Bo (CMB) | Marcus (CMB) |
| Lil T |  | Black Disciple |  |  | Andre (TunechiVille) | Boss Doro (CMB); Killa Kellz (Brick$quad 069); Nino (Brick$quad 069); BooGotti (Brick$quad 069) |  |
| Man Man |  | Black Disciple |  | Y | Taedoe (Lowelife) |  |  |
| Dreski |  | Black Disciple |  |  |  |  | Deyski (Lowelife) |
| BoaLegDonLoud ShawdyMac (décédé)PeeskiRockyTraydoeZelly |  |  | Y |  |  |  |  |

### Bang Man

`https://privedatabase.wordpress.com/bang-man/` · page 1194 · FCK HEAD$HOT · 2020-03-28

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Keonte (JigDogs)Mook (Jaro City) |  |  |  |  |  | 305 (Jaro City); Joe (Jaro City); BK (Jaro City); Baby D (Jaro City); Motor (Jaro City); ABM Tay (Jaro City); So Icey (STL/EBT); BossTrell (STL/EBT) |  |

### BASHVILLE

`https://privedatabase.wordpress.com/bashville-2/` · page 7914 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Black Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Rapper KuGlo is a member of this set.

- **Members listed:** KuGlo

- **Bodies attributed to the set:** Wint (E-Block), John (E-Block), Kaytie (E-Block), T-Mac (E-Block)

### BEAM TEAM

`https://privedatabase.wordpress.com/beam-team-2/` · page 7966 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Black Disciples, Breeds, Gangster Disciples
- **Also known as:** No Face Gang
- **Allies:** _none_
- **Enemies:** _none_

- **Members listed:** NookGloZay SavageJmannCorey (décédé), LilHeadKevoLil FoeJay (décédé), LilCT3b TKLil Ed9 (décédé), RicoRichardDope boy JayTrellLil Zay30 (décédé), JacqueesLilJohnnyLALil Lord (décédé)

### Bitedown

`https://privedatabase.wordpress.com/bitedown/` · page 4744 · FCK HEAD$HOT · 2020-05-10

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| James (M-Town)ChinaOMan (Sirconn City Gangsters)BayBay (MOB) |  |  |  |  |  | NumbaNine (Jaro City); Gucci (Jaro City); Lil Darrell (STL/EBT); Dutchie (STL/EBT); K.I. (STL/EBT); Young (STL/EBT); Spoon (STL/EBT); Jiale (STL/EBT); FBG Duck (STL/EBT); Nut (MOB); T-Baby (MOB); KD (051 Young Money); Oochie (051 Young Money); TTB Kelz (SuWu TTB); Chunky (Tyquan World); Hershey (Tyquan World); Chief Mexico (Tyquan World); Nickel Bag (Tyquan World) | Polo (051 Young Money) |

### BLACKGATE

`https://privedatabase.wordpress.com/blackgate-2/` · page 7892 · FCK HEAD$HOT · 2019-11-19

- **Nations:** Black Disciples
- **Also known as:** BGC, OBG
- **Allies:** GuttaVille, Front$treet, Nicko Gang, 600, O'Block, THF 46, DOD, ArtGang
- **Enemies:** _none_
- **Notes:** Part of the "300" movement. Rapper "SD" is a member of this set.

- **Bodies attributed to the set:** TeMarco (Met Boyz), N-Doe (Met Boyz), Doucy (Met Boyz), Kayo (Met Boyz), Keith (Met Boyz), Chop (Met Boyz), Johnny B (Met Boyz), Allo (MOB), Telly (SKD), Black Boy (SKD), Booda (SKD), Don Von (M-Town), Fred (Von World), Terrell (Von World), D.O.C. (GeoDrive), West (GeoDrive), Motor (Jaro City), Side (Jaro City)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| LilBlast |  | Black Disciple |  | Y |  | Booman (Geo Drive); G-Rayski (Geo Drive); Lil Moe (MOB) | — (—); — (—) |
| Sypo |  | Black Disciple |  |  | Motor (Jaro City); Side (Jaro City) |  |  |

### BLACKMOB (4CH)

`https://privedatabase.wordpress.com/7164-2/` · page 8004 · FCK HEAD$HOT · 2020-02-10

- **Nations:** 4 Corner Hustlers
- **Allies:** _none_
- **Enemies:** GhostMobb
- **Notes:** Based in West Chicago.

- **Members listed:** Dukes est un 4 Corner Hustler. Il est actuellement incarcéré.

- **Bodies attributed to the set:** Big Glo (GhostMobb), ? (GhostMobb)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Big Glo (GhostMobb) |  |  |  |  |  |  |  |

### BLACKMOBB

`https://privedatabase.wordpress.com/blackmobb/` · page 283 · FCK HEAD$HOT · 2020-03-27

- **Nations:** Maniac Black P.Stones, Black P.Stones
- **Allies:** _none_
- **Enemies:** _none_
- **Former allies:** ABK
- **Notes:** Formerly allied with ABK until ABK turned against them and allied with NLMB instead.

- **Members listed:** Bow Wow (décédé), BooSGHShakeyAwolMeechShawtyHittKing Scoobz (décédé), ShootaShellz (décédé), DBlack (décédé), BoogieCurfewJig Jay JordanJovanMaine ManeMoeManTacoVonnieBlack LordD-BoyT-Bone (décédé), TrappMoeDeo (décédé), Rhonell (décédé), Melvin (décédé), Sheldo (décédé), Hakeem (décédé), Ravon (décédé), Jordan (décédé), Eric (décédé), Lucky (décédé), Taco (décédé), Kasto (décédé)

- **Bodies attributed to the set:** Frederick (NLMB), Alfredo (NLMB), Vito (NLMB), C-Moe (NLMB), 1Eye (NLMB), Chico (NLMB), Pistol P (NLMB), Richie Rich (NLMB), Molly (NLMB), Big Wet (NLMB), G-Slim (NLMB), Madd Maxx (NLMB), Lil Von (NLMB), Jermaine (ABK), Joc (ABK), DeDe (ABK), Yogi (ABK), Rio (ABK), Lil Fame (ABK), PacMan (ABK), Diddy Bop (ABK), Errol (C-Block), Willie (C-Block), Daniel (C-Block), BobO (ABK)

### BLACKMOBB

`https://privedatabase.wordpress.com/blackmobb-2/` · page 7492 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Maniac Black P.Stones, Black P.Stones
- **Allies:** _none_
- **Enemies:** NLMB, ABK, C-Block
- **Former allies:** ABK
- **Notes:** Formerly allied with ABK until ABK turned against them and allied with NLMB instead.

- **Bodies attributed to the set:** Frederick (NLMB), Alfredo (NLMB), Vito (NLMB), C-Moe (NLMB), 1Eye (NLMB), Chico (NLMB), Pistol P (NLMB), Richie Rich (NLMB), Molly (NLMB), Big Wet (NLMB), G-Slim (NLMB), Madd Maxx (NLMB), Lil Von (NLMB), Jermaine (ABK), Joc (ABK), DeDe (ABK), Yogi (ABK), Rio (ABK), Lil Fame (ABK), PacMan (ABK), Diddy Bop (ABK, tué quelques jours après Shoota Shellz en 2017), Errol (C-Block), Willie (C-Block), Daniel (C-Block)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Shoota Shellz |  |  | Y |  | C-Moe (NLMB); Yogi (ABK); Richie Rich (NLMB) | Big Nuskii (NLMB); C.B. (NLMB); Train (NLMB); Jay (ABK); Chief Dezz (ABK) | Pistol P (NLMB); Big Wet (NLMB) |
| King Scoobz |  |  | Y |  | Jermaine (ABK) |  |  |
| ShawtyHitt |  | Gangster Disciple |  | Y | Richie Rich (NLMB); Molly (NLMB); Joc (ABK); 1Eye (NLMB); Diddy Bop (ABK, tué quelques jours après ShootaShellz); Big Wet (NLMB, père de WetEmUp) | Lil Herb (NLMB); Ramo (NLMB); MaddMaxx (NLMB); G Ty (NLMB); Lil WetEmUp (NLMB); Lil Bibby (NLMB); Pig (NLMB); Mally (NLMB); Pat (NLMB); ManMan (NLMB); Melo Marcus (NLMB); Tay (NLMB); Squally Mac (NLMB); Shoddo (NLMB); Crazy James (NLMB); G Herbo (NLMB); Choppa (NLMB); Squeak (NLMB); G Herbo (NLMB); Yogi (ABK); Randell (ABK); Gulla (ABK); Puff (ABK); Sosa (ABK); Chief Taco (C-Block) | C-Moe (NLMB); Pistol P (NLMB); Lil Von (NLMB) |
| Meech |  |  |  |  | MaddMaxx (NLMB) |  |  |
| Awol |  |  |  |  | Pistol P (NLMB) |  |  |
| Shakey |  | Black Disciple |  |  | Lil Fame (ABK) |  |  |
| SGH | Squad Go Hard |  |  | Y | Daniel (C-Block); Big Wet (NLMB) | Grece (NLMB); Rellski (NLMB); Copo (NLMB); Keemo (NLMB); Levar (NLMB); Doowop (NLMB); Larro (NLMB); G-Marco (NLMB); Lil D (C-Block); Shawn Moe (C-Block); T-Glizzy (ABK); Bobo (ABK); Ken (ABK); Shmuney (ABK) | C-Moe (NLMB); Errol (C-Block); DeDe (ABK); Yogi (ABK) |
| Boo |  |  |  | Y | Vito (NLMB) |  |  |

### BlastHisAss

`https://privedatabase.wordpress.com/blasthisass/` · page 4745 · FCK HEAD$HOT · 2020-05-10

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| James (M-Town)Polo (051 Young Money)ChinaOMan (Sirconn City |  |  |  |  |  | Dro (MOB); Bookie (MOB); Tristo (051 Young Money); Bankroll Q (051 Young Money); FYB J Mane (Jaro City); Bud (Jaro City); TB (Tyquan World); Big Dee (STL/EBT) |  |

### BOCO HOOD

`https://privedatabase.wordpress.com/boco-hood-2/` · page 7908 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Gangster Disciples, Black Disciples, Black P.Stones
- **Allies:** CampCity, Trap Squad
- **Enemies:** FaceWorld, DoonSquad, ScrappVille, REC City, ABM, Hella Bandz

- **Members listed:** Edwin « Eazy Tarentino » Cook (décédé), Joc (décédé), BabyStone (décédé), Lil DeMarcus (décédé), Flip (décédé), BKJ (décédé), Foxx (décédé), BooG (décédé, tué en 2019)

- **Bodies attributed to the set:** Lil Face (FaceWorld), Rashad (FaceWorld), MG (FaceWorld), Marr (FaceWorld), AD (FaceWorld), Joseph (DoonSquad), Davonte (ScrappVille), Boonie (REC City), Tay (ABM), BudaMan (REC City), Josh (FaceWorld), Ricky (FaceWorld), CJ (HellaBandz), Cello (FaceWorld)

### Booka

`https://privedatabase.wordpress.com/booka/` · page 4753 · FCK HEAD$HOT · 2020-05-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Charles (M-Town)Innocent |  |  |  |  |  | Travo (Jaro City); CEO Mike (Jaro City); CashCoon (Jaro City); EBoi (MOB); Domo (MOB); Lil Scrapp (MOB); Beans (MOB); Bookie (MOB); Rakeem (MOB); Dooski (MOB); Cleon (MOB); EBoi (MOB); Jeff (MOB); Reggie (MetBoyz); Priboy (051 Young Money); DJ Money (051 Young Money); Shawt Mac (051 Young Money); Killa Keemo (Brick$quad 069); Dez (Brick$quad 069); Lucky (STL/EBT) | Tyriq (Bloods d'Atlanta) |

### Breeze

`https://privedatabase.wordpress.com/breeze/` · page 3876 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Bankroll Q (051 Young Money) |  |  |  |  |  | MoKilla (No Luv City); D3 (No Luv City); Tay (No Luv City); Max LaFlare (No Luv City); Lil Ant (No Luv City); ManyNames (50 Strong); KD (051 Young Money) |  |

### BRICK CITY/600

`https://privedatabase.wordpress.com/brick-city-600/` · page 6277 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Black Disciples
- **Also known as:** Brick City
- **Allies:** O'Block, SquirtTown, Front$treet, Nicko Gang, THF 46, BlackGate, MoeTown, DukeSquad, SMB, 400E Murda Drive, Lowelife, NLMB, GMEBE, Risky Road
- **Enemies:** Jaro City, STL/EBT, Tyquan World, MOB, 051 Young Money, SuWu TTB, TYMB (part), Brick$quad 069, E-Block, 757, Stony Spot, Geo Drive, PBG
- **Notes:** Created mid-2010; formerly known as "Brick City", which was originally a Gangster and Black Disciples set before becoming Black Disciples only. The alliance with NLMB applies only to part of the 600's membership.

- **Bodies attributed to the set:** ??? (Jaro City), ??? (Jaro City), ??? (Jaro City), ??? (Jaro City), Hottie (Jaro City), Corey (Jaro City), Sammy Lo (Jaro City), TuTu (Jaro City), ??? (Jaro City), Derrick (Jaro City), Marlon (Jaro City), Kristle (innocente, MOB), Lil Scrapp (MOB), BayBay (MOB), Jamo (MOB), Dooski Tha Man (MOB), T-Streetz (051 Young Money), Fathead (051 Young Money), Polo (051 Young Money), Lil Marc (051 Young Money), Dale (STL/EBT), Odey (E-Spot), Charles (M-Town), James (M-Town), Javan (Innocent), ChinaOMan (Sirconn City Gangsters), Big V (Tyquan World), Coby (Tyquan World), Doc (No Luv City), Lil Mister (Wuga World), Michael (Bully Gang), MoeJoe (ChiefTown), Wookie (GeoDrive), White Mike (GeoDrive), BT (Risky Road), Travis (Jaro City, tué en 2019)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| 600Breezy |  | Black Disciple |  |  |  | B-Sko (Jaro City); Lil Joe (Jaro City); James (Jaro City); Dome (Jaro City); Flock (Jaro City); Rell Rell (Jaro City); Travo (Jaro City); EBoi (MOB); Lil G (MOB); Tank Montana (Drill City); Mr Man (Drill City); Fatz Mack (Drill City); Tino (Drill City); Ronald (Drill City); Reggie Baybee (CMB); Tristo (051 Young Money); Millz (051 Young Money); Lil Jay (STL/EBT); Lil Reggie (Brick$quad 069) | Michael (Bully Gang); Hottie (Jaro City); ChinaOMan (Sirconn City Gangsters) |
| BiteDown | 2x | Black Disciple |  | Y | James (M-Town); ChinaOMan (Sirconn City Gangsters); BayBay (MOB); Frère de sa petite amie (cousin de Lil Zay Osama); Sa petite amie (cousine de Lil Zay Osama); Innocent (STL/EBT) | NumbaNine (Jaro City); Gucci (Jaro City); Lil Darrell (STL/EBT); Dutchie (STL/EBT); K.I. (STL/EBT); Young (STL/EBT); Spoon (STL/EBT); Jiale (STL/EBT); FBG Duck (STL/EBT); Nut (MOB); T-Baby (MOB); KD (051 Young Money); Oochie (051 Young Money); TTB Kelz (SuWu TTB); Chunky (Tyquan World); Hershey (Tyquan World); Chief Mexico (Tyquan World); Nickel Bag (Tyquan World) | Polo (051 Young Money) |
| BlastHisAss | Blast Em | Black Disciple |  | Y |  | Dro (MOB); Bookie (MOB); Tristo (051 Young Money); Bankroll Q (051 Young Money); FYB J Mane (Jaro City); Bud (Jaro City); TB (Tyquan World); Big Dee (STL/EBT) | James (M-Town); Polo (051 Young Money); ChinaOMan (Sirconn City Gangsters) |
| CapFck12 | Capo, Steve Day | Black Disciple |  | Y | Jamo (MOB); Coby (Tyquan World); Dooski Tha Man (MOB) | Richie Jerk (Tyquan World); 2Times (Tyquan World); Archie (Jaro City); Motor (Jaro City); Mal (MOB); TB (Tyquan World); Rocko (051 Young Money) | Brick (STL/EBT) |
| Inky D |  | Black Disciple |  | Y |  | Lil Herl (Jaro City); NumbaNine (Jaro City); Dome (Jaro City); Dooski (MOB); Lil Jay (STL/EBT); Flame (STL/EBT); Kiddo (051 Young Money); Law (051 Young Money) | Dale (STL/EBT); Derrick (Jaro City) |
| Jusblow | BDK“. Il était proche de Lil Steve, Lil Boo et L'A Capone. Dans une bagarre contre TTB Nez, il reçoit une chaise et frappe Nez avec. En 2015, alors qu'il est à la sortie d'une boîte de nuit avec Lil Nick, ce dernier reçoit un headshot à la place de Jusblow, qui prend la fuite. Toujours en 2015, Stello est tué à sa place dans son véhicule, utilisé pour tuer Scrapp. En 2017, TW TB le fait courir, tout comme en 2018 ou Wooski le fait courir. Pour le «Steve Day | Black Disciple |  |  | Scrapp (MOB); Wookie (GeoDrive) | G-Mally (GeoDrive); G-Rayski (GeoDrive); Boo Man (Jaro City); Motor (Jaro City); Kobe (Jaro City); Ronte (Jaro City); Jyron (STL/EBT); Marly (STL/EBT); Mooche (MOB); 10Mille (MOB); Nut (MOB); Lil Shaan (MOB); Ario (051 Young Money) | Odey (E-Spot); Polo (051 Young Money); Dooski Tha Man (MOB); Tyriq (Bloods d'Atlanta) |
| Lil Dee |  | Black Disciple |  |  |  | Mikie (MOB); Dooski (MOB); Lil Scrapp (MOB); FBG Youny (STL/EBT); Rico (STL/EBT); Wooski (STL/EBT); Duskie (E-Block); Rock (Jaro City); TTB Nez (SuWu TTB) | James (M-Town); Scrapp (MOB) |
| Stello | Stello Tha Great, Stello Do Tha Dash | Black Disciple |  |  |  | 305 (Jaro City); Blocks (Jaro City); Krump (MuBu) | Hottie (Jaro City); MoeJoe (ChiefTown); Lil Scrapp (MOB) |
| Waldo | 4.0. | Black Disciple |  |  |  | Rell Rell (Jaro City); FYB Duke (Jaro City); Pooh Pooh (Tyquan World); Quinny Mac (No Luv City); Jefe (757); Cease (800); Rosé (051 Young Money) | Brick (STL/EBT); Coby (Tyquan World) |
| Makado |  | Black Disciple |  | Y | Washington (Innocente) | Beans (MOB); 10Mille (MOB); Lil Scrapp (MOB); Lil Loud (MOB); Jiale (STL/EBT); Brick (STL/EBT); CantGetRight (STL/EBT); Hari (Jaro City); Kobe (Jaro City); Po Lo (800); Dro (Tyquan World); Woo (051 Young Money) | Jamo (MOB); TB (Tyquan World); Dowell (Innocente) |
| Booka |  | Black Disciple |  |  | Charles (M-Town); Innocent (STL/EBT) | Travo (Jaro City); CEO Mike (Jaro City); CashCoon (Jaro City); EBoi (MOB); Domo (MOB); Lil Scrapp (MOB); Beans (MOB); Bookie (MOB); Rakeem (MOB); Dooski (MOB); Cleon (MOB); EBoi (MOB); Jeff (MOB); Reggie (MetBoyz); Priboy (051 Young Money); DJ Money (051 Young Money); Shawt Mac (051 Young Money); Killa Keemo (Brick$quad 069); Dez (Brick$quad 069); Lucky (STL/EBT) | Tyriq (Bloods d'Atlanta) |
| Cdai | 22 Shotz, Savage Squad Records | Black Disciple |  | Y | TuTu (Jaro City); ??? (Jaro City); Fathead (051 Young Money); Javan (innocent) | Lil Mike (Jaro City); Andre (MOB); Wooski (STL/EBT); Andrilla (051 Young Money); Chop (051 Young Money); Sly (051 Young Money); KD (051 Young Money); Lil Ant (051 Young Money); Chadon (Jaro City); Maino (MOB); Lil Pooh (GeoDrive); FBG Duck (STL/EBT); Nut (MOB); Keke (051 Young Money); Maneski (051 Young Money) | BT (Risky Road) |
| D.Rose |  | Black Disciple |  | Y | Doc (No Luv City); Dale (STL/EBT); Lil Marc (051 Young Money); Big V (Tyquan World) | Cam (Jaro City); 007 (Jaro City); NumbaNine (Jaro City); Domo (MOB); JuJu (MOB); Beans (MOB); Cash (STL/EBT); King Lil Jay (STL/EBT); RoRo (STL/EBT); FBG Cash (STL/EBT); FBG Butta (STL/EBT); Kreed Da Don (STL/EBT); Andrilla (051 Young Money); Keyso (051 Young Money); Rocko (051 Young Money); KD (051 Young Money); Chop (051 Young Money); Lil Ant (051 Young Money); NewMoney (051 Young Money); Boss Veze (50 Strong); Lil Duwuap (50 Strong); Chuck (No Luv City); Man (No Luv City); Benz (MetBoyz); Kelles (Brick$quad 069); West (Geo Drive); Maine Maine (Princeton Mobb); Lil Mook (Tyquan World); D-Money (Tyquan World); LJ (Tyquan World) | Don Von (Bully Boys); Fathead (051 Young Money); Dirty Rell (Jaro City); ? (Jaro City); Dougo (50 Strong); Javan Boyd (innocent) |
| D-Thang |  | Black Disciple | Y |  | ??? (Jaro City); Hottie (Jaro City); Kristle (innocente, MOB) | Kenny (Jaro City); Wayne (Jaro City); Baby D (Jaro City); Lil Panky (Jaro City); Joe (Jaro City); Tilgo (Jaro City); Santana (Jaro City); Ron (Jaro City); Gucci (Jaro City); 50Shot (Jaro City); WeeWee (STL/EBT); Meechie (STL/EBT); Chief Geo (MOB); Beans (MOB); Devon (MOB) |  |
| L'A Capone | Lil Assassin | Black Disciple | Y |  | Odey (E-Spot) | J-Ball (Von World); JGlizzy (Von World); Rio (MOB); Lil Des (MOB); Rakeem (MOB); 10Mille (MOB); Chamberlain (MOB); Beans (MOB); Lil Will (MOB); RoRo (STL/EBT); Lil P (STL/EBT); FBG Butta (STL/EBT); King Lil Jay (STL/EBT); Motor (Jaro City); Hari (Jaro City); TTB Nez (SuWu TTB); Lil Twan (Tyquan World) | Fathead (051 Young Money); Modell (STL/EBT) |
| Lil Boo |  | Black Disciple | Y |  | Sammy Lo (Jaro City); Polo (051 Young Money); Scrapp (MOB) | Dano (Jaro City); White Boy (Jaro City); Marvin (Jaro City); 50Shot (Jaro City); Noyd (MOB); Torry (MOB); Gucci (MOB); Mooche (MOB); Bookie (MOB); Lil G (MOB); Copo (MOB); Naro (STL/EBT); C-Ball (STL/EBT); Melly (051 Young Money); Lil Roy (051 Young Money); Raymon (051 Young Money); Wacko (051 Young Money); Richie Jerk (Tyquan World); OC (CrankTown) | Hottie (Jaro City); MoeJoe (ChiefTown); Kristle (innocente, MOB); Odey (E-Spot); Javan (Innocent); Venzel (Tyquan World) |
| Manny | BigSix0 | Black Disciple |  |  | Derrick (Jaro City); Travis (Jaro City, tué en 2019) | Creed (Jaro City); Mark (Jaro City); Ron (Jaro City); Boss (Jaro City); Billionaire Black (STL/EBT); Pooney (Tyquan World) | T-Streetz (051 Young Money) |
| Memo | Steve Day | Black Disciple |  |  | Lil Mister (Wuga World) | CantGetRight (STL/EBT); FBG Duck (STL/EBT); DJ (MOB); Famous Mac (MOB); Lil Shaan (MOB); Lil Shaan (MOB); Lil Des (MOB); Wookie (MOB); Lil Loud (MOB); Lil Loud (MOB); 10 Mille (MOB); KG (Wuga World); Lil Beam (Wuga World); Lil Twan (Tyquan World); Lil Cho (Tyquan World); Lil Ant (051 Young Money); PD (051 Young Money, 2019); Lil Danny (051 Young Money, 2019); SV (051 Young Money, 2019); Fat Shawty (Jaro City); Mal (Jaro City) |  |
| M-Thang |  | Black Disciple |  | Y | T-Streetz (051 Young Money) | Lil Darrell (Jaro City); Marcus (Jaro City); Chief Ty (Jaro City); Boom (051 Young Money); Millz (051 Young Money); Rosé (051 Young Money); Greedy (MetBoyz) | Marlon (Jaro City); James (M-Town) |
| RondoNumba9 |  | Black Disciple |  | Y | ? (Jaro City); BT (Risky Road) | TuTu (Jaro City); Brick (STL/EBT); JaJa (Jaro City); Woo (051 Young Money); Poone (SuWu TTB); Lil Bubba (Tyquan World); Big Dee (STL/EBT); Lil Scrapp (MOB); Oochie (051 Young Money); Mally (051 Young Money) | Fathead (051 Young Money); Charles (M-Town); Javan (Innocent) |
| Tay600 |  | Black Disciple |  | Y | 180 (CrankTown) | Lil Corey (Jaro City); TuTu (Jaro City); Skinny (Jaro City); Rock (Jaro City); Motor (Jaro City); Damage (Jaro City); Shell Da Don (MOB); BayBay (MOB); Dutchie (STL/EBT); FBG Duck (STL/EBT); Lil P (STL/EBT); Lil Jay (STL/EBT); FBG Butta (STL/EBT); Lil Jay (STL/EBT); Lil Cho (Tyquan World); Aero (051 Young Money); Keyso (051 Young Money); Remy (051 Young Money); Melly (051 Young Money); Ario (051 Young Money); Freaky (Brick$quad 069) | TuTu (Jaro City); Charles (M-Town); Innocent (STL/EBT); Innocent (STL/EBT); Javan (Innocent) |
| Trigga |  | Black Disciple |  | Y | MoeJoe (ChiefTown) |  |  |
| Baldy |  | Black Disciple | Y |  |  |  | Junebug (MOB) |
| Lil Steve |  | Black Disciple | Y |  |  | Lil Mike (Jaro City); Tell (Jaro City); Scrapp (MOB); Scrapp (MOB) |  |
| FaceSixO |  | Black Disciple |  |  |  | Darrion (MOB); Clutch (MOB); Mooche (MOB); TB (Tyquan World); PD (051 Young Money, 2019); Lil Danny (051 Young Money, 2019); SV (051 Young Money, 2019) | Jamo (MOB); Lil Mister (Wuga World); Polo (051 Young Money) |
| Young Famous |  | Black Disciple |  |  | Michael (Bully Gang) | DipLow (Jaro City); P5 (Jaro City); Weedy (Jaro City); Q-Tip (MOB); Bookie (MOB); Lil G (MOB); JuJu (MOB) |  |
| Edai |  | Black Disciple |  |  |  | Binky (Jaro City); Marquis (Jaro City); Dome (Jaro City); Trigga (Jaro City); Jamo (MOB); BJacob (MOB); EBoi (MOB); Rooga (MOB); Bookie (MOB); Lil G (MOB); Tezzy (MOB) | Michael (BullyGang) |
| Boowop | Booda | Black Disciple |  |  |  | Lieemy (051 Young Money); Truey (800); Rico (Geo Drive) |  |
| Porkey |  | Black Disciple |  |  |  | Wooski (STL/EBT) |  |
| AK |  | Black Disciple |  |  | ??? (Jaro City) |  | T-Streetz (051 Young Money) |
| JR |  | Gangster Disciple |  | Y | ??? (???) |  |  |
| BossMoo |  | Black Disciple |  |  |  |  | Derrick (Jaro City); Travis (Jaro City) |

### BRICK$QUAD 069

`https://privedatabase.wordpress.com/brickquad-069-2/` · page 7496 · FCK HEAD$HOT · 2019-11-08

- **Nations:** Insane Gangster Disciples
- **Allies:** CMB, JJ Gang, Wuga World, STL/EBT, Tay City, MOB
- **Enemies:** SMB, AMG, Dipset, Lowelife, DOD, Lamron, Doggpound, O'Block, 600, FaceWorld
- **Former allies:** Dipset
- **Notes:** Founded by Killa Kellz, a former OG of Lamron. War with Dipset broke out after Dipset killed Aiki.

- **Bodies attributed to the set:** Lil Mavin (AMG), EK (AMG), Traydoe (AMG), Ron (Lowelife), Big E (Lowelife), Ty (Dipset), Fanny (Dipset), Vaughn (Dipset), Spencer (Dipset), Lil Lodi (Dipset), Pervis (Dipset), Lance (Dipset), ED (Dipset), D.Rose (Dipset), Big Lick (Dipset), D-Tae (Dipset), Dre (DOD), Al (DOD), Kenneth (DOD), Keke (Lamron), Wudae (TayTown), Darnell (SMB), Boi Boi (SMB), JaJuan (FaceWorld), Bando Bandz (FaceWorld), Lafayette (Doggpound), Bud (Doggpound), Big Law (SMB, tué en 2019)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Swagg Dinero |  | Gangster Disciple |  |  |  | Big Pat (Lamron) | Keke (Lamron) |
| Aiki |  | Gangster Disciple | Y |  |  | Lil T (AMG); Mike (AMG); Tay Tay (AMG) |  |
| Ant Ant |  | Gangster Disciple |  | Y | Boi Boi (SMB); Vaughn (Dipset) | Dumb Worm (Dipset); Lil B (AMG); Montana (AMG); DeDe (Lamron); Justo (Lamron); BallOut (Lamron); Mack (Lamron); Poo Poo (SMB) | Ty (Dipset) |
| BDK Kevo |  | Gangster Disciple |  |  | Bando Bandz (FaceWorld); ??? (???) |  |  |
| Big Josh |  | Gangster Disciple | Y |  | Wudae (TayTown) | Tony (AMG); Loud Shawty (AMG); Raymo (SMB); Fat Ant (SMB); DK (Lamron) |  |
| ClayDoe |  | Gangster Disciple |  |  | Dre (DOD); D-Tae (Dipset) | Zelly (AMG); Prince Tay (AMG); J Nasty (Dipset); Meco (Dipset); Lil Block (Doggpound); Jeezy (Doggpound); Billups (Lamron); Pluto (Lamron); Lil Reese (Lamron) | Fanny (Dipset) |
| Freaky |  | Gangster Disciple |  | Y |  | Mimms (Lamron); Ty (Lamron); JL300 (Lamron) | Keke (Lamron) |
| J-Real |  | Black P.Stone |  |  |  | Bill (Dipset); Greg (Doggpound); J Money (AMG); Ello (AMG); Marco (FaceWorld); June (Lamron); Twin (Lamron); Marz (Lamron) | Boi Boi (SMB) |
| Kelles |  |  |  | Y |  | Face (TYMB); Ello (AMG); Black (Dipset); Makado (600); Rodie (Lamron); Dee (Lamron) | EK (AMG); Darnell (SMB) |
| Killa Keemo |  | Gangster Disciple |  |  | ??? (époque TVL); ??? (époque TVL); Ty (Dipset); Fanny (Dipset); Lafayette (Doggpound); Wudae (TayTown) | BJ (Doggpound); Troy (Doggpound); SD (BlackGate); BCity (Hitzsquad); FatBoyChubbz (Lamron); T-Mac (Lamron); D-Nice (Lamron); Bam (Dipset); Rio Dinero (Dipset); Shellz (Lowelife); Rocky (AMG); Lil Jeff (SMB); BCity (Central City); D.Rose (600) |  |
| Killa Kellz | Brick$quad 069 | Black Disciple |  | Y | JackBall (DOD) | Yung Mal (No Luv City); Rio (No Luv City); Dopes (Lamron); Ty (Lamron); Johnny (Lamron); D-Boy (Lamron) | Ty (Dipset) |
| Killa Tell |  | Gangster Disciple |  | Y | Lil Mavin (AMG); EK (AMG) |  |  |
| Lil Don |  | Gangster Disciple | Y |  | Traydoe (AMG) | Prince Tay (AMG); Lil D (Lowelife); Lil C (Lowelife); Fat Boi (Lowelife); Tooly (Lowelife); Jaquan (Lamron); D-Lo (FaceWorld); JT (FaceWorld); Lil Zack (Doggpound); Kenny Mac (Doggpound); D.Rose (600) | Polo Da Don (Doggpound); Big Law (SMB) |
| Lil Jojo | BDK | Gangster Disciple | Y |  |  | BoeLeg (AMG); Peeski (AMG); Lil T (AMG); Dookie (TYMB); Lil Durk (Lamron); J-Roc (Lamron); J-Roc (Lamron); Rodie (Lamron); JL (Lamron); Weezy (Lamron); Lil Reese (Lamron); Fresh (Lamron); Lil Block (Doggpound) |  |
| Moosalina |  | Gangster Disciple |  |  | Keke (Lamron); Lafayette (Doggpound) | C-Dub (Doggpound); BJ (Doggpound); Mo Bodies (FaceWorld); J-Red (AMG); Zelly (AMG); Beano (AMG); Lil Ant (Lowelife); King Clark (Lowelife); Lil D (Lowelife); D.Rose (600) | JaJuan (FaceWorld) |
| P.Rico |  | Gangster Disciple |  |  | Al (DOD); Big Law (SMB) | Rocky (AMG); Rob (AMG); Beano (AMG); Madd Maxx (Dipset); React Da DonAl (DOD); CJ (DOD); CheCheDee (Lamron); T-Mac (Lamron); Salo (Lamron); Black (Lamron); Polo Da Don (Doggpound) | Dre (DOD); DODFanny (DOD); Bando Bandz (FaceWorld) |
| YoYo |  | Gangster Disciple |  |  | Big Law (SMB) | Loso (Lowelife); Reaper (Lowelife); Harvey (Lowelife); Big Tone (Lowelife); Rio (Lowelife); Tooly (Lowelife); Ralph (Doggpound); Dot (Doggpound) | Bando Bandz (FaceWorld) |
| Dell Gotti |  | Black Disciple |  |  | D.Rose (Dipset) |  |  |

### BRICKYARD (4 CORNER GLO GANG)

`https://privedatabase.wordpress.com/brickyard-4-corner-glo-gang/` · page 7982 · FCK HEAD$HOT · 2020-01-27

- **Nations:** 4 Corner Hustlers
- **Also known as:** 4 Corner Glo Gang
- **Allies:** PoppyGang
- **Enemies:** 4100, 4400, KP-Gang, MOA, LMG, LA Gang
- **Notes:** Known for their affiliation with Glo Gang. In 2017, several high-ranking members were arrested under a federal RICO investigation.

- **Members listed:** Bro Man est un 4 Corner Hustler. Il est un OG de la Brickyard. En 2017, il est arrêté après une longue enquête sur son set, il encourt une peine de mort. Il était un tueur à gage pour le Cartel de Sinaloa.

- **Bodies attributed to the set:** Carlos CaldwellMaximillion McDanielLevar SmithGeorge KingFootsKato (Latin Kings)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Carlos CaldwellMaximillion McDanielLevar SmithGeorge KingFoo |  | Latin Kings |  |  |  |  |  |
| ManeMane |  | Four Corner Hustler |  |  |  |  |  |
| Sam Bug ou Terminator |  | Four Corner Hustler |  |  |  |  | Carlos CaldwellMaximillion McDanielLevar SmithGeorge KingFoots |
| Scarface ou Trigga |  | Four Corner Hustler |  |  |  |  | George KingFoots |
| Juhwun |  | Four Corner Hustler |  | Y |  |  | George KingFoots |
| Dookie (décédé, tué en 2019)Zay (décédé)Lil Chello (arrêté e |  |  | Y |  |  |  |  |

### BUFF CITY

`https://privedatabase.wordpress.com/buff-city-2/` · page 7964 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Black Disciples
- **Allies:** O'Block, 600
- **Enemies:** MBAM
- **Notes:** Located in the Wild 100's. Rapper "Joc Da Block" is a member. Many current members formerly belonged to WIIIC City (now O'Block); some were close to Odee of WIIIC City. In 2019 a member close to Deathrow 085 killed an NLMB member.

- **Members listed:** C-Money aussi connu sous le nom de “BD” est un Black Disciple. Il est actuellement incarcéré pour le meurtre de Willie de la NLMB. Il était proche d'Aero du Deathrow 085.

- **Bodies attributed to the set:** Roc (MBAM), Glizzy (MBAM), Jon Jon (MBAM), Willie (NLMB)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Willie (NLMB, tué en 2019) |  |  |  |  |  |  |  |
| Joc Da BlockWayne (décédé)D.Rose (décédé)C-MoneyBuff (décédé |  |  | Y |  |  |  |  |

### BWst LATIN KINGS

`https://privedatabase.wordpress.com/bwst-latin-kings/` · page 7997 · FCK HEAD$HOT · 2020-02-05

- **Nations:** Latin Kings
- **Also known as:** Berwyn & Winthrop Kings
- **Allies:** _none_
- **Enemies:** Winona Stones
- **Notes:** Located in the North Pole area of Chicago.

- **Members listed:** Jonathon est un Latin King. Il est actuellement incarcéré.

- **Bodies attributed to the set:** Michael (Winona Stones), Robert (Winona Stones), Mack (PottBlock/LOC City)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Michael (Winona Stones)Robert (Winona Stones) |  |  |  |  |  |  |  |
| Michael |  | Latin King |  | Y | Michael (Winona Stones); Robert (Winona Stones) |  |  |
| YG |  | Latin King |  | Y | Mack (PottBlock/LOC City) |  |  |

### Cadarro

`https://privedatabase.wordpress.com/cadarro/` · page 1897 · FCK HEAD$HOT · 2020-04-10

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Mon (DamenVille) |  |  |  |  |  |  |  |

### CapFck12

`https://privedatabase.wordpress.com/capfck12/` · page 4746 · FCK HEAD$HOT · 2020-05-10

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Jamo (MOB) |  |  |  |  |  | Richie Jerk (Tyquan World); 2Times (Tyquan World); Archie (Jaro City); Motor (Jaro City); Mal (MOB); TB (Tyquan World); Rocko (051 Young Money) | Brick (STL/EBT); Coby (STL/EBT) |

### CCG

`https://privedatabase.wordpress.com/ccg-2/` · page 8001 · FCK HEAD$HOT · 2020-02-08

- **Nations:** Conservative Vice Lords
- **Allies:** 600 CVLs
- **Enemies:** TVL sets

- **Members listed:** CoCo (décédé), Pat (décédé), Lil E (décédé), Nell (décédé), Lil Sam (décédé)

### Cdai

`https://privedatabase.wordpress.com/cdai/` · page 4754 · FCK HEAD$HOT · 2020-05-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| TuTu (Jaro City)Fathead (051 Young Money)Javan (Innocent) |  |  |  |  |  | Lil Mike (Jaro City); Andre (MOB); Wooski (STL/EBT); Andrilla (051 Young Money); Chop (051 Young Money); Sly(051 Young Money); KD (051 Young Money); Lil Ant (051 Young Money); Chadon (Jaro City); Maino (MOB); Lil Pooh (Geo Drive); FBG Duck (STL/EBT); Nut (MOB); Keke (051 Young Money); Maneski (051 Young Money) | BT (Risky Road) |

### CEO

`https://privedatabase.wordpress.com/ceo/` · page 4231 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| T-Mac (FollyBoyz)Molly (FollyBoyz)Scrap (FollyBoyz) |  |  |  |  |  | 50Shot Mall (FollyBoyz); Choppa (Lamron) |  |

### Chief Diddy

`https://privedatabase.wordpress.com/chief-diddy/` · page 3799 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Stain (No Luv City)Glizzy (No Luv City) |  |  |  |  |  | OG Haitian (50 Strong); Rosé (50 Strong); Breezy (50 Strong); King Murda (50 Strong); Jimmy (No Luv City); G Rasto (No Luv City); Izzy (No Luv City); Poom (Dumpstreet); T Man (Dumpstreet); PD (051 Young Money); Lil Danny (051 Young Money); Kymeon (051 Young Money); Maneski (051 Young Money); G-Rayski (GeoDrive); G-Mally (GeoDrive) | Earl (No Luv City) |

### CHRIS WORLD

`https://privedatabase.wordpress.com/chris-world-2/` · page 6535 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Black Disciples
- **Allies:** Zone7, 400E Murda Drive, Drill City, Mixx Mobb
- **Enemies:** STL/EBT, TYMB, MTV, Whiz City
- **Notes:** Based in Washington Park; founded in tribute to Chris of TYMB after his death. Chris World gradually became a fully independent set and went to war with its origin set, TYMB.

- **Bodies attributed to the set:** Obama (TYMB), Reginald (TYMB), Cash (Whiz City)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Kenny Mac |  | Black Disciple | Y |  | Obama (TYMB) |  |  |

### CHUCKMOBB

`https://privedatabase.wordpress.com/chuckmobb/` · page 973 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Gangster Disciples
- **Allies:** No Luv City
- **Enemies:** _none_

- **Members listed:** Earl (décédé)

### CoKilla

`https://privedatabase.wordpress.com/cokilla/` · page 3800 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Temmo (50 Strong) |  |  |  |  |  | Blood (50 Strong); Juice (50 Strong); Csko (50 Strong); Major (No Luv City); Teeski (No Luv City); KC (No Luv City); Alo (Shields); Hov (Dumpstreet); Ario (051 Young Money); James (051 Young Money) | Lil Doc (No Luv City); Big Meech (50 Strong); Lil Marc (051 Young Money) |

### COREY MONEY BROTHERS (CMB)

`https://privedatabase.wordpress.com/corey-money-brothers-cmb/` · page 6536 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Insane Gangster Disciples
- **Also known as:** CrazyVille
- **Allies:** Brick$quad 069
- **Enemies:** _none_
- **Notes:** Based in Englewood.

- **Bodies attributed to the set:** Romel (AMG), Lil D (AMG), Pokey (Doggpound), Webo (Doggpound), Uh-Uh (Lowelife), Ant Ant (Doggpound), J-Mann (Lowelife), Quenton (Lowelife), Mac (AMG), Etho (Lowelife), Darius (DOD), 3Much (Lowelife), Scottie (SMB), Albert (FaceWorld), Spencer (AMG), Leste (SMB), Jamal (Doggpound), Dudity (Doggpound), Killa (Lowelife), Little (TYMB), Marcus (Doggpound), Sap (Lamron), JuiceMan (Doggpound), OTF Tay (Lowelife), Andre D. Donner Jr. Tay (Lowelife), D-Ez (Doggpound)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Marco |  | Gangster Disciple |  | Y | Jamal (Doggpound); Dudity (Doggpound); Little (TYMB) | Bobby (Lowelife); Tee (AMG); J Money (AMG); Ro Ro (TYMB); Kenny Mac (Doggpound); Polo Da Don (Doggpound); Prince Dre (O'Block); Day Day (Lamron); 300OJ (Lamron) | Marcus (Doggpound) |
| Darnell |  | Gangster Disciple |  |  | JuiceMan (Doggpound) | Kenny Mac (Doggpound) |  |
| Art |  | Gangster Disciple |  | Y | Mac (AMG); Etho (Lowelife) |  |  |
| Reggie Baybee |  | Gangster Disciple |  |  |  | Lil John (Lowelife) |  |

### CORPS 🔞

`https://privedatabase.wordpress.com/corps/` · page 2462 · FCK HEAD$HOT · 2020-04-13

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| 13 Octobre 2019, 7535 S. Dobson |  |  |  |  |  |  |  |
| 2 membres de La Raza |  |  |  |  |  |  |  |
| Hothead (FaceWorld 069) |  |  |  |  |  |  |  |
| Coby (STL/EBT) |  |  |  |  |  |  |  |
| FYB Archie (Jaro City) |  |  |  |  |  |  |  |
| Lil Moe (GME) |  |  |  |  |  |  |  |
| Sakinah (GME) |  |  |  |  |  |  |  |
| Gremlin (3000ST) |  |  |  |  |  |  |  |
| Jamie Stone (8-Tray) |  |  |  |  |  |  |  |
| Kenneka Jenkins (innocente) |  |  |  |  |  |  |  |
| Krump (Dro City) |  |  |  |  |  |  |  |
| KTS Von (KTS) |  |  |  |  |  |  |  |
| Demetrius Cooper |  |  |  |  |  |  |  |
| Lil Marc (051 Young Money) |  |  |  |  |  |  |  |
| Membre des Satan Disciples |  |  |  |  |  |  |  |
| ShootaShellz (BlackMobb) |  |  |  |  |  |  |  |
| Waldo (600) |  |  |  |  |  |  |  |
| Welch (So Icy) |  |  |  |  |  |  |  |
| Zack “Zack TV” Stoner (GoonTown) | Zack TV |  |  |  |  |  |  |
| Biyo (MTG) |  |  |  |  |  |  |  |

### CRANKTOWN

`https://privedatabase.wordpress.com/cranktown/` · page 7915 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Black P.Stones
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Almost no one represents this set today; most members became members of the "800" after Diddy's death.

- **Members listed:** 180 (décédé), Chief SheedBig GuyDiddy (décédé), GenoOCSerg (décédé)

- **Bodies attributed to the set:** Saw (Dro City), Sno (Dro City), Earl (Dro City), Twon (Dro City), Blue (Dro City), Black Diamond (Dro City), Renauld (Roc Creek), Papa (Roc Creek), CMB (TYMB), Kush (TYMB), Maine Thang (TYMB), Scoot Boot (Dro City)

### CUTTAGANG

`https://privedatabase.wordpress.com/cuttagang-2/` · page 7988 · FCK HEAD$HOT · 2020-01-30

- **Nations:** Vice Lords
- **Allies:** GreedyGang, MayBlock, Foster Park, KTS, 3rd Ward
- **Enemies:** E-Spot, TrayTown, RMG, 8Tray
- **Notes:** A set dating back to the 1980s.

- **Members listed:** Prince Cutta

### D.Rose

`https://privedatabase.wordpress.com/d-rose/` · page 4755 · FCK HEAD$HOT · 2020-05-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Doc (Landlord COV)Dale (STL/EBT)Lil Marc (051 Young Money)Bi |  |  |  |  |  | Cam (Jaro City); 007 (Jaro City); NumbaNine (Jaro City); Domo (MOB); JuJu (MOB); Beans (MOB); Cash (STL/EBT); King Lil Jay (STL/EBT); RoRo (STL/EBT); FBG Cash (STL/EBT); FBG Butta (STL/EBT); Kreed Da Don (STL/EBT); Andrilla (051 Young Money); Keyso (051 Young Money); Rocko (051 Young Money); KD (051 Young Money); Chop (051 Young Money); Lil Ant (051 Young Money); NewMoney (051 Young Money); Boss Veze (50 Strong); Lil Duwuap (50 Strong); Chuck (ChuckMobb); Man (No Luv City); Benz (MetBoyz); Kelles (Brick$quad 069); West (Geo Drive); Maine Maine (Princeton Mobb); Lil Mook (Tyquan World); D-Money (Tyquan World); LJ (Tyquan World) | Don Von (Bully Boys); Fathead (051 Young Money); Dirty Rell (Jaro City); Dougo (50 Strong); Javan Boyd (Innocent) |

### DAMENVILLE

`https://privedatabase.wordpress.com/damenville-2/` · page 7992 · FCK HEAD$HOT · 2020-02-01

- **Nations:** Gangster Disciples
- **Allies:** LOC City, Art Gang, PocketBoyz
- **Enemies:** JackBoys, Justine, MurdaField, LordsVille, TytoLand

- **Bodies attributed to the set:** AJay (TytoLand), C-Murda (JackBoys), ??? (TytoLand), ??? (TytoLand), ??? (TytoLand), ??? (TytoLand), ??? (TytoLand), ??? (LordsVille), ??? (LordsVille), ??? (LordsVille), ??? (LordsVille), ??? (LordsVille), ??? (LordsVille), ??? (LordsVille), ??? (LordsVille), ??? (LordsVille)

### DAMENVILLE

`https://privedatabase.wordpress.com/damenville/` · page 366 · FCK HEAD$HOT · 2020-03-27

- **Nations:** Gangster Disciples
- **Also known as:** BloodGang
- **Allies:** LOC City, WB 057
- **Enemies:** _none_
- **Former allies:** JackBoys 052

- **Members listed:** Steveo (décédé), Tae (décédé), Ill Will (décédé), Bop D (décédé), By (décédé), Tuta (décédé), Mon (décédé), Tra'Don (décédé)

- **Bodies attributed to the set:** Tyto (5th Ward Life), JonJon (5th Ward Life), Stephon (5th Ward Life)

### Darren

`https://privedatabase.wordpress.com/darren/` · page 3879 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Big Lonnie (051 Young Money) |  |  |  |  |  | Israel (No Luv City); King Murda (50 Strong); Chief Rell (50 Strong) |  |

### DEATHROW 085

`https://privedatabase.wordpress.com/deathrow-085-2/` · page 7904 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Conservative Vice Lords
- **Allies:** _none_
- **Enemies:** GMEBE, NLMB, Latin Dragons
- **Former allies:** GMEBE
- **Notes:** Some members were once allied with GMEBE until GMEBE's Roe was killed; the war with the Latin Dragons goes back more than 15 years.

- **Bodies attributed to the set:** Roe (GMEBE), Sweetie (?), Millie (?), Scoota (NLMB)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Jayla |  | Vice Lord |  |  | Sweetie (?) |  | Willie (NLMB, tué en 2019) |
| Savo |  | Vice Lord | Y |  |  |  | Willie (NLMB, tué en 2019) |
| Fatlord |  | Vice Lord |  | Y | Elvis Garcia (tué en 2020) |  | Willie (NLMB) |

### Dell

`https://privedatabase.wordpress.com/dell/` · page 4235 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Zio (FollyBoyz)Kamikazi Mazi (FollyBoyz) |  |  |  |  |  |  |  |

### DELL MOB

`https://privedatabase.wordpress.com/dell-mob-2/` · page 7935 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Also known as:** Chris Block, ZipSet
- **Allies:** Welch World, MurdaTown
- **Enemies:** 051 Young Money
- **Former allies:** 051 Young Money
- **Notes:** Based in Bronzeville/Oakland; represents 'OJ World' in tribute to deceased Jaro City member OJ.

- **Members listed:** John JohnGlock BoyMillieKennyMeechyBlueChrisMoe (décédé), TrelloIkey MikeyDon Don (décédé), GNuskiRoscoRissaBaby BoyBluskiSohn (décédé), PatManZip (décédé), Vonta4PacKedron (décédé), ItchDawgMaurice (décédé, tué par la police en 2018)

- **Bodies attributed to the set:** Joshua (Jigdogs), Terrell (Jigdogs), Von (Jigdogs), Dooda (Jigdogs)

### DIPSET BLVD

`https://privedatabase.wordpress.com/dipset-blvd-2/` · page 7999 · FCK HEAD$HOT · 2020-02-05

- **Nations:** Gangster Disciples
- **Allies:** _none_
- **Enemies:** OTE
- **Former allies:** OTE
- **Notes:** A faction of OTE based in Cabrini Green; killed PBG member Dutty in 2019 at a shared party, after which OTE and several PBG allies turned against them.

- **Bodies attributed to the set:** Dutty (PBG, tué en 2019)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| AntDog |  | Gangster Disciple |  |  |  |  | Dutty (PBG) |

### DIPSET/FRONT$TREET

`https://privedatabase.wordpress.com/dipset-fronttreet/` · page 6278 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Black Disciples
- **Also known as:** O-Six-Uno, Glory Boyz, Dipset, Baldy World, Blood Gang, Mill Block
- **Allies:** BlackGate, 600, O'Block
- **Enemies:** MOB, Von World, GeoDrive, SKD, Tyquan World, STL/EBT, Jaro City
- **Notes:** Producer DJ Kenn and rapper Chief Keef, who represents them, are from this set; was a drug fortress in the 2000s and remains a major dealer set despite the towers being demolished.

- **Bodies attributed to the set:** MikeBall (MOB), Lemo (MOB), Junebug (MOB), Anton (MOB), Lionel (MOB), Cortez (MOB), Lil Dee (MOB), Chuck (MOB), Lonnie (MOB), Worm (M-Town), Stutta (M-Town), Jimmy (Von World), Dennis (Von World), Marcus (Von World), Shawntell (Von World), Muhammed (Von World), Chris (T-Luv), Won Won (Met Boyz), Lil Mike (GeoDrive), Anthony (SKD)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Antonio |  |  |  | Y |  |  | Chris (T-Luv) |
| Block Poppa | Mooski | Black Disciple |  | Y | Won Won (Met Boyz); Anthony (SKD) | Polo (Tyquan World); Lil Cho (Tyquan World); G-Rayski (GeoDrive); G-Rayski (GeoDrive); Lil Shaan (MOB); Lil Des (MOB); Lil Shaan (MOB); Lil Shaan (MOB); Rakeem (MOB); Lil Bobo (MOB); Wookie (MOB); Jyron (STL/EBT) | Lil Mike (GeoDrive) |
| Blood Money | Big Glo | Gangster Disciple |  |  | Lemo (MOB); Dennis (Von World) | Shy Glizzy (Washington D.C.) |  |
| DaDa | grâce | Black Disciple |  | Y | Junebug (M-Town); Cortez (MOB); Chris (T-Luv) | Rob (MOB); Domo (MOB); Q-Tip (MOB); BD (MOB); Davo (MOB); Maino (MOB); Dooski (MOB); Nut (MOB); Lil Scrapp (MOB); Mooche (MOB); DJ (MOB); Rock (Jaro City); Tristo (051 Young Money); Cello (STL/EBT) | Lonnie (MOB) |
| Fredo Santana |  | Black Disciple | Y |  | Lonnie (MOB) | Reese (MOB); Gucci (MOB); Black Boi (MOB); Dooski (MOB); Domo (MOB); Nut (MOB); Mooche (MOB) | MikeBall (M-Town) |
| GBE Capo | Drama | Black Disciple | Y |  |  | Mikie (MOB); Trevon (MOB); Curfew (BlackMobb); Lil Ant (Jaro City); Pook (MTG) | T-Bone (Black Mobb) |
| Juice Da Savage | Ninoratchi | Black Disciple |  |  | Chuck (MOB) | JGlizzy (Von World); Casper (Von World); JohnBoi (MOB); Raw Rell (MOB); Killa K.I. (MOB); Dooski (MOB); Myro (MOB) |  |
| Lil Los |  | Black Disciple |  | Y | Innocent | Leek (MOB); Nut (MOB); Richie Jerk (Tyquan World); White Mike (Tyquan World); LJ (Tyquan World); Dot (Tyquan World); Weezy (Jaro City) | Venzel (Tyquan World) |
| Nate |  | Black Disciple |  |  |  |  | Junebug (MOB) |
| Nino |  | Black Disciple |  |  | Muhammed Kebbeh (Von World) | Eddo (MOB); BayBay (MOB); John Boi (MOB); Dooski (MOB); Rooga (MOB); JuJu (MOB); King Cole (STL/EBT); Big G (Von World) | Worm (MOB); Dooski Tha Man (MOB) |
| Quono | QuonaMillie | Black Disciple | Y |  |  | Crusha (MOB); DJ (MOB); Noah (MOB); Damari (MOB); 10Mille (MOB); Mallie-G (Tyquan World); Pol (Tyquan World); TB (Tyquan World); Lil Mook (Tyquan World) | Muhammed Kebbeh (Von World) |
| Republican |  | Black Disciple |  | Y | Lionel (MOB) | Ron (Von World); Tyree (Von World); Rell (Von World); Fred (MOB); Cleon (MOB); Trevon (MOB); Beans (MOB); Andre (MOB) | Junebug (MOB); Marcus (Von World); Shawntell (Von World) |
| Toon |  | Black Disciple |  | Y | Lil Mike (GeoDrive) | Pooney (Tyquan World); Chief Mexico (Tyquan World); Kobe (Jaro City); Lil Des (MOB); Lil Moe (MOB) | Won Won (MetBoyz) |
| T-Slick | Left Eye | Black Disciple |  | Y |  | Javo (MOB); Weezy (MOB); Maino (MOB); Pyro (MOB); Mikie (MOB); El Ruger (Jaro City); Lil Darrell (Jaro City); FBG Butta (STL/EBT); Montana (051 Young Money); T-Streetz (051 Young Money) | Chuck (MOB) |
| Gino Marley |  | Black Disciple |  |  |  | Blow (Von World); Ced (MOB); BJacob (MOB) |  |
| Caper Boy |  | Black Disciple |  |  |  | EBoi (MOB); BD (MOB); Rio (MOB); Dro (MOB); Lil George (MOB) |  |
| JusGlo |  | Black Disciple |  |  |  | LA (MOB); Jeff (MOB) |  |
| Tadoe |  | Black Disciple |  |  |  | Killa K.I. (MOB); Ron Boi (MOB) |  |
| Max |  | Black Disciple |  |  | Stutta (M-Town); Worm (M-Town) |  |  |
| Lil Savage |  | Black Disciple |  | Y |  |  | Venzel (Tyquan World) |
| Darnell |  | Black P.Stone |  |  |  | Myro (MOB); Lil Loud (MOB); Black Boi (MOB); Tyree (MOB); Rooga (MOB); Jamo (MOB) | Lonnie (MOB) |

### DISCIPLES OF DAVID (D.O.D)

`https://privedatabase.wordpress.com/disciples-of-david-d-o-d/` · page 7917 · FCK HEAD$HOT · 2020-01-25

- **Bodies attributed to the set:** Alex (8×13), Johnny (8×13), Lil Albert (Brick$quad 069), Brett (Tay City), Christian (Tay City), Ricky (E-Block)

### DMoney

`https://privedatabase.wordpress.com/dmoney/` · page 4115 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Dart (ABM) |  |  |  |  |  |  |  |

### DOGGPOUND

`https://privedatabase.wordpress.com/doggpound-2/` · page 6537 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Black Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Based in Englewood; rapper Lil Durk, his brother D-Thang, and their cousin OTF Nuski are from this set; part of the '300' movement.

- **Bodies attributed to the set:** Fred (Wuga World), 8Ball (CMB), Pimp (Wuga World), Dave-E (Brick$quad 069), Fool (Wuga World), Boss Joc (CMB), OG Dog (Wuga World), Reginald (MBAM), D-Block (Young Morgan Mafia), Rashard (Tay City), JayLoud (CMB), Lil Kiyon (Wuga World), Gutta (CMB), Juan (Tay City), Tray (Wuga World, tué en 2018), G French (Wuga World, tué en 2019), Mat (CMB), Ward (PillzVille), Lil Chris (CMB), Nelly (PillzVille)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Lil Block |  | Black Disciple |  |  | 8Ball (CMB); Dave-E (Brick$quad 069) | Kells (Brick$quad 069); P.Rico (Brick$quad 069); Marco (CMB); Diesel (Wuga World); Lil Larry (Wuga World) |  |
| Polo Da Don |  | Black Disciple | Y |  | JayLoud (CMB) | Stain (Wuga World); Lil Mister (Wuga World); MK (Wuga World); Toocon (CMB); Lil Mike (CMB); Zay (MBAM); Killa Kenzo (Brick$quad 069) | Fool (Wuga World) |
| BJ |  | Black Disciple |  |  | OG Dog (Wuga World) | Art (CMB); Boss Doro (CMB); Josh Da Menace (CMB); Jay (CMB); Man Man (Brick$quad 069); Icey (Brick$quad 069); Lil Jojo (Brick$quad 069); Molly (Brick$quad 069); 2 Shots (Wuga World); Splash (Wuga World); Big Stix (Wuga World); Aero (051 Young Money); Tu Tu (MuBu) |  |
| Kenny Mac |  | Black Disciple |  | Y |  | Lil Mattie (CMB); Vonta (CMB); DayDay (CMB); TomTom (Wuga World); Lil Beam (Wuga World); Kells (Brick$quad 069) |  |

### DRILL CITY

`https://privedatabase.wordpress.com/drill-city/` · page 7918 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Black Disciples, Gangster Disciples
- **Allies:** _none_
- **Enemies:** _none_

- **Members listed:** Fatz MakLeakyTank Montana

- **Bodies attributed to the set:** Pac Man (Dro City), Dro (Dro City), Mello (EvansMobb), BG (EvansMobb), Justin (EvansMobb), J-Hood (EvansMobb), Bobby (EvansMobb), CoJack (EvansMobb), Tency (Whiz City), Rickey (Whiz City), Boo-G (TYMB)

### DRO CITY

`https://privedatabase.wordpress.com/dro-city-2/` · page 7971 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Gangster Disciples
- **Allies:** 051 Young Money, TYMB, NLMB
- **Enemies:** CrankTown, PocketTown, Chris World, DrillCity, MTV, 800, MixxMobb, O'Block, 600, THF 46
- **Notes:** A neighborhood made up of several Gangster Disciples sets (SnoBlock, now TPG; DBlock; RowLife; SawBlock; Roc Creek; Hood Gang); formerly called MurderTown and Ghost Town, and before that Eastside Disciples, renamed after Dro's death in 2005; part of OTF's original lineup; their rap group is MuBu (Man Up Band Up).

- **Members listed:** Obama est un Gangster Disciple. Il était proche de Krump. C'est un OG de Dro City.

- **Bodies attributed to the set:** Serge (CrankTown), — (—), — (—), ??? (???), ??? (???), ??? (???), ??? (???), ??? (???), ??? (???)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Serge (CrankTown) |  |  |  |  |  |  |  |
| Krump |  | Gangster Disciple |  |  | — (—); — (—) |  |  |
| Curt Mac |  | Gangster Disciple |  |  | ??? (???); ??? (???); ??? (???); ??? (???); ??? (???); ??? (???) |  |  |
| Big RiffPacMan (décédé)Scoot Boot (décédé)SnoBoy (décédé)Dro |  |  | Y |  |  |  |  |

### DUMPSTREET

`https://privedatabase.wordpress.com/dumpstreet-2/` · page 6479 · FCK HEAD$HOT · 2019-11-19

- **Nations:** Gangster Disciples
- **Allies:** No Luv City, Brick$quad 069, JJ Gang, CMB, Tyquan World, 50 Strong
- **Enemies:** MoeTown, FlinBoyz

- **Bodies attributed to the set:** ? (FlinBoyz), ? (FlinBoyz), ? (FlinBoyz), ? (FlinBoyz)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| JuJu |  | Gangster Disciple |  |  |  |  | Cheno (O'Block) |
| EBub | Dub | Gangster Disciple |  | Y |  | Cleo (MoeTown); Vell (MoeTown); CoKilla (MoeTown); Buddah Black (MoeTown); Trigga (MoeTown); Khalil (MoeTown) | Bobby (MoeTown); Johnny (MoeTown) |

### E-BLOCK

`https://privedatabase.wordpress.com/e-block-2/` · page 7919 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Also known as:** HadiWay
- **Allies:** STL/EBT, StonySpot
- **Enemies:** _none_
- **Notes:** Tooka and Wooski of STL/EBT originate from this set.

- **Members listed:** Duskie est un Gangster Disciple. Il est actuellement incarcéré. Il est le meilleur ami de Nello.

- **Bodies attributed to the set:** Ant (400E Murda Drive), Man Man (400E Murda Drive), China White (400E Murda Drive), Kool-Aid (400E Murda Drive), Corey (400E Murda Drive), Slip (400E Murda Drive), Lil B (BashVille), Ricky (BashVille), King Shorty (BashVille), Pillz (BashVille), Jayskiii (BashVille), PhilCo (D.O.D), Darius (EvansMobb, tué en 2019)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Jayskiii (BashVille) Hell Rell (400E Murda Drive) |  |  |  |  |  | Gee (BashVille); Wooda (BashVille); LuLu (BashVille); Lil Dirk (400E Murda Drive); Chris (400E Murda Drive); Memo (600) | HK (O'Block) |
| Nello |  | Gangster Disciple |  |  | Darius (EvansMobb, tué en 2019) | Ant (400E Murda Drive); Johnny Dang (400E Murda Drive); Spoon (400E Murda Drive); Filly (400E Murda Drive); Vono (400E Murda Drive); Burger (600); Lil Trey (BashVille); Wooda (BashVille); Lucci (BashVille); Woney Woo (O'Block); BJ (O'Block); King Dino (BuckTown); GRayski (EvansMobb) | Hell Rell (400E Murda Drive) |
| Hadi |  | Gangster Disciple | Y |  |  | Tre Savage (BashVille); JB Bin Laden (400E Murda Drive); Eli (400E Murda Drive); Nano (400E Murda Drive) |  |

### EBK Trigga

`https://privedatabase.wordpress.com/ebk-trigga/` · page 3885 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Wack (051 Young Money)Ant (051 Young Money)Roscoe (50 Strong |  |  |  |  |  |  |  |

### EVANS MOBB

`https://privedatabase.wordpress.com/evans-mobb-2/` · page 7939 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Gangster Disciples
- **Allies:** _none_
- **Enemies:** MTV, Drill City, Whiz City
- **Notes:** Based in Chatham.

- **Bodies attributed to the set:** Mal (MTV), Mac (MTV), Puncho (Drill City), Smoke (Drill City), Hulio (Whiz City), Lil Reggie (Drill City), Butta (HadiWay, tué en 2019), Solo Moe (MTV)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Hittz |  | Gangster Disciple |  |  |  |  |  |
| Bones |  | Gangster Disciple |  | Y | Butta (HadiWay, tué en 2019) |  |  |

### FACEWORLD

`https://privedatabase.wordpress.com/faceworld/` · page 7907 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Gangster Disciples, Black Disciples
- **Also known as:** Bogus Bogus
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Based in Marquette Park; rapper OTF Nuski was a member of this set.

- **Bodies attributed to the set:** Qwint (SquadVille), Ulysses (E-Spot), Corey (E-Spot), Joc (BocoHood), Baby Stone (BocoHood), Lil DeMarcus (BocoHood), Maurice (E-Spot), Roc (E-Spot), Man Man (Brick$quad 069), B-Dub (Wuga World), Richard (GunHead), Cash (Deuce Life), Marco (E-Spot), Bobby (REC City), Sam (A-Block), Flip (BocoHood), Lil MarkeyBKJ (BocoHood), DB (CMB), Steve (E-Spot), Eazy T (BocoHood), CeeJay (Brick$quad 069, tué en 2019)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Bando Bandz |  | Black Disciple | Y |  |  | Stephen (BocoHood) | JayLoud (CMB); Sam (A-Block); Lil Markey (Deuce Life) |
| Krazy Karl |  | Gangster Disciple |  | Y | Corey (E-Spot); Roc (E-Spot) |  |  |
| Cello |  | Black Disciple | Y |  | Marco (E-Spot); Steve (E-Spot) |  | Corey (E-Spot) |
| Mo Bodies |  | Black Disciple |  | Y | Sam (A-Block) |  | Cash (Deuce Life) |
| OTF NuNu ou Nuski |  | Black Disciple |  |  |  | Mike (Wuga World); Krump (MuBu) |  |

### Five Star

`https://privedatabase.wordpress.com/five-star/` · page 3801 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Dell (50 Strong)Big Meech (50 Strong) |  |  |  |  |  | Csko (50 Strong); Kiar (50 Strong); CEO (50 Strong); King Greg (50 Strong); Triggah900 (50 Strong); Rambo (No Luv City); Duke (No Luv City); Les (No Luv City); Puke (Dumpstreet); Mally (051 Young Money) | Temmo (50 Strong); Lil Marc (051 Young Money) |

### FOLLYBOYZ

`https://privedatabase.wordpress.com/follyboyz/` · page 940 · FCK HEAD$HOT · 2020-03-28

- **Members listed:** G Nate (décédé), Folly Molly (décédé), 50Shot MallBooda MoeChief DiddyCoKillaFive StarG-Nuk (décédé), KhalilBreeze (décédé), MaintainOMillieRayskoDarrenBubbaEBK TriggaFreddy MacG MoumaJ-Roc (décédé), O-DoggMoneyManScrap (décédé), SmallsYG ShortyB-Luv-It (décédé), Caddy MacZack (décédé), Lil Derrick (décédé), T-Mac (décédé), SwakaZio (décédé), Mazi (décédé), Banks (décédé), TruthBeek (décédé), Bobby (décédé), Johnny (décédé), G Tywone (décédé), Eric (décédé), Jovan (décédé), G Crane (décédé), Arthur (décédé), Jody (décédé), Uncle Vuz (décédé), Cortez (décédé), Paw Paw (décédé), VellDanny (décédé), PliesAlmighty AutoPearl (décédé), Health (décédé), Lil Greg (décédé), G DoodieFatzNickNickScaleOtto Tell WoohSuwooLil DeeKayHoolyRonni MoeArmani (décédé), Shi Money (décédé), EDogg (décédé), Jeremiah (décédé)

- **Bodies attributed to the set:** 1-4 (GGE), Earl (No Luv City), Peanut (Shields), Big Hersh (No Luv City), Wally (No Luv City), Stain (No Luv City), Glizzy (No Luv City), Temmo (50 Strong), Dell (50 Strong), Big Meech (50 Strong), Tunechi (Insane City), Shoe (No Luv City), Lafa (KTC), Bankroll Q (051 Young Money), Big Lonnie (051 Young Money), Nate (Dumpstreet), Dougo (50 Strong), Maniack (JackBoys)

### FOSTER PARK

`https://privedatabase.wordpress.com/foster-park-2/` · page 7986 · FCK HEAD$HOT · 2020-01-30

- **Nations:** Black P.Stones
- **Allies:** CrossAhland, Terror Dome, E-Spot, OTL, FollyBoyz, NateVille, Rack City, MayBlock, CuttaGang
- **Enemies:** G-Ville, SmashVille, D-Block, 8Tray, MikeCity, SDub, Fuck City, 87th Cutthroat

- **Members listed:** Reno (décédé), Deno (décédé), Lil Reno (décédé), Lil Deno (décédé), Keem (décédé), Tae (décédé), Aliyah (décédée), CeCe (décédé), Shaw (décédé), Lil Jerry (décédé), Shorty B (décédé), Donnie (décédé), Jaymo (décédé), Thugga (décédé), GdoIT (décédé), Bino (décédé), Mika (décédé), Kiev (décédé), NuNu (décédé)

### FREE SMOKE

`https://privedatabase.wordpress.com/free-smoke-2/` · page 7920 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Also known as:** BBG
- **Allies:** JigDogs, TouchMoney
- **Enemies:** 757, OBN, THF46

- **Members listed:** Durty ReddFreaky JRebelBay Bay (décédé), TuwopTankHoBoDookieDaDaMook Da Murderer (tireur actif), Ski Ski SkuddBeBe (décédé), ReskoBravoDJLil MoeAlloLil ODonteTorchGotti (décédé)

### G-Nuk

`https://privedatabase.wordpress.com/g-nuk/` · page 3802 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Tunechi (Dumpstreet)Shoe (No Luv City)Lafa (KTC) |  |  |  |  |  | Zo (Landlord COV); Boss Veze (No Luv City); Wop (No Luv City); DJ (50 Strong); Vic (Dumpstreet); Jaski (Dumpstreet); Strizzy (Dumpstreet); T Man (Dumpstreet) | Lil Doc (No Luv City) |

### G-VILLE

`https://privedatabase.wordpress.com/g-ville-2/` · page 7922 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Allies:** Terror Dome, QuietMoney TTM, SDub, BoysTown, YoungWorld, 87th Cutthroats, NuneWorld, 600
- **Enemies:** Killaward 078, SmashVille, RMG, Da Stain, Foster Park
- **Notes:** Based in Auburn Gresham.

- **Members listed:** Toon était un Gangster Disciple. Il est décédé. Il était le cousin de RondoNumba9 de la 600 et de Big Swirl du Risky Road. Il était proche de Lil Twan du même set.

- **Bodies attributed to the set:** Corey (Killaward), Lil Nate (Killaward), Antonio (Killaward), Keith (Killaward), Lil Juice (Killaward), Tae Boog (Killaward), Pat (Smashville), Ace (Killaward), Ricky (Killaward), GMoney (Killaward), Capo (Killaward), Killa (Killaward), Myrick (Smashville), E-Frank (Killaward), Tunchie (CTG), Skero (Killaward), Mello (Smashville), Rico (Killaward), BK (Killaward), Bari (Killaward), Warren (CTG), Gov (Killaward), LY (Killaward), Boss Ceejay (Killaward)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Ly (KillaWard Kutthroat 78th) |  |  |  |  |  | Sean (New Money 080); Chuck (New Money 080); King Louie (MuBu/Dro City) |  |
| Maine |  | Gangster Disciple |  | Y | BK (New Money 080 KillaWard) |  |  |
| Lil TwanDello (décédé)Gucci (décédé)Frank (décédé)Jamari (dé |  |  | Y |  |  |  |  |

### Gary Miller

`https://privedatabase.wordpress.com/gary-miller/` · page 2116 · FCK HEAD$HOT · 2020-04-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Shaq (W.B 057) |  |  |  |  |  |  |  |

### GEO DRIVE

`https://privedatabase.wordpress.com/geo-drive-2/` · page 7926 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Allies:** SKD, 051 Young Money, MOB
- **Enemies:** Front$treet, THF46, BlackGate, 600
- **Notes:** Based in Washington Park; rapper Jusblow of the 600 originates from this set.

- **Members listed:** Lil Pooh est un Gangster Disciple. Il est actuellement incarcéré pour le meurtre de «Phillip» du Roc Creek. Il a été condamné à 30 ans de prison.

- **Bodies attributed to the set:** Gymshoe (No Law), Phillip (Roc Creek), Homme du Wisconsin G-Boogie (Welch World/SK)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Gymshoe (No Law)Phillip (Roc Creek) |  |  |  |  |  |  |  |
| Mally |  | Gangster Disciple |  |  |  |  | Waldo (600) |
| Pig |  | Gangster Disciple |  |  | Homme du Wisconsin |  |  |
| Lil AntGrayskiLil RayD.O.C. (décédé)West (décédé)Lil Mike (d |  |  | Y |  |  |  |  |

### GGE

`https://privedatabase.wordpress.com/gge/` · page 944 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Black P.Stones
- **Allies:** MoeTown
- **Enemies:** _none_
- **Notes:** Wages an internal war against other sets within the MoeTown alliance.

- **Members listed:** TrelloTWhy (décédé), NuskiRelloDamianLoso (décédé), Lil Dell (décédé), Jody (décédé), Black (décédé), Dwade1-4 (décédé)

- **Bodies attributed to the set:** G Nate (FollyBoyz), Low (Dumpstreet)

### GME/EBE

`https://privedatabase.wordpress.com/gme-ebe/` · page 7903 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Titanic Stones
- **Also known as:** Roe Block
- **Allies:** NLMB, 600
- **Enemies:** KTS, Deathrow

- **Members listed:** EBE Bandz (décédé, tué en 2019), JP ArmaniMurdaLil Chief Dinero (cousin de L'A Capone de la 600), Chief MoeRoe (décédé), Shayla (décédée, sœur de Pistol), KiddoPistolBoss Kat (condamné à 50 ans), 30ShotRico (frère de Lil Chief Dinero), AlloBravoScotty (décédé), Sakinah (décédée), Donte (décédé)

- **Bodies attributed to the set:** Smith (?), Maine Chief (3 Bs)

### GOONIE GANG

`https://privedatabase.wordpress.com/goonie-gang-2/` · page 7965 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Gangster Disciples
- **Allies:** Brick$quad 069
- **Enemies:** Push Squad, TLove
- **Notes:** Subject of one of the largest investigations in recent years in Chicago, in 2018.

- **Members listed:** Turman est un Gangster Disciple. Il est actuellement incarcéré.

- **Bodies attributed to the set:** Gerald Bumper (GD), Kenneth Whittaker (?), Ramal Hicks (?), Gerald Sias (GD), Davon Horace (?), Andre Donner (?), Krystal Jackson (?), Stanley Bobo (GD), Alonzo Williams (GD), Johnathon Johnson (GD), David Easley (GD)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Kenneth Whittaker (GD)Ramal Hicks (?) |  |  |  |  |  |  |  |
| O'Dog |  | Gangster Disciple |  | Y | Gerald Sias (GD); Davon Horace (?); Andre Donner (?); Krystal Jackson (?); Stanley Bobo (GD); Alonzo Williams (GD); Johnathon Johnson (GD) |  |  |
| Christian |  | Gangster Disciple |  | Y | David Easley (GD) |  |  |

### GRIMEY GANG

`https://privedatabase.wordpress.com/grimey-gang/` · page 3718 · FCK HEAD$HOT · 2020-04-21

- **Nations:** Black Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Located on 57 South Racine.

- **Members listed:** SosaDoodieDaShooterTrigga (décédé), Zek (décédé, affilié du Grimey Gang)

### GUNHEAD

`https://privedatabase.wordpress.com/gunhead-2/` · page 7921 · FCK HEAD$HOT · 2020-01-25

- **Members listed:** Nutso

### GUTTAVILLE

`https://privedatabase.wordpress.com/guttaville-2/` · page 8002 · FCK HEAD$HOT · 2020-02-10

- **Nations:** Mickey Cobras
- **Also known as:** LexVille
- **Allies:** BlackGate, THF 46
- **Enemies:** 051 Young Money, SKD, GeoDrive, THF 44
- **Notes:** A very old set; renamed LexVille after the death of Lex.

- **Members listed:** Rio est un Mickey Cobra. Il est actuellement incarcéré. Il s'est déjà battu à plusieurs reprises contre Aero de la 051 Young Money. Ce dernier finira même par balancer Rio.

- **Bodies attributed to the set:** Geo (SKD), Cornbread (051 Young Money)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Geo (SKD) |  |  |  |  |  | Aero (051 Young Money); Aero (051 Young Money); Aero (051 Young Money) |  |
| Kevo |  | Mickey Cobra |  | Y | Cornbread (051 Young Money) |  |  |

### GUTTAVILLE GANGSTAS (GVG)

`https://privedatabase.wordpress.com/guttaville-gangstas-gvg/` · page 7955 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Renegade Gangster Disciples
- **Also known as:** DayDay World, North Pole Gangstas, Strait Heat, GuttaVille Gangstas
- **Allies:** LOC City, Lil4Mobb, IBM, SedVille
- **Enemies:** Peterson LKs, Hoola Gang, OTE, TBG, PBG/TFG
- **Notes:** Based in Edgewater; the DayDay World nickname honors deceased member DayDay.

- **Members listed:** Ahunna Stacks est un Renegade Gangster Disciple. Il est le grand frère de Gwala Mane du même set et le cousin d'Edai et Cdai de la 600.

- **Bodies attributed to the set:** 1-80-7 (Peterson LKs), MJ (Hoola Gang), Eddie (TFG), Rudolph (PBG), Julian (Peterson LKs), Karl (Peterson LKs), Dumah (Hoola Gang), AL G (PBG), Hi-C (Hoola Gang), Fetty Wop (Hoola Gang), Shad (GME/EBE), Deonte (PBG), Bo (Hoola Gang), Henno (TFG), 2Cups (TFG), Fetty (Hoola Gang), Ball (Hoola Gang)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Skool Boy (TFG) |  |  |  |  |  |  |  |
| Chelo |  | Gangster Disciple |  |  |  | Trav (TFG); Snake (TFG); Skino (TFG); MGK (Hoola Gang); Screw (Hoola Gang); Billa (THF 46); Fil (PBG); Dominic (Peterson Latin Kings) | Vell (TFG); Bo (Hoola Gang) |
| Gwala Mane |  | Gangster Disciple |  | Y |  | Gino Mac (TFG); C40 (TFG); TFG Bigz (TFG); Deshon (PBG); Boy (Peterson Latin Kings); Cane (Peterson Latin Kings); Lil Glo (Hoola Gang) | Henno (TFG) |
| Lil Duke | Young Pappy | Gangster Disciple |  |  | 2Cups (TFG) | Anthony (Peterson Latin Kings); Savage Sheen (TFG); Young Pappy (TFG/PBG); Nick (TFG); Coon (TFG); Jonho (Hoola Gang); D-Wade (Hoola Gang); Polo (Hoola Gang); BK (Hoola Gang); Lil Shawn (PBG) | Henno (TFG) |
| Mikey |  | Gangster Disciple |  |  | Fetty Wop (Hoola Gang) | Ed (Peterson Latin Kings); C40 (TFG); Dooney Mac (TFG); Nardo (TFG); Fatty (Hoola Gang); Rico (Hoola Gang); Jango (Hoola Gang); Twin (Hoola Gang) |  |
| Young Gino |  | Gangster Disciple |  |  | Henno (TFG) |  | 2Cups (TFG) |
| Del |  | Gangster Disciple |  |  |  | Polo (Hoola Gang); CashieBino (PBG) |  |
| DayDay (décédé)CEOMexicoPromoLiq Da GodBig MikeAXGutta (décé |  |  | Y |  |  |  |  |

### GUWOPGANG 075

`https://privedatabase.wordpress.com/guwopgang-075-2/` · page 7994 · FCK HEAD$HOT · 2020-02-05

- **Nations:** Black P.Stones
- **Allies:** EastEnd
- **Enemies:** _none_
- **Notes:** Repeatedly shouted out by Lil Herb (G Herbo); ShootaShellz has clashed with them over their ties to the NLMB.

- **Bodies attributed to the set:** Lil Curryio (MurdaTown, tué en 2020)

### HARVEY WORLD

`https://privedatabase.wordpress.com/harvey-world-2/` · page 7099 · FCK HEAD$HOT · 2020-02-07

- **Nations:** Black P.Stones
- **Allies:** _none_
- **Enemies:** O'Block
- **Notes:** Located in Harvey, a small suburb south of Chicago; in 2012 clashed with Chief Keef over a perceived diss against a deceased member, leading to ongoing clashes with O'Block.

- **Members listed:** Kaheem était un Black P.Stone. Il est décédé quelques semaines après avoir tué Goonie Looney.

- **Bodies attributed to the set:** Goonie Looney (No Limit 087)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Goonie Looney (No Limit 087) |  |  |  |  |  |  |  |

### HELLA BANDZ

`https://privedatabase.wordpress.com/hella-bandz-2/` · page 7947 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Gangster Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Located in West Pullman; rapper Lil Mouse was a member.

- **Members listed:** Lil Mouse est un Gangster Disciple venant du set Hella Bandz. Il continue de représenter «MBMG» et «TDG» mais après des embrouilles interne, il n'est plus en bonne entente avec les membres de son set. Il ne représente donc plus le set en lui-même et a même fait un son «Fuck Hella Bandz» avec DMoney.

- **Bodies attributed to the set:** Lil Rookie (RMG), Mono (RMG), Breezy (RMG), Mac (RMG), Ponnie (RMG), Antoine (RMG), Mari (RMG)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Remy (RMG) |  |  |  |  |  |  |  |
| Top Shatta |  | Gangster Disciple |  |  | Mari (RMG) | Remy (RMG); Big T( RMG) | Ponnie (RMG) |
| Gunna (décédé)Gutta (décédé)Ra Ra |  |  | Y |  |  |  |  |

### HOODGANG

`https://privedatabase.wordpress.com/hoodgang/` · page 1029 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Gangster Disciples, Black Disciples
- **Allies:** _none_
- **Enemies:** _none_

- **Members listed:** Lil RonBoss Malek (décédé)

- **Bodies attributed to the set:** Kenny G (ZoLand), Gusto (DDG/ZoLand)

### HOOLA GANG

`https://privedatabase.wordpress.com/hoola-gang-2/` · page 7956 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Black P.Stones
- **Also known as:** HiC City, Wicked City, BNR, BOG, A-Town Asylum, Dirt Gang, Rangers, Shower Posse, Ivy League, Kyro City
- **Allies:** StoneVilles, WW
- **Enemies:** PBG/TFG, Lil4Mobb, Uptown Lawds, GVG, Buck Town, OTE, YH, IBM, LOC City
- **Former allies:** PBG/TFG
- **Notes:** Based in Uptown; formerly merged with PBG/TFG until they killed TFG's King Shoota, since then at war.

- **Members listed:** Bigga P est un Black P.Stone. Il est actuellement incarcéré.

- **Bodies attributed to the set:** Quincy (Hazel Mobb), Lenny (Uptown Lawds), Goose (Uptown Lawds), Gutta (GVG), Jimmy (Buck Town), Peo (Uptown Lawds), Soowoo (Buck Town), Tez (Uptown Lawds), Nino (Lil4Mobb), Big Scoota (LOC City), Cortize (GVG), Frank (Uptown Lawds), Twiggie (LOC City), Jizzle (Lil4Mobb), Gucci (GVG), Teezy (Lil4Mobb), Lil Ant (Lil4Mobb), Jizzle (Lil4Mobb), King Shoota (TFG), Save (TFG), Rat G (GVG), Darius (TBG), Nino Lord (YH)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Lenny (Uptown Lawds)Goose (Uptown Lawds)Soowoo (Buck Town) |  |  |  |  |  |  |  |
| Dirt | Splash King, DirtBagg | Black P.Stone | Y |  | Nino (Lil4Mobb); Teezy (Lil4Mobb) | G-Tuck (TBG); Cody (Buck Town); TayTay (Buck Town); Sconny (Lil4Mobb); Michael (Lil4Mobb); Teezy (Lil4Mobb); Rachael (Uptown Lawds); Rat G (GVG) |  |
| Duski | Duwop, WopTote50 | Black P.Stone | Y |  | Lil Ant (Lil4Mobb) | Skuduh (LOC City); King Ty (LOC City); James (GVG); Tyrone (Lil4Mobb); D-Lo (Lil4Mobb); Sconny (Lil4Mobb); Tali (TBG); Bang Da Hitta (PBG) |  |
| Jango |  | Black P.Stone | Y |  | Cortize (GVG); Jizzle (Lil4Mobb); Save (TFG) | G-Ball (GVG); Trigga (GVG); James (GVG); Nation (Lil4Mobb); JuJu (Lil4Mobb); Michael (Lil4Mobb); Prince Shorty (Lil4Mobb); Junior (Lil4Mobb); Dinero (TBG); Lud C (TBG); Tali (TBG); Dre Day (LOC City); BuDouble (TFG); Guwop (TFG); TaySav (PBG); ShottyGoCrazy (PBG); Big Squad (PBG) | Nino (Lil4Mobb); Byro (Central City GDs); King Shoota (TFG) |
| Toolie |  | Black P.Stone |  | Y | Frank (Uptown Lawds); Gucci (GVG); Rat G (GVG) | Darcy (GVG); Ahunna Stacks (GVG); Dough (GVG); P Nickle (Buck Town); Quell (Lil4Mobb); Tune (Lil4Mobb); Lil Man (Lil4Mobb); Cole (Lil4Mobb); Link (Uptown Lawds); Terrance (Uptown Lawds); Lil Nick (TBG); Bald Head (TBG); Mice (LOC City); Kiwi (LOC City); G Deal (TFG); Ant Dog (TFG); Burt (TFG); Savage Dawgg (PBG) |  |
| Lil Bill |  | Black P.Stone |  | Y | Save (TFG) |  |  |
| 40 Cal |  | Black P.Stone | Y |  |  | CrazyEye (Buck Town); Stick (Buck Town) |  |
| Banks |  | Black P.Stone | Y |  |  | BugUp (Lil4Mobb); Lil Chros (Lil4Mobb); Lil Mook (TBG) |  |
| Blinks |  | Black P.Stone |  | Y |  | Eday (Uptown Lawds); Butta Mouse (Buck Town); Mexico (GVG) |  |
| Lil Moe |  | Black P.Stone | Y |  |  | Dre Day (LOC City); Queezy (LOC City); Lil JayJay (LOC City) |  |
| Skrilla Mac | Skrillz | Black P.Stone |  | Y | Tez (Uptown Lawds) |  |  |
| Shawn |  | Black P.Stone |  |  |  | Hot Rodd (Lil4Mobb); Tyrone (Lil4Mobb) |  |
| Trap |  | Black P.Stone |  |  |  | Meech (Lil4Mobb); Mula (Lil4Mobb); Lil Duke (GVG) |  |
| Twin |  | Black P.Stone |  |  |  | Jarious (Lil4Mobb); Lil Ant (Lil4Mobb); Quell (Lil4Mobb); Tune (Lil4Mobb); Gucci (TBG); Tevo (LOC City); KD (LOC City); Shotta Lord (TBG) | Frank (Uptown Lawds); Gucci (GVG) |
| RicoPackManTimo (décédé)Lil GloPoloBKBandoDBGotti FrescoRedd |  |  | Y |  |  |  |  |

### Inky D

`https://privedatabase.wordpress.com/inky-d/` · page 4747 · FCK HEAD$HOT · 2020-05-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Dale (STL/EBT)Derrick (Jaro City) |  |  |  |  |  | Lil Herl (Jaro City); NumbaNine (Jaro City); Dome (Jaro City); Dooski (MOB); Lil Jay (STL/EBT); Flame (STL/EBT); Kiddo (051 Young Money); Law (051 Young Money) |  |

### INSANE MONEY MOB (IMM)

`https://privedatabase.wordpress.com/insane-money-mob-imm/` · page 7923 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Insane Gangster Disciples
- **Allies:** _none_
- **Enemies:** MME
- **Notes:** IMM stands for Insane Money Mob.

- **Members listed:** Lil Jeff était un Insane Gangster Disciple. Il était aussi connu sous le nom de «Lil Jeff So Insane» ou “#99“. Il est décédé. Il était proche du rappeur Lil Jay de STL/EBT. Il était membre du groupe “FBG“.

- **Bodies attributed to the set:** Chris (MME), O (MME), D-Thang (MME), Tellz (MME), B-Boy (MME)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Chris (MME) |  |  |  |  |  | Ujean (MME); Maine (MME); Kells (MME); Wook (MME); Lil Rob (Lamron) |  |
| HittahT-DawgTripShootahDushawnRayYoung FinesseDrilla (décédé |  |  | Y |  |  |  |  |

### J-Roc

`https://privedatabase.wordpress.com/j-roc/` · page 3886 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Les (No Luv City)Jackpot (No Luv City)Famous Dex (MOE)CEO (5 |  |  |  |  |  |  |  |

### JACKBOYS

`https://privedatabase.wordpress.com/jackville/` · page 950 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Black P.Stones
- **Also known as:** LoveNone
- **Allies:** MoeTown
- **Enemies:** LOC City, WB 057
- **Former allies:** LOC City, WB 057
- **Notes:** Located at 52nd and 53rd Marshfield.

- **Members listed:** King Jay Lil LawJackBoy ScootaYungin YayJackBoy NateManiack (décédé), GMarlo (décédé), C-Murda (décédé)

- **Bodies attributed to the set:** Tae (DamenVille), Heado (LOC City), ChiefLocMoney (LOC City), Rico (LOC City), Ill Will (DamenVille), Bop D (DamenVille), Mon (LOC City), By (DamenVille)

### Jacoby

`https://privedatabase.wordpress.com/jacoby/` · page 1769 · FCK HEAD$HOT · 2020-04-10

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Gary Miller (LordsVille)Jacob (Just-Us)Kevin (Just-Us) |  |  |  |  |  |  |  |

### JARO CITY

`https://privedatabase.wordpress.com/jaro-city-2/` · page 7486 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Gangster Disciples, Black Disciples
- **Allies:** 051 Young Money, STL/EBT, Tyquan World, SuWu TTB, MOB, 757, Geo Drive, SKD
- **Enemies:** _none_
- **Notes:** Formerly known as ABM/COB before Jaro was killed; known as a set of dealers and money-makers rather than shooters despite common perception; the reason the 600 was created.

- **Bodies attributed to the set:** Dameon (TYMB), Stanley (TYMB), Marcus (TYMB), Boo (TYMB), Albert (PocketTown), Big Squirt (SquirtTown), Curt (SquirtTown), Black Boy (SquirtTown), BJ (SquirtTown), Slo-Folkz (SquirtTown), Jizzle (SquirtTown), Don (Brick City), Craig (Brick City), Alonzo (Brick City), Black Steve (Brick City), Leo (Brick City), DD (Brick City), D-Thang (600), White White (O'Block), G-Red (NLMB, tué en 2018)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| 50 Shots |  | Gangster Disciple |  | Y | DD (Brick City); Alonzo (Brick City); White White (O'Block) | Beans (Brick City); Stunna Steve (Brick City); Cord (TYMB); Young Famous (600); D-Thang (600); Stello (600); Locsta Hendrix (O'Block); Bruh Bruh (O'Block/THF 46); Bang Man (O'Block); Chief Keef (O'Block); Ronn Taylor (O'Block); Dizzle (O'Block) | Reezy (WIIIC City); Curt (SquirtTown) |
| Lil Panky |  | Black Disciple |  |  | Craig (Brick City) | Black Ty (Brick City); D-Thang (600); Deski (TYMB) |  |
| TuTu |  | Gangster Disciple | Y |  | Curt (SquirtTown); Jizzle (SquirtTown) | Mike Mane (Brick City); Cornell (Brick City); King Doda (TYMB); Dookie (TYMB); Phat B (TYMB); Mike (TYMB); Jitta (TYMB); Lil Ryan (SquirtTown) |  |
| Dome | The Muscle | Gangster Disciple |  | Y | D-Thang (600) | 600Breezy (600); AK (600) |  |
| Skinny |  | Black Disciple |  | Y | Boo (TYMB) | Tay600 (600); Lil Dee (600); Stu (O'Block); Man (O'Block); Famous (BlackGate) | HK (O'Block) |
| Torrance |  | Gangster Disciple |  |  | Black Steve (Brick City) | King Rio (SquirtTown); Jay (Brick City); Willie (WIIIC City); Odee (WIIIC City); Boobie (O'Block); Big A (O'Block); Scu (O'Block); Slick (O'Block); Big Dre (TYMB) | Curt (SquirtTown) |
| Wayne |  | Gangster Disciple |  | Y |  | Manny (TYMB); Demo (TYMB) | Tyquan (Jaro City) |
| Motor |  | Black Disciple | Y |  | Leo (Brick City) | Edai (600); BossTop (O'Block); L'A Capone (600); O'BlockKing Von (O'Block); M-Thang (600); RondoNumba9 (600); Jusblow (600); Tway (O'Block); Gleesh (O'Block); Lil Durk (Lamron) | White White (O'Block); Lil Boo (600) |
| FYB J Mane |  | Black Disciple |  |  |  | Fredo Santana (Front$treet); BJ (O'Block); RondoNumba9 (600) | G-Red (NLMB, tué en 2018) |
| FYB Mattana |  | Gangster Disciple |  |  | G-Red (NLMB, tué en 2018) |  |  |
| FYB DJ | 007 | Gangster Disciple |  |  |  | Solo (O'Block); SP (O'Block); Man-Maneski (600); Huncho Hoodo (600); BossMoo (600); Jaquan (Lamron) |  |
| Lil Darrell | Bugged Up | Gangster Disciple |  |  |  | Snika Bar (TYMB); Peevan (TYMB); DP (O'Block); Boo (O'Block); J-Money (O'Block); Jarvis (O'Block); DC (O'Block); AK (Brick City/600); M-Thang (600); BiteDown (600) | Melly (051 Young Money) |
| Lil Mike |  | Gangster Disciple |  | Y |  | Trell (TYMB); Jhari (TYMB); Cortney (TYMB); Lil Boo (600); D.Rose (600); T-Slick (Front$treet); Lil Melo (O'Block); B Way (O'Block); BooMan (Geo Drive) |  |
| JaJa | JaJa Gang | Gangster Disciple | Y |  |  |  | Curt (SquirtTown) |
| Travis |  | Gangster Disciple | Y |  |  |  | Melly (051 Young Money) |

### JARO CITY

`https://privedatabase.wordpress.com/jaro-city/` · page 243 · FCK HEAD$HOT · 2020-03-26

- **Nations:** Gangster Disciples, Black Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Formerly known as ABM/COB before Jaro was killed.

- **Members listed:** Jarvis « Jaro » Lil MikeLil DarrellDJMattanaJ ManeTuTu (décédé), Lil Panky50ShotsMotor (décédé), WayneTorranceSkinnyDomeTiger (décédé), Dalvin (décédé), Hottie (décédé), Corey (décédé), Sammy Lo (décédé), Archie (décédé), JaJa (décédé), SeanDerrick (décédé), Jeremy (décédé), Mook (décédé), BankHead (décédé), P5 (décédé), Twink (décédé), Lil Ho (décédé), GFredeo (décédé), Boobie (décédée), OJ (décédé), Tommy (décédé), Dashea (décédé), Trell (décédé), Side (décédé), Hood (décédé), Jonrynn (décédé), Lil Wood (décédé), Tyquan (décédé), Phillip (décédé), Dark (décédé), Moon Mo (décédé), Serge (décédé), Don Von (décédé), DP (décédé), Gucci 305Baby DBinkyBlocksBoo ManB-SkoCamCashCoonChadonChief TyCopoCreedDamageDanoDipLowEl RugerDukeGloWopHariJamesJoeKeionKaliffKennyKobeLil AntLil BossLil JoeLil SavageLil WorkaMarquisMaziNicoNumba9Ray Ray Reese GezzyRell RellRichy RichRockRonRonteRubySantanaSmokeyTilgoTravo (décédé)

- **Bodies attributed to the set:** Dameon (TYMB), Stanley (TYMB), Marcus (TYMB), Boo (TYMB), Albert (PocketTown), Big Squirt (SquirtTown), Curt (SquirtTown), Black Boy (SquirtTown), BJ (SquirtTown), Slo-Folkz (SquirtTown), Jizzle (SquirtTown), Don (Brick City), Craig (Brick City), Alonzo (Brick City), Black Steve (Brick City), Leo (Brick City), DD (Brick City), D-Thang (600), White White (O'Block), G-Red (NLMB)

### JIGDOGS

`https://privedatabase.wordpress.com/jigdogs-2/` · page 7934 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Allies:** FreeSmoke, TouchMoney
- **Enemies:** Dell Mob, TYB, MurdaTown
- **Notes:** Based in Bronzeville/Oakland.

- **Members listed:** JamonDamionBobDestooJoshua (décédé), BoomanMookZeusTerrell (décédé), JuicemanVon (décédé), KBLil FatzJohnny GunzBoola (décédé), JigalowDooda (décédé)

- **Bodies attributed to the set:** Derick (TYB), Darius (TYB), Sohn (Dell Mob), Jo Jo (TYB), ChrisMoe (Dell Mob), Roc (5th Ward), Zip (Dell Mob)

### Jilla

`https://privedatabase.wordpress.com/jilla/` · page 1773 · FCK HEAD$HOT · 2020-04-10

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Steveo (DamenVille)Tra'Don (LOC City BotY)GPap (LOC City Bot |  |  |  |  |  |  |  |

### Jordan

`https://privedatabase.wordpress.com/jordan/` · page 2185 · FCK HEAD$HOT · 2020-04-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Antonio McCroy |  |  |  |  |  | Michelle Whites (innocente) |  |

### Jusblow

`https://privedatabase.wordpress.com/jusblow/` · page 4748 · FCK HEAD$HOT · 2020-05-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Scrapp (MOB)Wookie (Geo Drive) |  |  |  |  |  | G-Mally (Geo Drive); G-Rayski (Geo Drive); Boo Man (Jaro City); Motor (Jaro City); Kobe (Jaro City); Ronte (Jaro City); Jyron (STL/EBT); Marly (STL/EBT); Mooche (MOB); 10Mille (MOB); Nut (MOB); Lil Shaan (MOB); Ario (051 Young Money) | Odey (E-Spot); Polo (051 Young Money); Tyriq (Bloods d'Atlanta) |

### JUST-US

`https://privedatabase.wordpress.com/just-us/` · page 951 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Black P.Stones
- **Allies:** MoeTown
- **Enemies:** _none_

- **Members listed:** Kevin (décédé), Jacob (décédé)

### KEDIZE HOMICIDE KINGS

`https://privedatabase.wordpress.com/kedize-homicide-kings-2/` · page 7998 · FCK HEAD$HOT · 2020-02-05

- **Nations:** Latin Kings
- **Allies:** _none_
- **Enemies:** RCst
- **Notes:** Located at North Pole; at war with other Latin Kings sets, notably RCst (Rosemont & Claremont).

- **Bodies attributed to the set:** KC (RCst)

### Kiar

`https://privedatabase.wordpress.com/kiar/` · page 4232 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Zack (FollyBoyz) |  |  |  |  |  |  |  |

### KILL TO SURVIVE (KTS)

`https://privedatabase.wordpress.com/kill-to-survive-kts/` · page 7491 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Gangster Disciples, Vice Lords
- **Also known as:** Kutthroat
- **Allies:** _none_
- **Enemies:** NLMB, GMEBE, 8×13, Sirconn City Gangsters, MTG, Solo City
- **Notes:** KTS is an alliance of sets including Lakeside GDs, PocketTown, and 075 Vice Lords, that itself became a set members represent.

- **Bodies attributed to the set:** Mike (8×13), Gotti (8×13), Sherm (8×13), Fearro (Sirconn City Gangster), Lil Arron (Sirconn City Gangster), Robert (Sirconn City Gangster), Drama (MTG), Daimmyon (Solo City), Big Los (NLMB), Roc (NLMB), Alamo (NLMB), Sko (NLMB), Lil Black (NLMB), G-Millz (NLMB), Marquis (NLMB), G-Bacon (NLMB), Kobe (NLMB), Magic (NLMB), Lil C (NLMB), Lil P (NLMB)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| KTS Dre |  | Gangster Disciple |  |  | Magic (NLMB, tué en 2019) | PrinceYae (Sirconn City Gangsters); VoeBama (Sirconn City Gangsters); Lil Darro (Sirconn City Gangsters); G-Bread (NLMB); Mello (NLMB); Squeak (NLMB) | Gotti (8×13); Big Los (NLMB); Alamo (NLMB) |
| KTS Von aussi connu sous le nom de « Big Kutthroat Da Smoker | Big Kutthroat Da Smoker | Gangster Disciple | Y |  | Gotti (8×13); Roc (NLMB); Alamo (NLMB); Big Los (NLMB); Fearro (Sirconn City Gangsters); Kobe (NLMB) | Pistol P (NLMB); WetEmUp (NLMB); G-Herbo (NLMB); Larro (NLMB); Choppa (NLMB); Flocka (NLMB); TA (FaceWorld); Billa (THF 46); Devo Capone (MTV); Gutta (Hitzsquad); Dee (8×13); Santana (8×13); Trale (Sirconn City Gangsters); Day Day (Sirconn City Gangsters); Mally (NLMB) | Lil Arron (Sirconn City Gangsters) |
| Murda Migo |  | Vice Lord |  | Y | Mike(8×13) |  |  |
| Nello |  | Vice Lord |  | Y | Sherm (8×13) |  |  |
| Rio G |  | Vice Lord |  |  |  | EBK Juvie (NLMB); White Shawn (NLMB); Lil Bruce (NLMB); King Ze (Sirconn City Gangsters); Tre (Sirconn City Gangsters); Gucc (Sirconn City Gangsters); Jody Boi (Sirconn City Gangsters) |  |
| Vinnie |  | Gangster Disciple |  | Y | Lil Arron (Sirconn City Gangsters) | Lil Billy (Sirconn City Gangsters); Man Man (Sirconn City Gangsters); Montana (Sirconn City Gangsters); Drizzle (Sirconn City Gangsters); Crazy James (NLMB); Key (NLMB) | Big Los (NLMB); Fearro (Sirconn City Gangsters) |
| Meechie |  | Vice Lord |  |  | G-Millz (NLMB); Lil C (NLMB); Lil P (NLMB) |  |  |

### KILLAWARD 078

`https://privedatabase.wordpress.com/killaward-078/` · page 7894 · FCK HEAD$HOT · 2019-11-19

- **Nations:** Gangster Disciples
- **Allies:** ABM, REC City, PocketTown (YKN), FlipSide, SmashVille, 9-0, RMG (YKN)
- **Enemies:** G-Ville, Terror Dome, QuietMoney, FaceWorld, MayBlock, D-Town, Foster Park, RMG, CTG, Out7aw City
- **Notes:** Killaward is represented by several mutually warring sets including New Money and 75th; one of the first Gangster Disciples sets to feud internally; rappers King Von, Lil $hawn, King Samson, and Loskiii are from this set; formerly called 'Ward', renamed 'KillaWard' in honor of Killa (aka Lil Will), killed in the BBG Terror Dome neighborhood.

- **Bodies attributed to the set:** Joseph (Terror Dome), Loreal (Terror Dome), Vaughn (Terror Dome), Jamal (Terror Dome), T-Time (Terror Dome), Lil Moe (Terror Dome), JayMoe (Terror Dome), Lil Deno (Terror Dome), Curtis (Terror Dome), Nut (Terror Dome), BigHeadHuncho (Terror Dome), Gucci (G-Ville), Frank (G-Ville), Dello (G-Ville), Jamari (G-Ville), Toon (G-Ville, cousin de RondoNumba9 et Big Swirl), Dantario (G-Ville), Robert (G-Ville), Rio (G-Ville), Lil Sid (G-Ville), C-Note (G-Ville), Trell (G-Ville), Brian (G-Ville), Taco (Out7aw City), Los (Out7aw City), Jack (Out7aw City), TimMoe (Quiet Money), K.O. (Quiet Money), Philon (Quiet Money), Tece (Killaward), Bryan (G-Ville, tué en 2019), Nuk (SmashVille), Twilla (SmashVille), BJ (SmashVille), Sinbad (SmashVille), Lil Money (KillaWard YKN 078), Lil C (KillaWard YKN 078), Donald (KillaWard YKN 078), Swerv (New Money 080), ? (New Money 080, en 2008)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Quietmoney, faceworld, terrordome, mayblock(old), Gville, No |  |  |  |  |  |  |  |
| YK |  | Gangster Disciple |  | Y | T-Time (Terror Dome) | Mère de T-Time |  |
| Lil Will |  | Gangster Disciple | Y |  | ? (Black P.Stones); ? (Black P.Stones); ? (Black P.Stones); ? (Black P.Stones); ? (Black P.Stones) |  |  |
| Juice |  | Gangster Disciple |  |  |  |  |  |
| Juiceman |  | Gangster Disciple | Y |  | Black Moe (New Money 080/BBG Terror Dome) |  |  |
| Squash |  | Gangster Disciple |  |  |  |  | Black Moe (New Money 080/Terror Dome) |
| Lil Josh |  | Gangster Disciple |  | Y | JayMoe (BBG Terror Dome) |  |  |
| Sean |  | Gangster Disciple |  |  | Dell (G-Ville); Corn (G-Ville); ??? (QuietMoney); ??? (QuietMoney) |  |  |
| Thermo |  | Gangster Disciple |  |  | Gucci (G-Ville) |  | Dell (G-Ville); Corn (G-Ville) |
| Money |  | Gangster Disciple | Y |  |  |  | Gucci (G-Ville) |
| JD Hotter |  | Gangster Disciple |  |  | Bari (G-Ville) |  |  |
| Swerv |  | Gangster Disciple | Y |  | Lil Money (KillaWard YKN 078) | Lil Twan (dans les jambes, G-Ville) |  |
| StrechRamboGottiLooneyKingTallCelloKing ShawnEALoskiiO-DoggB |  |  | Y |  |  |  |  |

### King Greg

`https://privedatabase.wordpress.com/king-greg/` · page 4233 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Lil Derrick (FollyBoyz)Molly (FollyBoyz) |  |  |  |  |  | Truth (FollyBoyz); Chief Diddy (FollyBoyz); Five Star (FollyBoyz); Scale (FollyBoyz); EDogg (FollyBoyz); Maintain (FollyBoyz); Deega (FollyBoyz); Goonie Looney (No Limit 087); Money Man (TYMB); D.Rose (600) | Scrap (FollyBoyz) |

### KTC

`https://privedatabase.wordpress.com/ktc/` · page 943 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Black P.Stones
- **Allies:** MoeTown
- **Enemies:** _none_

- **Members listed:** Lafa (décédé)

- **Bodies attributed to the set:** G-Nuk (FollyBoyz)

### LAKESIDE

`https://privedatabase.wordpress.com/lakeside-2/` · page 7952 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Gangster Disciples
- **Allies:** _none_
- **Enemies:** NLMB
- **Notes:** Based in South Chicago.

- **Members listed:** Posto était un Gangster Disciple. Il est décédé. En son hommage, le Lakeside le représente sous le nom “Posto Gang“. Il était le grand frère de Dezz du même set.

- **Bodies attributed to the set:** Lawrence (NLMB), Vanity (NLMB), Corey (NLMB), Dev (NLMB), Fazo (NLMB), Chico (NLMB), WhiteFolkz (NLMB), BabyCrack (NLMB), Guwop (NLMB), Loso (NLMB), Copo (NLMB)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Kobe (NLMB) |  |  |  |  |  | J. Dot (NLMB); Lil Bibby (NLMB); Moodie (NLMB); G-Bread (NLMB) |  |
| Dezz |  | Gangster Disciple |  |  |  |  | Copo (NLMB) |
| Lil Ty |  | Gangster Disciple |  |  | Copo (NLMB) |  |  |
| Romael |  | Gangster Disciple |  | Y | Vanity (NLMB); Corey (NLMB) |  | Lawrence (NLMB) |
| Shannon |  | Gangster Disciple |  | Y | Lawrence (NLMB) |  | Vanity (NLMB); Corey (NLMB) |
| Royal Baybee |  | Gangster Disciple |  |  |  |  | MaddMaxx (NLMB) |
| Birdy MontanaBoomainD-BlackKing PoochieLoLo (décédé)SnookT-B |  |  | Y | Y |  |  |  |

### LAMRON

`https://privedatabase.wordpress.com/lamron-2/` · page 7489 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Black Disciples
- **Allies:** TTE, P-Streets, O'Block, 600, Central City, MoeTown
- **Enemies:** No Luv City, Shields, Brick$quad 069, CMB, Wuga World
- **Notes:** A very old set, now money-focused; rappers Lil Durk and Lil Reese represent Lamron; part of the '300' movement; shot at the funeral of James from M-Town.

- **Bodies attributed to the set:** Andre (No Luv City), Delmont (No Luv City), Thomas (No Luv City), Isaac (No Luv City), Chello (No Luv City), Lil Ron (No Luv City), Al G Mac (No Luv City), Lil Ricky (No Luv City), Cleo (No Luv City), Billie (No Luv City), Chuck (No Luv City), Fred (No Luv City), G Money (No Luv City), Jataris (No Luv City), King Bam (No Luv City), Willie (Shields), David (Shields), Rodrick (Shields), Nunu (Shields), Mannie (Shields), Marshall (Shields), Kenny (Shields), Travis (Shields), Darryl (Shields), Shay (Shields), Shawn (Shields), Baby Stone (Tay City), Thomas (Brick$quad 069)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Big Murda |  | Black Disciple |  |  | Willie (Shields); Mannie (Shields) |  |  |
| 300OJ |  | Black Disciple |  |  | Thomas (Brick$quad 069) | Freaky (Brick$quad 069); Robino (Brick$quad 069); EBub (Dumpstreet); Quinny Mac (No Luv City); NewMoney (051 Young Money) |  |
| Boona |  | Black Disciple |  |  | Chello (No Luv City); Marshall (Shields) |  |  |
| Boonie Moe |  | Black P.Stone |  |  | Lil Ron (No Luv City) |  |  |
| Buddha |  | Black Disciple | Y |  | Andre (No Luv City); David (Shields) |  |  |
| Day Day |  | Black Disciple |  |  | Kenny (Shields); Fred (No Luv City) | Blake (No Luv City); Glizzy (No Luv City); Tay (No Luv City); Izzy (No Luv City); Alo (Shields); Joe P (Shields); Twan (Shields); Dez (Brick$quad 069); Dell Gotti (Brick$quad 069); T-Lowe (051 Young Money) | Billie (No Luv City) |
| DeDe |  | Black Disciple |  | Y | Billie (No Luv City) | Meechie (Shields); Zae Zae (Shields); Ray Bands (No Luv City); Gino Louchie (No Luv City); Martavius (No Luv City); Blake (No Luv City); Jeezy (No Luv City); P.Rico (Brick$quad 069); Melly (051 Young Money); James (051 Young Money); Chop (051 Young Money) | Kenny (Shields); Fred (No Luv City) |
| Jam |  | Black Disciple |  | Y | Al G Mac (No Luv City) |  |  |
| JL300 aussi connu sous le nom de «Jesse Law» | Jesse Law | Black Disciple |  |  | Travis (Shields) | Glizzy (No Luv City); Denis (No Luv City); Zo (No Luv City); J-Roc (Shields); BDK Kevo (Brick$quad069); Boss Tony (Brick$quad069); Raymo (Brick$quad069); Kiddo Da Drilla (051 Young Money) |  |
| Keke |  | Black Disciple |  |  | Lil Ricky (No Luv City) |  | Lil Jojo (Brick$quad 069) |
| Lil Law |  | Black Disciple | Y | Y | Delmont (No Luv City); Thomas (No Luv City) |  |  |
| Pluto | Lil Pat | Black Disciple | Y |  | Spizzle (Shields); Cleo (No Luv City) |  |  |
| Twin |  | Black Disciple |  |  | G Money (No Luv City) | Les (No Luv City); Tone Bone (No Luv City); Lil Ant (No Luv City); Chuck (No Luv City); Boss Jay (No Luv City); Antoine (Shields); King Dre (Brick$quad 069); $wagg Dinero (Brick$quad 069); Tay Savage (Welch World); Aero (051 Young Money); Remy (051 Young Money); Montana (051 Young Money); Melly (051 Young Money) | Thomas (Brick$quad 069) |
| Water |  | Black Disciple |  |  | Freaky (No Luv City) | D Money (No Luv City); Ray Bands (No Luv City); Israel (No Luv City); Zo (No Luv City); Teeski (No Luv City); Izzy (No Luv City); KT Rasta (No Luv City); Alo (Shields); El Chopo (Shields); Teroe (Shields) |  |
| J-Macc | Lil Jojo | Black Disciple |  |  |  | D Money (No Luv City); YoYo (Brick$quad 069) | Lil Don (Brick$quad 069) |
| Lil Reese |  | Black Disciple |  |  |  | Rozay (No Luv City); Trin G (No Luv City); Earl (No Luv City); Rambo (No Luv City); Darnell (No Luv City); Lil Jojo (Brick$quad 069); Lil Marc (051 Young Money) | Thomas (No Luv City) |
| Beski |  | Black Disciple |  |  |  |  | Marshall (Shields); Cleo (No Luv City) |
| FatBoyChubbz |  | Black Disciple |  |  |  | Melly (051 Young Money); Woo (051 Young Money); Andrilla (051 Young Money); P.Rico (Brick$quad 069) |  |
| Lil Durk | Durkiooooooooo | Black Disciple |  |  |  | Emmanuel (No Luv City); Ball Hard (No Luv City) |  |
| Ballout |  | Black Disciple |  |  |  |  |  |

### LANDLORD COV

`https://privedatabase.wordpress.com/landlord-cov/` · page 972 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Gangster Disciples
- **Allies:** No Luv City
- **Enemies:** _none_

- **Members listed:** ZoRay BandsDenisCello (décédé), Jack PotBig Hersh (décédé), Doc (décédé)

- **Bodies attributed to the set:** Jimmy (FuckTown), Bobby (FollyBoyz), Johnny (FollyBoyz), Jeremiah (FollyBoyz), EDogg (FollyBoyz), Shi Money (FollyBoyz), J-Roc (FollyBoyz)

### LEXIQUE

- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** This is a glossary entry defining the term BACKDOOR (luring an ally or enemy through a door to kill them), popularized in Chicago after the death of Melly 051, not a set biography.

### Lil Dee

`https://privedatabase.wordpress.com/lil-dee-2/` · page 4749 · FCK HEAD$HOT · 2020-05-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| James (M-Town)Scrapp (MOB) |  |  |  |  |  | Mikie (MOB); Dooski (MOB); Lil Scrapp (MOB); FBG Youny (STL/EBT); Rico (STL/EBT); Wooski (STL/EBT); Duskie (E-Block); Rock (Jaro City); TTB Nez (SuWu TTB) |  |

### Lil Zo

`https://privedatabase.wordpress.com/lil-zo/` · page 1770 · FCK HEAD$HOT · 2020-04-10

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Sugar Ray (LordsVille) |  |  |  |  |  |  |  |

### LIL4MOBB

`https://privedatabase.wordpress.com/lil4mobb-2/` · page 7957 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Conservative Vice Lords, 4 Corner Hustlers
- **Also known as:** Hazel Mobb, A.B.M
- **Allies:** TBG, YH, GVG, LOC City, CPL, SedVille
- **Enemies:** PBG/TFG, Hoola Gang, D-Town, SK, LDubb GDs
- **Notes:** Based in Uptown; renamed after Lil 4 was killed; known for killing rapper Young Pappy.

- **Members listed:** BaeBae est un 4 Corner Hustler.

- **Bodies attributed to the set:** Ivy (HoolaGang), Wicked (HoolaGang), Dwayne B (Hoola Gang), CB (TFG), Khaos (HoolaGang), Kano (LDubb GDs), A-Town (HoolaGang), HiC (HoolaGang), Re (LDubb GDs), Jamarrion (LDubb GDs), Mark (HoolaGang), Chucky (TFG), Charlie (PBG), Tony (LDubb GDs), Gino (LDubb GDs), Fee-Mack (TFG), Dan (HoolaGang), Rancho (D-Town), Big Baby (HoolaGang), Sco (TFG), ManMan (LDubb GDs), Carlos (TFG), Kyro (HoolaGang), Lil Troy (TFG), Neezy (PBG), Big Red (TFG), Young Pappy (TFG), Dirt (Hoola Gang), KD (Hoola Gang), Fatty (Hoola Gang), Banks (Hoola Gang), .40 Cal (Hoola Gang), A-Town (Hoola Gang), DonDon (Hoola Gang)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Dan (HoolaGang)Sco (TFG) |  |  |  |  |  |  |  |
| Lil Sam | Sammy Sosa |  |  |  | KD (Hoola Gang) | Byrna (Hoola Gang); B Sconey (Hoola Gang); Jango (Hoola Gang); King Shoota (TFG); Lil Roger (TFG); G Deal (TFG); Henry (L Dubb GDs); Jam (L Dubb GDs); Hino (L Dubb GDs) | Big Red (TFG); Fatty (Hoola Gang) |
| Meech | TruFoe |  |  |  | Gino (LDubb GDs) | Tony (L Dubb GDs); Dan (Hoola Gang); Kyro (Hoola Gang) |  |
| Nation |  |  |  | Y | Jamarrio (LDubb GDs); Fee Mack (TFG); Neezy (PBG) |  |  |
| Teezy |  |  |  |  |  | Twin (Hoola Gang); EastSide (Hoola Gang); Dirt (Hoola Gang); PBG Kemo (PBG); Dmacc (PBG); Skino (TFG) |  |
| Cole |  |  |  |  |  | Uncle Murda (Hoola Gang) |  |
| Lil 4 (décédé)Young DoloEJ (décédé)DKZay TiggyMysean (décédé |  |  | Y |  |  |  |  |

### LOC CITY

`https://privedatabase.wordpress.com/loc-city-2/` · page 7954 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Gangster Disciples, Black Disciples
- **Also known as:** 1212, MMG, Jeffery Boyz, Get Rich, Blake Block, Montana Gang, Keno World, Munchie Gang, Lawless
- **Allies:** IBM, GVG, Lil4Mobb, TBG
- **Enemies:** PBG/TFG, SouthEnd, TaeTown, Hoola Gang, OTE, ABM
- **Former allies:** ICG
- **Notes:** LOC stands for Loyalty Over Cash; based in Rogers Park.

- **Members listed:** BA est un Gangster Disciple.

- **Bodies attributed to the set:** Bird (GVG), Meech (GVG), Freaky (ICG), Clive (ICG), Tae (South End), Pooh Bear (ICG), Edward (PBG), Eazy (TFG), JB (PBG), JamRock (TaeTown), Tim (TFG), Aquan (TaeTown), Harlem (StoneVille), Deonte (PBG), Tony (ABM), Lil Greg (ABM), Keyo (PBG), Pep (PBG), Bo (TaeTown), Lil Moe (Hoola Gang), Mac Duece (Hoola Gang), Cmac (Hoola Gang), Timo (Hoola Gang), Mosey (PBG), Midnite (TFG), $avage (TFG), Too Eazy (TFG), Lil Ace (TaeTown), Tank (CAst)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| JB (PBG)Tim (TFG)Bo (TaeTown) |  |  |  |  |  | Dummy Dixon (TaeTown); Wilson (TaeTown); Head (TaeTown); China Badazz (PBG); Derv (PBG); DenDen (PBG); TaySav (PBG); ShottyGoCrazy (PBG); Mook (TFG); Twin (Hoola Gang); Jango (Hoola Gang); CB (TFG); Lil Vell (OTE) | Dirt (Hoola Gang) |
| Bad Luck |  | Gangster Disciple |  | Y | Edward (PBG); Harlem (StoneVille); Cmac (Hoola Gang) | E Dirty (StoneVille); Big Moe (StoneVille); DenDen (PBG); E.O. (PBG); Magic City (PBG); Face (PBG); Blood Raw (PBG); Junior (PBG); Stuckey (PBG); G Maxxo (PBG); Skrilla Mac (Hoola Gang); PeeJay (Hoola Gang); Toolie (Hoola Gang); Nathan (Hoola Gang); Twin (Hoola Gang); Rico (Hoola Gang); Bigga P (Hoola Gang); Lil Glo (Hoola Gang); Jumananee (ABM); Lil Moe (ABM); Javon (ABM); Tony (ABM); Mitch (TaeTown); Fat Dude (TaeTown); Wilson (TaeTown); Spud (TFG); Foolie (TFG); BuDouble (TFG); Shorty Long (TFG) | JB (PBG); Pep (PBG); Eazy (TFG); Timo (Hoola Gang) |
| DB aussi connu sous le nom de «Derry» | Derry | Gangster Disciple |  | Y | Lil Greg (ABM) | Bino (PBG); PBG Spazz (PBG); TaySav (PBG); Jaey Peso (TaeTown); Veli (TaeTown); D-Wade (Hoola Gang); Cashie (Hoola Gang); Twin (Hoola Gang); Fatty (Hoola Gang); Savage Sheen (TFG); Bookie (TFG) | Tony (ABM) |
| King Ty |  | Black Disciple |  |  | Keyo (PBG); Midnite (TFG); Timo (Hoola Gang) | Jaye Peso (TaeTown); Lil Ace (TaeTown); Jin (TaeTown); Cortez (TaeTown); Devo (TaeTown); Fat Dude (TaeTown); Lucci Menace (PBG); Lil $hawn (PBG); Noodle (PBG); Mark (PBG); PBG Kemo (PBG); Big Squad (PBG); BuDouble (TFG); Young Pappy (PBG/TFG); Timo (Hoola Gang); PeeJay (Hoola Gang) | Tae (TaeTown) |
| Skuduh |  | Gangster Disciple |  | Y | Mosey (PBG); Lil Ace (TaeTown) | Lennie (PBG); Fredo (PBG); TaySav (PBG); Pipp (PBG); Kellz (TaeTown); Lil 4 (TaeTown); Rondo (TaeTown); Mooski (TaeTown); Toolie (Hoola Gang); Ace (TFG); Bookie (TFG) |  |
| Munchie |  | Gangster Disciple | Y |  | JamRock (TaeTown); Pooh Bear (ICG); JB (PBG) | Too Tall (TaeTown); Daddy-O (PBG); Hothead (PBG); Lil Dutty (PBG); ShottyGoCrazy (PBG); PBG Spazz (PBG); Osama (ABM); Young Pappy (PBG/TFG); Dooney Mac (TFG); Fatty (Hoola Gang) | Keyo (PBG) |
| Lil JayJay |  | Gangster Disciple |  |  | Lil Moe (Hoola Gang); $avage (TFG) | Lil DJ (PBG); MK (PBG); Straight Drop (PBG); Muke (PBG); Lennie (PBG); Pipp (PBG); Lil John (PBG) | Mosey (PBG) |
| Tylo |  | Gangster Disciple |  |  |  | Bud Dub (PBG); Jonell (ABM); Bo (TaeTown); Dontreal (TaeTown); Skino (TFG); King Shoota (TFG); G Deal (TFG); Crystal (Hoola Gang, femme) | CMac (Hoola Gang); Midnite (TFG) |
| G Pops |  | Gangster Disciple |  |  |  |  | Freaky (ICG) |
| Mice | MurdaMan | Gangster Disciple |  |  | Tae (South End) | MoneyMan (TaeTown); Gucci (TaeTown); Wop (TaeTown); Bino (PBG); PBG Spazz (PBG); Diddy (PBG); Ant Dog (TFG); Shawn (Hoola Gang); EastSide (Hoola Gang) | Harlem (StoneVille) |
| Kejuan |  | Gangster Disciple |  |  | Mac Duece (Hoola Gang) |  |  |
| Baby |  | Black Disciple |  |  |  | Diddy (PBG); DMacc (PBG); Mosey (PBG); Quinny (PBG); Johno (Hoola Gang); Cashie (Hoola Gang); Savage Sheen (TFG); Huncho (ABM) |  |
| Deshinni |  | Gangster Disciple |  | Y |  | Moolah (Hoola Gang); DB (Hoola Gang); Gino Mac (TFG); Muke (PBG); Fahiem (PBG); Deshon (PBG); Jin (TaeTown) | JamRock (TaeTown) |
| Dre Day | Lil Dre | Black Disciple |  |  |  | PBG Spazz (PBG); Shockey (PBG); TaySav (PBG) |  |
| Ice Man |  | Gangster Disciple |  | Y |  | Tucci (PBG); EastSide (Hoola Gang) |  |
| Mondo |  | Gangster Disciple |  | Y |  | Stuckey (PBG); Neezy (PBG); Lil $hawn (PBG); TFG Bigz (TFG); Young Pappy (PBG/TFG); Justo (Hoola Gang); ShortyFoe (ABM) |  |
| Rocket |  | Gangster Disciple | Y |  |  | Tae (SouthEnd); Piff (ABM); Marshawn (ABM) |  |
| SlammaBlake (décédé)Keno (décédé)V12 (décédé)KenBenAJ (décéd |  |  | Y |  |  |  |  |

### LOC CITY (BotY)

`https://privedatabase.wordpress.com/loc-city-boty/` · page 450 · FCK HEAD$HOT · 2020-03-27

- **Nations:** Gangster Disciples
- **Allies:** DamenVille, W.B 057
- **Enemies:** _none_
- **Notes:** Not to be confused with the LOC City in North Chicago.

- **Members listed:** GlockBoy BoBoGlockBoy KOGPap (décédé), Heado (décédé), ChiefLocMoney (décédé), Rico (décédé), Mon (décédé), Tra'Don (décédé)

### LOC CITY (BotY)

`https://privedatabase.wordpress.com/loc-city-boty-2/` · page 7991 · FCK HEAD$HOT · 2020-02-01

- **Nations:** Gangster Disciples
- **Allies:** DamenVille, ArtGang, PocketBoyz
- **Enemies:** Justine (MoeTown), MurdaField (MoeTown), LordsVille, JackBoys (MoeTown)
- **Notes:** Not to be confused with the LOC City from North Pole; mostly BDK.

- **Bodies attributed to the set:** Tyto (LordsVille), C-Murda (JackBoys), AJ (JackBoys), Kevin (Jackboys, tué en 2019), Jacob (Jackboys, tué en 2019)

### LORDSVILLE

`https://privedatabase.wordpress.com/lordsville/` · page 1790 · FCK HEAD$HOT · 2020-04-10

- **Nations:** Insane Vice Lords
- **Also known as:** HoyneBoyz
- **Allies:** _none_
- **Enemies:** DamenVille, LOC City, W.B 057
- **Notes:** Long-running war against DamenVille, LOC City and W.B 057.

- **Members listed:** Sugar Ray (décédé), Gary Miller (décédé)

- **Bodies attributed to the set:** Shaq (W.B 057)

### LOWELIFE

`https://privedatabase.wordpress.com/lowelife-2/` · page 7944 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Black Disciples
- **Allies:** _none_
- **Enemies:** AMG, Brick$quad 069, BlockBurna, CMB, Wuga World
- **Former allies:** AMG
- **Notes:** Based in Englewood; part of the '300' movement; went to war with former ally AMG in 2017.

- **Members listed:** Deyski, aussi connu sous le nom «OffHisAss» était un Black Disciple. Il est décédé.

- **Bodies attributed to the set:** Michael (BlockBurna), Zoe (Brick$quad 069), Darnell (Brick$quad 069), Corey (CMB), Arthur (Wuga World), Wale (CMB), Oochie (CMB), JJ (BlockBurna), Nose (CMB), Keylow (CMB), StunnaMan (CMB), Husi (Brick$quad 069), Trap (Brick$quad 069), G-Freak (AMG), Von (AMG), Lil Don (Brick$quad 069, tué en 2019), Savo (AMG, tué en 2019)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Oochie (CMB)JJ (BlockBurna) |  |  |  |  |  | Boss Doro (CMB); Marco (CMB); Dia (CMB); Lil Heavy (CMB); DayDay (CMB); Freaky (Brick$quad 069); Moosalina (Brick$quad 069) | Wale (CMB); BayBay (MOB) |
| Harvey |  | Black Disciple |  |  |  |  | JayLoud (CMB) |
| Lil D |  | Black Disciple |  |  |  | Josh Da Menace (CMB); Boos Eight (CMB) |  |
| Lil T |  | Black Disciple |  |  | StunnaMan (CMB); Trap (Brick$quad 069) | Darnell (CMB); Molly (Brick$quad 069); Osama (Brick$quad 069); T Streetz (Brick$quad 069); Lil Don (Brick$quad 069); Dreski (AMG) | Husi (Brick$quad 069) |
| LoweKo |  | Black Disciple |  |  | Keylow (CMB, beau père de Lil Bubba du Tyquan World) | Vonta (CMB); Toocon (CMB); Jay (CMB); Dell Gotti (Brick$quad 069); Killa Kellz (Brick$quad 069); Boss Tony (Brick$quad 069) |  |
| Tae Shoota |  | Black Disciple |  | Y | Arthur (Wuga World); Wale (CMB) | Reese (CMB); Boos AJ (CMB); Elliot (CMB); Marco (CMB); P.Rico (Brick$quad 069) | Keylow (CMB) |
| Taedoe |  | Black Disciple | Y |  | Nose (CMB); Husi (Brick$quad 069) | Bam Bam (Brick$quad 069); King Dre (Brick$quad 069); YoYo (Brick$quad 069); Eski (CMB); Darnell (CMB) | StunnaMan (CMB) |
| Ikey |  | Black Disciple |  |  |  |  | Lil Don (Brick$quad 069) |
| Thirty |  | Black Disciple |  |  | Lil Don (Brick$quad 069) |  |  |
| Lil John |  | Black Disciple |  |  |  | Reggie Baybee (CMB) |  |
| MontanaEtho (décédé)Uh-Uh (décédé)J-Mann (décédé)Quenton (dé |  |  | Y |  |  |  |  |

### M.O.M

- **Nations:** Gangster Disciples
- **Allies:** No Luv City
- **Enemies:** _none_

### Maintain

`https://privedatabase.wordpress.com/maintain/` · page 3877 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Big Meech (50 Strong) |  |  |  |  |  | Boss Bully (50 Strong); Big Squad (50 Strong); JD (50 Strong); Rambo (No Luv City); Nino (No Luv City); Ball Hard (No Luv City); Boss Jay (No Luv City); Aero (051 Young Money) |  |

### Makado

`https://privedatabase.wordpress.com/makado/` · page 4752 · FCK HEAD$HOT · 2020-05-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Washington (Innocente)Dowell (Innocente) |  |  |  |  |  | Beans (MOB); 10Mille (MOB); Lil Scrapp (MOB); Lil Loud (MOB); Jiale (STL/EBT); Brick (STL/EBT); CantGetRight (STL/EBT); Hari (Jaro City); Kobe (Jaro City); Po Lo (800); Dro (Tyquan World); Woo (051 Young Money) | Jamo (MOB); Brick (STL/EBT); Coby (STL/EBT); TB (Tyquan World) |

### ManyNames

`https://privedatabase.wordpress.com/manynames/` · page 4242 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| JayG (FollyBoyz)J-Roc (FollyBoyz)Fatz (FollyBoyz) |  |  |  |  |  |  |  |

### Marlon

`https://privedatabase.wordpress.com/marlon/` · page 4147 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Tayski (Lamron) |  |  |  |  |  |  |  |

### MARSHALL FIELD MCs

`https://privedatabase.wordpress.com/marshall-field-mcs-2/` · page 7959 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Mickey Cobras
- **Also known as:** FTE
- **Allies:** Sedville
- **Enemies:** OTE, Sac Boyz
- **Notes:** Based in Near North Side.

- **Members listed:** Lance (décédé), Mookie (décédé), Funcky (décédé), Diddy (décédé), Jamal (décédé), Meji (décédé), Patrick (décédé)

- **Bodies attributed to the set:** 50 (OTE), Troy (OTE), Tunechi (OTE), Head (OTE)

### MET BOYZ

`https://privedatabase.wordpress.com/met-boyz-2/` · page 7936 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Allies:** 051 Young Money, SKD
- **Enemies:** _none_
- **Notes:** Based in Washington Park; formed in the 2000s as '051 Met Boyz' from the merger of Met Boyz and 051, once the most powerful alliance in South Chicago.

- **Members listed:** Meiko est un Gangster Disciple. Il est actuellement incarcéré pour avoir participé au meurtre de L'A Capone de la 600.

- **Bodies attributed to the set:** Mike (BlackGate), Phil (BlackGate), 40 (GuttaVille), Ghost (DukeSquad)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| L'A Capone (600) |  |  |  |  |  |  |  |
| BenzWon Won (décédé)Geanni (décédé)Lil KennyMarco (décédé)Re |  |  | Y |  |  |  |  |

### MITCH BLOCK

`https://privedatabase.wordpress.com/mitch-block-2/` · page 7938 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Gangster Disciples, Black Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Former allies:** STL/EBT
- **Notes:** Based in the Wild 100's; fell out with STL/EBT and rapper Lil Jay after an extortion attempt, which led to Lil Jay and FBG Butta's imprisonment.

- **Members listed:** Lil LawJ Da KiddBoss MUncle MollyRYUKelz (décédé), KCMontrey (décédé), AaronJOMitch (décédé), Shawn (décédé), ReeseDopeBoiJizzle (décédé)

- **Bodies attributed to the set:** Filmon (RNM)

### MIXX MOBB

`https://privedatabase.wordpress.com/mixx-mobb-2/` · page 7940 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Gangster Disciples, Black Disciples
- **Allies:** _none_
- **Enemies:** Whiz City, MTV, TYMB
- **Notes:** Based in Chatham.

- **Members listed:** Lil De'Seann était un Gangster Disciple. Il est décédé. Il était proche de Poppie et TB du Tyquan World. Il est tué par la police, ces derniers ont dit que De'Seann avait pointé une arme vers eux mais d'après les témoins, il n'avait aucune arme. Le jour où il est tué par la police, il a une bagarre le matin dans un bus avec un ennemi à lui, il tue Millie du Whiz City et ensuite il se fera tuer par un policier à côté du corps de Millie.

- **Bodies attributed to the set:** Gleen Mac (Whiz City), Millie (Whiz City), Steff (MTV), Lowe (Whiz City), Suey (TYMB), TJ (Whiz City), Dontay (GMEBE), Sakinah (GMEBE), Jatoine (MOB, tué en 2018)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Steff (MTV)Millie (Whiz City) |  |  |  |  |  | Tyshon (Whiz City); TJ (Whiz City); Bumpa (Whiz City); Outlaw (TYMB); Ro Ro (TYMB); Ken (MTV); Chino (MTV) | Lowe (Whiz City) |
| T3 |  | Gangster Disciple |  | Y | ??? (TYMB); ??? (Whiz City); ??? (Whiz City); Dontay (GMEBE); Sakinah (GMEBE) | Bravo (GMEBE) |  |
| ZoLil Mexico (décédé)Santana (décédé) |  |  | Y |  |  |  |  |

### MNA (4CH)

`https://privedatabase.wordpress.com/mna-4ch/` · page 8005 · FCK HEAD$HOT · 2020-02-10

- **Nations:** 4 Corner Hustlers
- **Allies:** _none_
- **Enemies:** B-Gang
- **Notes:** Based in West Chicago; responsible for a triple murder outside a store in late 2019.

- **Bodies attributed to the set:** Quashun (B-Gang), Tion (B-Gang), Charles (B-Gang)

### MOB

`https://privedatabase.wordpress.com/mob/` · page 7483 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Gangster Disciples
- **Allies:** Geo Drive, Von World, SKD, STL/EBT, Wuga World, Jaro City
- **Enemies:** 600, Front$treet, BlackGate, THF 46, Shields, DukeSquad, Nicko Gang, MetLife, O'Block
- **Notes:** MOB stands for Mind On Business.

- **Bodies attributed to the set:** CO (Front$treet), K-Killa (Front$treet), Corey-B (Front$treet), Blood Money (Front$treet), BlackBoy (Brick City), Baldy (600), Lil Steve (600), Stello (600), Burger (600), Waldo (600), Jamiere (BlackGate), Fred (Shields), ? (Shields), Lil Nick (DukeSquad), Pyro (800), Trey Savage (Nicko Gang), JMacc (MetLife), ??? (???)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Lil Shaan |  | Gangster Disciple |  |  | Waldo (600, tué en 2018) | Demon (Nicko Gang); Porkey (600); Lil Blast (BlackGate); Chick Lee (Front$treet); ScoWop (Front$treet) |  |
| Lil Bobo |  | Gangster Disciple |  |  |  |  | Waldo (600) |
| Mal |  | Gangster Disciple |  |  | Burger (600) | Lil G (Front$treet); Dreski (Front$treet); Juice Da Savage (Front$treet); Gino Marley (Front$treet); Nate (Front$treet); Chief Domo (600); BlastHisAss (600); Kuda (600) | Stello (600) |
| Nut |  |  |  |  | Lil Nick (DukeSquad) | Makado (600); Tay600 (600); Jusblow (600); Memo (600); Carl Fredo (Front$treet); Nate (Front$treet); J3 (Front$treet); C. Blac (Nicko Gang) | Stello (600); Burger (600) |
| 10 Mille |  | Gangster Disciple |  |  |  | BossMoo (600); Manny (600); Kuda (600); BlastHisAss (600); Mooch (Front$treet); Ray (DukeSquad); Day Day (Nicko Gang) | Lil Nick (DukeSquad); Waldo (600) |
| BayBay |  | Gangster Disciple | Y |  | ??? (???); Stello (600) | AK (Brick City/600); Boowop (600); S.Dot (600); Landro Da Don (Front$treet); Shawn (Front$treet); Quawn (MetLife) | Lil Steve (600); Blood Money (Front$treet); Lil Boo (600) |
| Beans |  | Gangster Disciple |  | Y |  | Booka (600); Bitedown (600); Memo (600); Will (O'Block); SD (BlackGate); Kyro (Front$treet); Lil So (Front$treet); Guwop (Front$treet); Young (STL/EBT) | Baldy (600); Phillip (Roc Creek) |
| Bookie |  | Gangster Disciple |  |  |  | Mystro (MetLife); Dro Philly (600) | Baldy (600) |
| Cleon |  | Black Disciple |  | Y | K-Killa (Front$treet); Jamiere (BlackGate) | Max (Front$treet); Dreski (Front$treet); Lil G (Front$treet); Tadoe (Front$treet); Meechy (Front$treet); Mook (BlackGate); OBGeezy (BlackGate); Edai (600); Inky D (600); D Money (600); B-Mike (O'Block) | Baldy (600) |
| Domo |  | Gangster Disciple |  | Y | CO (Front$treet); Baldy (600); Pyro (800) | Scud (Front$treet); Landro Da Don (Front$treet); Ruskee (Front$treet); Nino (Front$treet); Big Woo (Front$treet); Bit Bit (Front$treet); Tylee (Front$treet); Kudos (Front$treet); Booka (600); Huncho Hoodo (600); 600Breezy (600); Trigga (600); Cdai (600) |  |
| Dooski | Dooski Tha Man | Gangster Disciple |  |  | ? (Shields) | GloWop (Front$treet); J Smoove (Front$treet); Kyro (Front$treet); Lil Gunz (Nicko Gang); Lil Dee (600); Man-Maneski (600) |  |
| Killa K.I |  | Gangster Disciple | Y | Y |  | Max (Front$treet); Michael (Front$treet); Big Woo (Front$treet); Kudos (Front$treet); Juice Da $avage (Front$treet); Darnell (Front$treet); Anthony (Front$treet); Block Poppa (Front$treet); Republican (Front$treet); Tadoe (Front$treet); Nate (Front$treet); Gino Marley (Front$treet); Dev Smiley (Front$treet); Landro Da Don (Front$treet); Young Famous (600); Boowop (600); M-Thang (600); B-Baby (MetLife); J-How (BlackGate); Wooh Thang (DukeSquad) |  |
| Lil Moe |  | Gangster Disciple |  | Y |  | Lil So (Front$treet); ??? (O'Block) |  |
| Lil Scrapp |  | Gangster Disciple | Y |  | Lil Steve (600); Fred (Shields) | FaceSixO (600); BlastHisAss (600); RondoNumba9 (600); Cdai (600); Booka (600); Waldo (600); Nino (Front$treet); Ruskee (Front$treet); Trey (Front$treet); Scotty (O'Block); Lil Allan (O'Block); OTF Ikey (O'Block); SD (BlackGate); Denno (BlackGate) | Baldy (600); Odee (WIIIC City) |
| Monsta |  | Gangster Disciple | Y |  | Trey Savage (Nicko Gang) | MeatBall (Front$treet); Sosa (Front$treet); Vinceo (Front$treet); P-Wop (Front$treet); Wooh Thang (DukeSquad); Boos Jack (DukeSquad); Lil JB (Nicko Gang); KuKu (Nicko Gang); FaceSixO (600) |  |
| Mooche |  | Gangster Disciple |  |  | Blood Money (Front$treet) |  | Fred (Shields) |
| Rob |  | Gangster Disciple |  |  |  |  |  |
| Rooga |  | Gangster Disciple |  |  |  | Nate (Front$treet); Maino (Front$treet); Chief Domo (600) |  |
| Lil Des |  | Gangster Disciple |  |  | JMacc (MetLife) |  |  |
| Jamo |  | Gangster Disciple | Y |  |  | 600Breezy (600); S.Dot (600) | Baldy (600) |

### MOE

`https://privedatabase.wordpress.com/moe/` · page 971 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Gangster Disciples
- **Allies:** No Luv City
- **Enemies:** _none_

- **Members listed:** Famous DexPillZalskyFlockaLABillyBandanaDonnoMooMooGlizzyBoyMoeFK (décédé), NinoJuJu (décédé), DooDoo (décédé), 6 ShotsBall HardDMoneyIzzyLesMarlonQuinny MacTayTone BoneJugg (décédé), Glizzy (décédé), Lil Ron (décédé), DukeGMac (décédé)

- **Bodies attributed to the set:** Drizzle (Flin Boyz), Lil Greg (FollyBoyz), Paw Paw (FollyBoyz), Dart (ABM), Tece (Lamron), Lil Moe (Lamron), Armani (FollyBoyz), Skooly (Flin Boyz)

### MOETOWN

`https://privedatabase.wordpress.com/moetown/` · page 479 · FCK HEAD$HOT · 2020-03-27

- **Bodies attributed to the set:** NuNe (Insane City), Woo (Shields), Migo (Shields), Tonio (Dumpstreet), Eddy (La Raza), Ju (No Luv City), Rusty (Shields), Malachi (Shields), Fatz (No Luv City), Tell (Jaro City), Zoey Zoe (CMB), G-Nauch (Insane City), Johno (Pocket Boyz), Nelly (Pocket Boyz), Kae (Pocket Boyz)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| YCK |  |  |  |  |  |  |  |
| FOLLYBOYZ |  |  |  |  |  |  |  |
| BBG |  |  |  |  |  |  |  |
| MACTOWN |  |  |  |  |  |  |  |
| KTC |  |  |  |  |  |  |  |
| GGE |  |  |  |  |  |  |  |
| JETGANG |  |  |  |  |  |  |  |
| 5400 |  |  |  |  |  |  |  |
| AMB |  |  |  |  |  |  |  |
| BACKBLOCK |  |  |  |  |  |  |  |
| OTL |  |  |  |  |  |  |  |
| JACKBOYS |  |  |  |  |  |  |  |
| JUST-US |  |  |  |  |  |  |  |
| MURDAFIELD |  |  |  |  |  |  |  |

### MOETOWN

`https://privedatabase.wordpress.com/moetown-2/` · page 7490 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Black P.Stones
- **Allies:** 600, O'Block, Lamron, NLMB
- **Enemies:** Dumpstreet, 051 Young Money, No Luv City, La Raza, LOC City (DamenVille)/Blood Gang, Shields, 50 Strong, Jaro City, NuneWorld, 757, HB, CMB, Insane City, STL/EBT
- **Notes:** MoeTown is an alliance made up of Folly Boyz, GGE, Lowelife (not the separate set of the same name), Murdafield, D-Block, BackBlock, SODMG, Just-Us, OTL, 5400, KTC, Jet Black, AMB, MackTown and Jackboys.

- **Bodies attributed to the set:** DeAndre (50 Strong), Tyree (50 Strong), Dell (50 Strong), Dougo (50 Strong), Big Meech (50 Strong), Temmo (50 Strong), Tra'Don (50 Strong), Big Hersh (No Luv City), Wally (No Luv City), Earl (No Luv City), Stain (No Luv City), Shoe (No Luv City), Glizzy (No Luv City), Dope (No Luv City), Mook-G (No Luv City), Fatz (No Luv City), Jugg (No Luv City), Doodroo (No Luv City), Woo (Shields), Migo (Shields), Rusty (Shields), Malachi (Shields), Peanut (Shields, tué en 2018), Nate (Dumpstreet), Tonio (Dumpstreet), Lowe (Dumpstreet), Blue Benji (Dumpstreet, tué en 2018), Tunechi (NuNeWorld), G-Nauch (NuNeWorld, tué en 2019), Bankroll Q (051 Young Money), Big Lonnie (051 Young Money, tué en 2018), Tell (Jaro City, tué en 2018), Eddy (La Raza), Nune (Insane City), Ill Will (DamenVille), Bop D (DamenVille), Tuda (DamenVille), Heado (DamenVille), Tay Burna (DamenVille), G-Pap (DamenVille), Lil Steve (LOC City BOTY), Buck (LOC City BOTY), Roc (LOC City BOTY), G-Nuk (FollyBoyz), Zoey Zoe (CMB), Johno (PocketBoyz), Nelly (PocketBoyz), Kae (PocketBoyz), Blue (PocketBoyz), Lil Glenn (JigDogs), 1.4 (GGE/MoeTown)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| 50Shot Mall |  | Black P.Stone |  | Y | Earl (No Luv City); Peanut (Shields, tué en 2018) | Kiar (50 Strong); Loko (50 Strong); Chief Rell (50 Strong); CEO (50 Strong); Chief Rell (50 Strong); Zo (No Luv City); Rambo (No Luv City); Bootz (No Luv City); Killa Kellz (Brick$quad 069); Strizzy (Dumpstreet); PD (051 Young Money, 2018); Lil Danny (051 Young Money, 2018); Kymeon (051 Young Money, 2018); Maneski (051 Young Money); G-Rayski (GeoDrive); G-Mally (GeoDrive) | Lil Doc (No Luv City); Wally (No Luv City); Temmo (50 Strong) |
| Booda Moe |  | Black P.Stone |  |  | Big Hersh (No Luv City); Wally (No Luv City) |  |  |
| Chief Diddy |  | Black P.Stone |  |  | Stain (No Luv City); Glizzy (No Luv City) | OG Haitian (50 Strong); Rosé (50 Strong); Breezy (50 Strong); King Murda (50 Strong); Jimmy (No Luv City); G Rasto (No Luv City); Izzy (No Luv City); Poom (Dumpstreet); T Man (Dumpstreet); PD (051 Young Money, 2018); Lil Danny (051 Young Money, 2018); Kymeon (051 Young Money, 2018); Maneski (051 Young Money); G-Rayski (GeoDrive); G-Mally (GeoDrive) | Earl (No Luv City); King Thaddo (50 Strong) |
| CoKilla |  | Black P.Stone |  | Y | Temmo (50 Strong) | Blood (50 Strong); Juice (50 Strong); Csko (50 Strong); Major (No Luv City); Teeski (No Luv City); KC (No Luv City); Alo (Shields); Hov (Dumpstreet); Ario (051 Young Money); James (051 Young Money) | Lil Doc (No Luv City); Big Meech (50 Strong); Lil Marc (051 Young Money) |
| Five Star | Star-G | Black P.Stone |  | Y | Big Meech (50 Strong) | Csko (50 Strong); Kiar (50 Strong); CEO (50 Strong); King Greg (50 Strong); Triggah900 (50 Strong); Rambo (No Luv City); Duke (No Luv City); Les (No Luv City); Puke (Dumpstreet); Mally (051 Young Money) | Temmo (50 Strong); Lil Marc (051 Young Money) |
| G-Nuk |  | Black P.Stone | Y |  | Tunechi (Dumpstreet); Shoe (No Luv City); Rashon (Lafas) | Zo (No Luv City); Boss Veze (No Luv City); Wop (No Luv City); DJ (50 Strong); Vic (Dumpstreet); Jaski (Dumpstreet); Strizzy (Dumpstreet); T Man (Dumpstreet) | Lil Doc (No Luv City) |
| Khalil |  | Black P.Stone |  | Y |  |  | Rell (757) |
| Breeze |  | Black P.Stone | Y |  | Bankroll Q (051 Young Money) | MoKilla (No Luv City); D3 (No Luv City); Tay (No Luv City); Max LaFlare (No Luv City); Lil Ant (No Luv City); ManyNames (50 Strong); KD (051 Young Money) |  |
| Darren |  | Black P.Stone |  |  | Big Lonnie (051 Young Money) | Israel (No Luv City); King Murda (50 Strong); Chief Rell (50 Strong) |  |
| Maintain |  | Black P.Stone |  |  |  | Boss Bully (50 Strong); Big Squad (50 Strong); JD (50 Strong); Rambo (No Luv City); Nino (No Luv City); Ball Hard (No Luv City); Boss Jay (No Luv City); Aero (051 Young Money) | Big Meech (50 Strong) |
| Raysko |  | Black P.Stone |  |  |  | YC Da Problem (50 Strong); Tonio (No Luv City) | Big Lonnie (051 Young Money) |
| Bubba |  | Black P.Stone |  | Y | Nate (Dumpstreet) |  |  |
| Scrap | Mr.Shoot Up The Party | Black P.Stone | Y |  | Dougo (50 Strong); Dell (50 Strong) |  |  |
| Smalls |  | Black P.Stone |  |  |  | Duke (No Luv City); Gunplay (No Luv City); G Rasto (No Luv City); Izzy (No Luv City); Quack (Dumpstreet); Law (051 Young Money) | Bankroll Q (051 Young Money) |
| OMillie |  | Black P.Stone |  | Y |  | King Greg (50 Strong); Lil Duwuap (50 Strong); Two Times (No Luv City); Ray Bands (No Luv City); Ball (No Luv City); Gino Louchie (No Luv City); JuJu (Dumpstreet) |  |
| EBK Trigga |  | Black P.Stone |  |  |  | Wack (051 Young Money); Ant (051 Young Money); Roscoe (50 Strong); YC (50 Strong); John Gotti (50 Strong); Breezy (50 Strong) |  |
| J-Roc |  | Black P.Stone | Y |  |  | Les (No Luv City); Jackpot (No Luv City); Famous Dex (No Luv City); CEO (50 Strong) |  |
| Moneyman |  | Black P.Stone |  |  |  |  |  |
| O-Dogg |  | Black P.Stone |  |  |  |  |  |
| Freddy Mac |  | Black P.Stone |  |  |  |  |  |
| Caddy Mac |  | Black P.Stone |  |  |  |  |  |
| YG Shorty |  | Black P.Stone |  |  |  |  |  |
| TWhy |  | Black P.Stone | Y |  |  |  | Bankroll Q (051 Young Money) |
| Malik |  | Black P.Stone |  | Y | G-Nuk (MoeTown) |  |  |

### MONEY BY ANY MEANS (MBAM)

`https://privedatabase.wordpress.com/money-by-any-means-mbam/` · page 7963 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Gangster Disciples
- **Allies:** Brick$quad 069
- **Enemies:** Buff City
- **Notes:** Based in the Wild 100's; rapper Lil Flip is a member.

- **Members listed:** Lil Flip est un Gangster Disciple. Il est le petit frère de Mazi et le grand frère de Dre du même set. Il est un membre officiel du JoJo World. Il est proche de certains membres de la Brick$quad 069.

- **Bodies attributed to the set:** Wayne (Buff City), D.Rose (Buff City, tué en 2018), Cortez (Buff City), ??? (Buff City), ??? (Buff City)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| D.Rose (Buff City, tué en 2018) |  |  |  |  |  | Père de Glahh (Buff City) |  |
| Mazi |  | Gangster Disciple |  |  | ??? (Buff City); ??? (Buff City) |  |  |
| Roc Roc (décédé)Glizzy (décédé)2Glockz (décédé)Da (décédé)Re |  |  | Y |  |  |  |  |

### MOOSEBLOCK

`https://privedatabase.wordpress.com/mooseblock-2/` · page 7942 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Gangster Disciples
- **Allies:** _none_
- **Enemies:** PaxTown, Sirconn City Gangsters

- **Members listed:** Lil Moose (décédé), Lil PoloGhetto (décédé), Boss Kee (décédé), MuMu (décédé), Skitso (décédé), JJ (décédé), Skee (décédé), Gucci (décédé), Aaron (décédé), BoomBoom (décédé)

- **Bodies attributed to the set:** EJ (PaxTown), Floyd (PaxTown), Mannie (PaxTown), Dinno (PaxTown), Jaleel (PaxTown), John'O (Sirconn City Gangsters), Kojack (PaxTown), Pierre (PaxTown), Lil Larry (PaxTown), Burt (PaxTown), Big Moe (PaxTown), Trife (PaxTown), Tracy (PaxTown), Dominic (Sirconn City Gangsters), Yatta (PaxTown), Pete (PaxTown), Jaleel (PaxTown), Black (PaxTown), Snoop (PaxTown), NuNu (PaxTown), Mari (Sirconn City Gangsters)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Bonna |  | Gangster Disciple |  | Y |  |  |  |
| Shawty |  | Gangster Disciple |  | Y | Jaleel (PaxTown) |  |  |

### MTG

`https://privedatabase.wordpress.com/mtg-2/` · page 7953 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Gangster Disciples
- **Also known as:** Drama World
- **Allies:** _none_
- **Enemies:** NLMB
- **Former allies:** NLMB
- **Notes:** Named 'Drama World' in honor of slain member Drama; known for killing Capo of the GBE; some NLMB members still represent Drama World.

- **Members listed:** Red Dot est un Gangster Disciple. Il n'est PAS le tueur de GBE Capo.

- **Bodies attributed to the set:** Rayford (NLMB), GBE Capo (Front$treet), Lil Gage (NLMB), Solo (NLMB)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| GBE Capo (Front$treet) |  |  |  |  |  |  |  |
| Drama (décédé)Biyo (décédé)Lil Joe (décédé)Lil C (décédé)Wop |  |  | Y |  |  |  |  |

### MTV

`https://privedatabase.wordpress.com/mtv-2/` · page 7906 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Black Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Based in Chatham; rapper Tray Savage of Glo Gang is a member.

- **Bodies attributed to the set:** Juany (Mixx Mobb), Twan (Mixx Mobb), Lil Chris (Evans Mobb), Mannie (8Tre Mobb), Jeromy (Hitzsquad), BT (Evans Mobb), Don Darius (8Tre Mobb), Hell Mell (Hitzsquad), Daemon (Mixx Mobb), BJ (Mixx Mobb), Young (Hitzsquad), Nookie (Whiz City)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Polo |  | Black Disciple |  |  | Don Darius (8Tre Mobb) |  |  |
| Murda Manski |  | Black Disciple |  | Y | Juany (Mixx Mobb); Mannie (8Tre Mobb) | Lil De'Seann (MixxMobb); OJay (MixxMobb); Act Rite (Evans Mobb); Teddy (8Tre Mobb); Murda Mal (8Tre Mobb); Kenneth (8Tre Mobb); Leaky (Drill City) |  |
| Tray Savage |  | Black Disciple |  |  |  | Ant Man (8Tre Mobb); TayRuga (8Tre Mobb); Kavontae (8Tre Mobb); James (8Tre Mobb); Shoota Shoota (8Tre Mobb); Pooka (Evans Mobb); Pierre (Evans Mobb); D'Money (MixxMobb); Lil Jay (STL/EBT) |  |

### MURDAFIELD

- **Nations:** Black P.Stones
- **Allies:** MoeTown
- **Enemies:** _none_

### MURDATOWN

`https://privedatabase.wordpress.com/murdatown-2/` · page 7933 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Allies:** 600
- **Enemies:** 051 Young Money, JigDogs, 757, MOB
- **Notes:** Responsible for the imprisonment of RondoNumba9 and Cdai of the 600, though relations with the 600 remain good; at war with MOB since 2020.

- **Members listed:** Timo est un Gangster Disciple. En 2014, il tire sur un ennemi du MurdaTown mais les balles vont en direction de Lil Boo (600)

- **Bodies attributed to the set:** Mike (757), Gregory (JigDogs), ??? (757), Ray Ray (757), Tarzan (757), Ayanna (affiliée de la PMBMB), Ant (PMBMB), Tyrone (PMBMB), Jim Bean (Jaro City, tué en 2019), Carter (757), Buddy (757), Crack (757)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Mike (757)Gregoy (JigDogs) |  |  |  |  |  | Snoop (757); Obama (757); Spatch (757); Gucci (757); AP (757); Louie (757); Lil Say (SuWu TTB) |  |
| Boss Luck |  | Gangster Disciple |  | Y | Ayanna (PMBMB affiliée); Ant (PMBMB); Tyrone (PMBMB) | ??? (051 Young Money, en 2015); ??? (051 Young Money, en 2015) | Sonny (757) |
| Terry (décédé)Draco (décédé)Millie (décédé)Doe (décédé)Lil S |  |  | Y |  |  |  |  |

### MURDERVILLE

`https://privedatabase.wordpress.com/murderville/` · page 1152 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Gangster Disciples
- **Also known as:** STL/EBT, Boss City
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** MurderVille was the former name of the set now known as STL/EBT; nobody uses the MurderVille name anymore.

- **Members listed:** Ty (décédé), GregDeadman (décédé), Snap Brian Thomas (décédé)

- **Bodies attributed to the set:** Tokyo G (WIIIC City)

### NICKO GANG

`https://privedatabase.wordpress.com/nicko-gang-2/` · page 7925 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Allies:** 600, OBN, 400E Murda Drive
- **Enemies:** _none_
- **Notes:** Based in Washington Park; considered the future generation of the 600.

- **Members listed:** Demon est un Gangster Disciple.

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Booman (Geo Drive)Quesy (Geo Drive)Shell Da Don (MOB)Dupree |  |  |  |  |  |  |  |
| KuKilla |  | Gangster Disciple |  |  |  | Lil Ant (Geo Drive); Lil Bobo (MOB) |  |
| Lil Nick |  | Gangster Disciple |  |  |  |  |  |
| OnSight |  | Black Disciple |  | Y |  | Dooski (Geo Drive); Leek (MOB); Damari (MOB); Noah (MOB); AP (757); Tyler (Tyquan World) | Khalil (Pointe Drive) |
| Lil JB |  | Gangster Disciple |  |  |  | G-Mally (Geo Drive); Louie (Tyquan World) |  |
| Melvo |  | Gangster Disciple | Y |  |  | Kesy (Tyquan World); Polo (Tyquan World); Double (Geo Drive); Koro (MOB) |  |
| Trey Savage |  | Gangster Disciple | Y |  |  | G-Rayski (Geo Drive); Ty (MOB) |  |
| OttoTay Savage (frère de Trey Savage)Rico (décédé)Valentino |  |  | Y |  |  |  |  |

### NO LIMIT 083

`https://privedatabase.wordpress.com/no-limit-083-2/` · page 7948 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Black P.Stones
- **Also known as:** No Limit No Essex
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Based in South Chicago.

- **Members listed:** 358 Trap GodTony (décédé), VestaD NiceKing Sosa (décédé), 40ZolaHakeemLontaeVonteLimaceLil MoeDreDay (décédé), PC (décédé), SmileyJaymo Tha'Don (décédé), Weezy (décédé)

### NO LIMIT 087

`https://privedatabase.wordpress.com/no-limit-087-2/` · page 7937 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Black P.Stones, Latin Kings
- **Also known as:** Medina Town, 500, Murda Ave
- **Allies:** _none_
- **Enemies:** _none_
- **Former enemies:** NLMB
- **Notes:** Formerly at war with NLMB; tensions have cooled and relations became neutral.

- **Members listed:** Goonie Looney360WinnieHarvey (décédé), Lil DaveCBLamontMurda (décédé), ChoppaRalph (décédé), SmileyBig G (décédé), P-Nut (décédé), Rolex (décédé), Fred (décédé), Lil RedWhitney (décédé), Joe (décédé), B-Neal (décédé), Jareem (décédé), Sosa (décédé), Cassey (décédé), PatPerryLil Jermaine (décédée), Mookie (décédé), StuntaSnake (il est gay), CK (il est gay)

- **Bodies attributed to the set:** Carl (APS)

### NO LIMIT/MUSKEGON BOYZ

`https://privedatabase.wordpress.com/no-limit-muskegon-boyz/` · page 7487 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Renegade Black P.Stones, Renegade Gangster Disciples
- **Allies:** ABK, THF 46, 600 (part), O'Block (part), MoeTown (some)
- **Enemies:** Lakeside, KTS, DeathRow 085, MTG, Black Mobb, Jaro City, STL/EBT, ABKColes Mobb, D-Town
- **Former allies:** MTG
- **Former enemies:** ABK, No Limit 087
- **Notes:** NLMB stands for Never Leave My Brothers, an alliance of No Limit (Renegade Black P.Stones) and Muskegon Boys (Renegade Gangster Disciples), an EBK set; rappers G Herbo and Lil Bibby are members; still represents MTG's slain member's Drama World despite now being at war with MTG.

- **Bodies attributed to the set:** ??? (tué par Big Wet), ??? (tué par Big Wet), ??? (tué par Big Wet), ??? (tué par G-Slim), ??? (tué par G-Slim), ??? (tué par Big Nuskii), ??? (tué par G-Bread), ??? (tué par G-Gil), Larry (Lakeside), Hakeem (Black Mobb), Ravon (Black Mobb), Jordan (Black Mobb), B-Neal (No Limit 087), Nutts (Lakeside), Lucky (Black Mobb), Eric (Black Mobb), DickHead (Lakeside), Deo (Black Mobb), Gucci (Lakeside), Oochie (KTS), LoLo (Lakeside), Bud (KTS), Posto (Lakeside), Deebo (KTS), KTS Von (KTS), T-Bone (Black Mobb), Lil Jamaine (Lakeside), Nunnie (MTG), Lil Paris (Lakeside), Lil 4 (MTG), Archie (Jaro City), Biyo (MTG), Lil Joe (MTG), Jo Blo (MTG), Lil C (MTG), Wop (MTG), Ed (Ceno City), Raheem (Ceno City), Dylan (Ceno City), Emmanuel (Ceno City), Gege (D-Town), Christian (No Limit 083), Ronald (No Limit 083), PaPa (Out7aw City), Taco (FuckTown), Stixx (FuckTown), OneStep (PaxTown), Lil Moe (Sirconn City Gangsters), Jamonty (No Luv City, tué en 2019), Lil C (KillaWard, tué en 2019)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| EBK Juvie |  | Black P.Stone |  | Y | LoLo (Lakeside) | TrappMoe (BlackMobb); D-Boy (BlackMobb); Awol (BlackMobb); Nemo (No Limit 083); Birdy Montana (Lakeside); Royal Baybee (Lakeside); Denny G (KTS); Chief Smokey (KTS); Aero (KillaWard); D-Will (PacoLand, avant son arrestation); Bally (PacoLand, avant son arrestation) | Jordan (Black Mobb); Bud (KTS); KTS Von (KTS) |
| 30 Clipz |  | Black P.Stone |  | Y | Archie (Jaro City) | Jackboii Dezz (Lakeside); Booda (Lakeside); Kobe (Jaro City); Pook (MTG); Den (MTG) | Biyo (MTG); Wop (MTG) |
| Choppa |  | Black P.Stone |  | Y | Von (KTS); Wop (MTG) |  |  |
| Copo |  | Black P.Stone | Y |  | Lil 4 (MTG) |  |  |
| CrateHead | Credo | Black P.Stone |  | Y | Ravon (Black Mobb); Nutts (Lakeside); Lucky (Black Mobb) |  |  |
| Crazy James | CJ | Black P.Stone |  | Y | Jordan (Black Mobb); Fille (Lakeside); Posto (Lakeside) | Bud (Lakeside); El PoyoLoco (Lakeside); Lil Paris (Lakeside); Rickey (Lakeside); Royal Baybee (Lakeside); Booda (Lakeside); ShawtyHitt (BlackMobb); Black (BlackMobb); TMoe (BlackMobb); Shakey (BlackMobb); Whiz (BlackMobb); KTS Dre (KTS); Chief Smokey (KTS); KTS Von (KTS) | Ronald (No Limit 083); Eric (Black Mobb) |
| Doowop | Wop“, «Dooski, 60 Shots | Black Disciple |  |  | T-Bone (Black Mobb) | Jay (BlackMobb); Main Mane (BlackMobb); King Scoobz (BlackMobb); Rocky (BlackMobb); Lil Mil (Lakeside); Quagg (MTG); Puva (MTG); Hari (Jaro City) | Lil Jamaine (Lakeside) |
| Fazo |  | Black P.Stone | Y |  | Larry (Lakeside) |  |  |
| G Herbo ou Lil Herb |  | Black P.Stone |  |  |  | King Mello (Lakeside); Snook (Lakeside); Lil John (Lakeside); Blu (Lakeside); Main Mane (BlackMobb); ShootaShellz (BlackMobb); ShawtyHitt (BlackMobb); Fro Moe (BlackMobb); Black (BlackMobb); Bud (KTS); Murda Migo (KTS) | Christian (No Limit 083); LoLo (Lakeside) |
| G-Maneski |  | Black P.Stone |  |  | B-Neal (No Limit 087); Taco (FuckTown) | T'o Da Prince (BlackMobb); TrappMoe (BlackMobb); Boodaman (BlackMobb); Main Mane (BlackMobb); Rocky (BlackMobb); Smokey J (KTS); Mello (Lakeside); Leek (MTG) | T-Bone (Black Mobb) |
| Kilo |  | Black P.Stone |  | Y | Biyo (MTG) | Rio G (KTS); TVK (MTG); Den (MTG) | Wop (MTG) |
| Lil Chief |  | Black P.Stone |  |  | Gucci (Lakeside) |  |  |
| Mally | Mr.Shoot Up The Party | Black P.Stone |  |  | Oochie (KTS); Lil Joe (MTG); Lil C (MTG) | Montana (BlackMobb); Clifton (BlackMobb); Ashton Kutcher (BlackMobb); Cameron (BlackMobb); King Poochie (Lakeside); TimDog (Lakeside); Boss Ceejay (KillaWard); Lil Art (PocketTown); Kane (MTG); JR (MTG) | DickHead (Lakeside); Deebo (KTS) |
| Kyro |  | Black P.Stone |  |  | Gege (D-Town); Ronald (No Limit 083) | Lil Jamaine (Lakeside); Posto (Lakeside); TimDog (Lakeside); T-Beastie (Lakeside); Don Don (KTS); KTS Von (KTS); KTS Dre (KTS); Lil Bill (KTS); Curfew (BlackMobb); T-Money (BlackMobb); King Turk (BlackMobb); DoomzDay (PocketTown) |  |
| Merch Money |  | Black P.Stone |  |  | Bud (KTS); Deebo (KTS); JoBlo (MTG); Lil Jamaine (Lakeside) | Booda (Lakeside); KTS Dre (KTS); Sino (KTS); Blowski (PocketTown); Boss Gee (PocketTown); Ty (MTG); Pook (MTG); Boss Nut (MTG); Boogie (BlackMobb) | Nunnie (MTG); Lil Joe (MTG); Lil C (MTG); Wop (MTG) |
| OTF Pat | Project | Black P.Stone |  |  |  | ShootaShellz (BlackMobb); Ronnie Moe (PocketTown); Junior (Lakeside) | Archie (Jaro City) |
| Pistol P | PeeWee | Black P.Stone | Y |  | Hakeem (Black Mobb) |  |  |
| Smoke Da D.O |  | Black P.Stone |  |  | Lil Paris (Lakeside) |  |  |
| WetEmUp | vengeance | Black P.Stone |  | Y | DickHead (Lakeside); Nunnie (MTG); Ed (Ceno City); Raheem (Ceno City); Dylan (Ceno City); Emmanuel (Ceno City) | Greg (BlackMobb); Taco (BlackMobb); Boodaman (BlackMobb); BooMan (Lakeside); Snook (Lakeside); KTS Dre (KTS); Denny G (KTS); El Chapo (MTG) | Oochie (KTS); Lil Jamaine (Lakeside); Wop (MTG) |
| MaddMaxx |  | Black P.Stone | Y |  | PaPa (Out7aw City); Deo (Black Mobb); Eric (Black Mobb); KTS Von (KTS) | Sino (KTS) | ??? (KTS); Ed (Ceno City); Raheem (Ceno City); Dylan (Ceno City); Emmanuel (Ceno City); Bud (KTS); LoLo (Lakeside); Jordan (Black Mobb); Posto (Lakeside) |
| Big Wet était le père de Lil WetEmUp du même set. Il était l |  |  |  |  | ????????? |  |  |
| G-Slim était le père de Lil G-Slim du même set et le frère d |  |  |  |  | ?????? |  |  |

### NOSEDMOBB

`https://privedatabase.wordpress.com/nosedmobb-2/` · page 8000 · FCK HEAD$HOT · 2020-02-07

- **Nations:** Black Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Based in the Holy City area; named in honor of a member who died in 2009.

- **Members listed:** KNine RemyVSOPSheen Capone

### OAK BOYZ NATION (OBN)

`https://privedatabase.wordpress.com/oak-boyz-nation-obn/` · page 7895 · FCK HEAD$HOT · 2019-11-19

- **Nations:** Gangster Disciples, Black Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** OBN stands for Oak Boyz Nation; source bio text is truncated (cuts off mid-sentence).

- **Bodies attributed to the set:** Jay-G (SuWu TTB), Therlow (SuWu TTB), Mero (SuWu TTB), BooG (SuWu TTB), Willie (757), Boonie (757), Rob (757), Ray Ray (757), Frump (051 Young Money), Boola (JigDogs), Aaron (TouchMoney), Khalil (Pointe Drive)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| “Oak Boy Nation“. La rappeuse «KatieGotBandz» vient de ce se | Oak Boy Nation“. La rappeuse «KatieGotBandz |  |  |  |  |  |  |
| Scoota |  | Gangster Disciple | Y |  | Frump (051 Young Money) | Mook (757); 757Wooski (757); Jizzle (757); BA (757); Kenny (SuWu TTB) |  |
| Booda | Boss Rell | Black Disciple | Y |  | DonJuan (SuWu TTB) | Quanny (JigDogs); Tony (JigDogs); Mero (SuWu TTB) |  |
| Dise |  | Black Disciple |  | Y | Khalil (Pointe Drive) |  |  |

### Odee

`https://privedatabase.wordpress.com/odee/` · page 1189 · FCK HEAD$HOT · 2020-03-28

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Jeremy (Jaro City) |  |  |  |  |  | M.Dot (Jaro City); Lil Worka (Jaro City); Baby D (Jaro City); DipLow (Jaro City); Tilgo (Jaro City); Mr.Hot Sauce (STL/EBT); Diesel (STL/EBT); K.I. (STL/EBT); FBG Butta (STL/EBT) | Mook (Jaro City) |

### OMillie

`https://privedatabase.wordpress.com/omillie/` · page 3884 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| King Greg (50 Strong)Lil Duwuap (50 Strong)Two Times (No Luv |  |  |  |  |  |  |  |

### ONLY THE END (OTE)

`https://privedatabase.wordpress.com/only-the-end-ote/` · page 7960 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Gangster Disciples
- **Also known as:** Wild End, TMG, Nation Block, Money Mobb
- **Allies:** PBG, OTA, SK, Sac Boyz, 1200, Drake City, BH, AMM, E-Way
- **Enemies:** Sedville, Marshall Field MCs, LOC City, GVG, TBG, SuWu, Bejian World, OTG, TNG, CAst, GhostTown, BuckTown, SuWu Mobb
- **Notes:** Based in Near North Side; some OTE members also represent PBG.

- **Members listed:** FBG Bigga est un Insane Gangster Disciple et membre du groupe “Fly Boy Gang“. Il est proche de STL/EBT et de certains membres comme FBG Duck et Billionaire Black. Il était aussi proche avec Lil Jeff de l'IMM, décédé.

- **Bodies attributed to the set:** Block C (Sedville), Jabari (SedVille), Killa (SedVille), Tim Tim (Sedville), Ed (Sedville), Lil Bit (Sedville), Thana (Sedville), Shoe Diddy (Sedville), Kenny C (SedVille), Castillo (SedVille), Snokey (SedVille), Darnell (SedVille), Kei (Sedville), Mick (SedVille), Mat (SuWu Mobb), Malachi (SuWu Mobb), Black (SuWu Mobb), Banks (SuWu Mobb), Gutta (SuWu Mobb), Lil E (SuWu Mobb), Don D (SuWu Mobb), Patrick (Marshall Field MCs), Lance (Marshall Field MCs), Funcky (Marshall Field MCs), Mookie (Marshall Field MCs), Do It Montana (Marshall Field MCs), Shotty (Marshall Field MCs), June (DBK), Smooth (DBK), Shadown (GhostTown), BooBay (Bejian World), Wanted (BuckTown), Sha-Sha (GhostTown), Style (Bejian World), King Herm (Bejian World)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Block C (SedVille) |  |  |  |  |  | Shaquille (SedVille); ManMan (SedVille); Lil Rondo #9 (SedVille); Dell Gotti (Brick$quad 069) |  |
| Dre Savage | Polo G | Gangster Disciple |  |  |  | Polo G (SedVille) |  |
| DaDa |  | Gangster Disciple |  |  | Block C (SedVille); Tim Tim (SedVille); Ed (SedVille); Lil Bit (SedVille) | Woldie (SedVille); Kyle (SedVille); Therbo (SedVille); Lil Felton (SedVille); Lil Blast (SedVille); Al (SedVille); Max (Marshall Field MCs); Gino (Marshall Field MCs); Rosay (Marshall Field MCs); Henry (SuWu Mobb); Bottle (SuWu Mobb); Jigga (SuWu Mobb) |  |
| JD | John Gotti | Gangster Disciple |  |  | Mat (SuWu Mobb); Black (SuWu Mobb) | Jerk (SedVille); Bud (SedVille); L-Chapo (SedVille); Al (SedVille); Lil Fly (SedVille); Danny (Marshall Field MCs); Mango (Marshall Field MCs); Wheaty (SuWu Mobb); Trick (SuWu Mobb); Moonk (SuWu Mobb) | Tim Tim (SedVille) |
| MakeItHappen | Sosa | Gangster Disciple |  |  | Thana (SedVille) | Smooky Smokes (SedVille); Daddyo (SedVille); Woldie (SedVille); Kemo (SedVille); Skinny (SedVille); Jerk (SedVille); Therbo (SedVille); Bec (Marshall Field MCs); Rex (Marshall Field MCs); Rosay (Marshall Field MCs); Keenan (Lil4Mobb); Mario (Lil4Mobb); Ado (Lil4Mobb); Tune (Lil4Mobb); Duke (SuWu Mobb) | Shoe Diddy (SedVille); Tim Tim (SedVille); Ed (SedVille); Lil Bit (SedVille) |
| Trap | Trap Glo, Quese Mac | Gangster Disciple | Y |  |  | Max (Marshall Field MCs) |  |
| YK |  |  |  |  |  |  |  |
| Luw |  | Gangster Disciple |  | Y |  | Kemo (SedVille); Pooda (SedVille); Jabari (SedVille); Ricky Rackzz (SedVille); Lil Justo (SedVille); Suit (Marshall Field MCs); Mike (Marshall Field MCs); Tooth (SuWu Mobb); Lee (SuWu Mobb) | Black (SuWu Mobb) |
| Lil Mouse | LM | Gangster Disciple |  |  |  |  | Mookie (Marshall Field MCs) |
| DreDay |  | Gangster Disciple | Y | Y |  | Cluck (SedVille); Kei (SedVille); Larry Bird (SedVille); Mitch (Marshall Field MCs); Pron Boy (SuWu Mobb) |  |
| SG Ali (rappeuse)Head (décédé)G WetEmUpLil VellLil NashDeloL |  |  | Y |  |  |  |  |

### OTF

`https://privedatabase.wordpress.com/otf/` · page 4333 · FCK HEAD$HOT · 2020-04-24

- **Members listed:** Lil DurkKing VonBayzoo

- **Bodies attributed to the set:** Tyriq (Bloods Atlanta), Juke (Bloods Atlanta)

### OUT7AW CITY

`https://privedatabase.wordpress.com/out7aw-city-2/` · page 7949 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Apache Stones
- **Allies:** _none_
- **Enemies:** YatesMobb, QuillBlock
- **Notes:** Rapper No Good Loso is a member.

- **Members listed:** No Good Loso est Apache Stone. Mon interview avec lui est disponible en cliquant ici.

- **Bodies attributed to the set:** Gooch (YatesMobb), Dionte (QuillBlock)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Dionte (QuillBlock) |  |  |  |  |  | Lil Dave (YatesMobb); Killa (YatesMobb); T (YatesMobb); Wooda Man (YatesMobb); Vesta (No Limit 083); So Icy (No Limit 083) | Gooch (YatesMobb) |
| Lil Greeg |  |  |  | Y |  | ??? (No Limit 083, en 2020) |  |
| Tom TomJoe SmokeSheed (décédé)DMoe (décédé)MonteCello SosaWo |  |  | Y |  |  |  |  |

### O’BLOCK

`https://privedatabase.wordpress.com/oblock/` · page 1151 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Black Disciples
- **Also known as:** WIIIC City
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Renamed from WIIIC City in honor of member Odee after his death; considered a stronghold for Black Disciples and their allies.

- **Members listed:** DukeE-DoggKing VonPatoon (décédé), MarcusTrey 5T-Roy (décédé), Lil Drilla (décédé), Big AB-MikeBoss MoneyBoss ManC-BangD-BandzJaydo (décédé), MuwopJohnoManCheno (décédé), BossTopChief KeefC-MurdaGleesh HK (décédé), J-Money (décédé), DQ35BJBoboBoobieBoss ShonCarlitoDeloDemarlowDizzleDmaccDPFreakHunchoIkeyJiggaJoey Johno KDKevoLil AllanLil GoochLil KhoriLil MarioSam (décédé), Locsta HendrixNuwapOchoOTF IkeyPrince DreQuanoRageRay RillaScottyScudd ShaunoSheroid (décédé), SlickSoloSPTisT-ManWhite White (décédé), WillieWoney WooZellMomoLil AskiiCortisMookJaydotNenaLil TQ (décédé)

- **Bodies attributed to the set:** Dirty Rell (Jaro City), Marcus (STL/EBT), P5 (Jaro City), Reggie (SKD), Modell (STL/EBT), BossTrell (STL/EBT), Stunna (SuWu TTB), K.I. (STL/EBT), Malcolm (FMG), Twink (Jaro City), Lil Ho (Jaro City), Poppie (Tyquan World), Brick (STL/EBT), TB (Tyquan World), GFredeo (Jaro City), CantGetRight (STL/EBT), Dooski Tha Man (MOB), Troy (innocent), Billy (innocent), Coby (STL/EBT), Père à Tooka (Innocent)

### P-BLOCK (4CH)

`https://privedatabase.wordpress.com/p-block-4ch/` · page 8006 · FCK HEAD$HOT · 2020-02-10

- **Nations:** 4 Corner Hustlers
- **Allies:** _none_
- **Enemies:** GhostMobb
- **Notes:** Based in West Chicago; rapper Lil Savage is a member.

- **Members listed:** Lil Savage

- **Bodies attributed to the set:** LZ (GhostMobb), Nutso (GhostMobb), Will (GhostMobb), Spike (GhostMobb)

### PAXTOWN

`https://privedatabase.wordpress.com/paxtown-2/` · page 7943 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Gangster Disciples
- **Also known as:** Bogus Boyz, Yatta World, EJ City
- **Allies:** _none_
- **Enemies:** MooseBlock
- **Notes:** Based in South Shore; co-founded by the father of TB from Tyquan World.

- **Members listed:** Big TB (décédé, père de TB), EJ (décédé), Lil JoshWhodi (cousin de TB et de Big TB), Yatta (décédé), Floyd (décédé), Mannie (décédé), Dino (décédé), Kojack (décédé), Pierre (décédé), Lil Larry (décédé), Burt (décédé), Big Moe (décédé), Tracy (décédé), Pete (décédé), Jaleel (décédé), Black (décédé), Snoop (décédé), NuNu (décédé)

- **Bodies attributed to the set:** Ghetto (MooseBlock), Boss Kee (MooseBlock), MuMu (MooseBlock), Skitso (MooseBlock), JJ (MooseBlock), Skee (MooseBlock), Gucci (MooseBlock), Aaron (MooseBlock), BoomBoom (MooseBlock)

### PBG/TFG

`https://privedatabase.wordpress.com/pbg-tfg/` · page 7488 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Insane Gangster Disciples
- **Also known as:** Insane Cutthroat Gangsters, FreakyVille, CreamTeam, Mosey World, B-Block, James World
- **Allies:** OTE, STL/EBT
- **Enemies:** LOC City, Slutty Boyz, SouthEnd, Lil4Mobb, Hoola Gang, GVG, IBM, CAst, Buck Town, BWst, WW, TBG, SedVille, Marshall Field MCs, O'Block, 600
- **Notes:** PBG (Rogers Park) was called Insane Cutthroat Gangsters before Pooh Bear was killed and stands for Pooh Bear Gang; TFG (Uptown) stands for The Fucking Guys.

- **Bodies attributed to the set:** Terry (Lil4Mobb), Uno (GVG), Redd (Hoola Gang), DayDay (GVG), Lil 4 (Hazel Mobb), Shandel (Hazel Mobb), Belmont (Hazel Mobb), Byro (TBG), Darell (TBG), Lil Rose (TBG), Big O (TBG), Ivan (BW), Alex (LOC City), AL Mac (LOC City), Slutty (Slutty Boyz), Gerald (LOC City), Michael (SouthEnd), Lil E (LOC City), Jonathan (LOC City), Pig (Slutty Boyz), Bleek (Slutty Boyz), Marcus (LOC City), Blake (LOC City), Von (Killaward 078), Deon (LOC City), Keno (LOC City), Murda (Slutty Boyz), Blake Tha Snake (Slutty Boyz), Munchie (LOC City), EJ (Lil4Mobb), AJ (LOC City), V12 (LOC City), Keon (LOC City), Vonni (LOC City), Duski (Hoola Gang), Ivan (Winthrop Kings), Tommy (Adam Street), Cease (Uptown Lawds), ??? (???), Goofy B (tué en 2019), Craig (D-Block), T (D-Block), Sam (D-Block), Donte (D-Block), Al (CAst), Cease (Uptown Lands)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| King Shoota |  | Gangster Disciple | Y |  | Terry (Lil4Mobb); Uno (GVG); Redd (Hoola Gang) | C-Dre (TBG); Tae Black (TBG); Amarion (Lil4Mobb); Kye (Lil4Mobb); Sconny (Lil4Mobb); Michael (Lil4Mobb); Earl (Lil4Mobb); Damon (Uptown Lawds); Mexico (GVG); Ahunna Stacks (GVG); Mike (Hoola Gang); Rico (Hoola Gang); Jango (Hoola Gang) | EJ (Lil4Mobb) |
| Savage Sheen |  | Gangster Disciple |  | Y | DayDay (GVG) | Kirk (Lil4Mobb); Lil Sam (Lil4Mobb); Zay Tiggy (Lil4Mobb); CEO (GVG); Dirty D (GVG); Big Mike (GVG); J Steev (GVG); Lil Duke (GVG); Lil Zo (GVG); Rocky (TBG) | Lil 4 (Hazel Mobb) |
| Bigz |  | Gangster Disciple |  | Y | Lil 4 (Hazel Mobb); Byro (TBG) |  |  |
| Bang Da Hitta | Mr.Rogers | Gangster Disciple |  | Y | Lil E (LOC City); Munchie (LOC City); Duski (Hoola Gang) | Stevon (LOC City); Marcus (LOC City); Dwight (LOC City); Ice Man (LOC City); Tyjuan (LOC City); B.Lord (LOC City); Skuduh (LOC City); Mexico (GVG); Young GinoJ Rock (Lil4Mobb); Bart (Lil4Mobb); DB (Hoola Gang); Johno (Hoola Gang); Polo (Hoola Gang) | Blake (LOC City); Keno (LOC City) |
| D Boi |  | Gangster Disciple |  | Y | Jeff (LOC City) | Lil E (LOC City); Slamma (LOC City); Damo (LOC City); HB (LOC City); Kiwi (LOC City); Baby (LOC City); Mechie Mac (LOC City); Tony (LOC City); Darius (LOC City); Denny (SluttyBoyz) |  |
| Dmacc |  | Gangster Disciple |  | Y |  |  | Jonathan (LOC City); Deon (LOC City) |
| Gullie Gibson |  | Gangster Disciple |  | Y | Slutty (West End); Pig (SluttyBoyz) |  |  |
| Lil Dutty aussi connu sous le nom de «DuttyDoThaDash» | DuttyDoThaDash | Gangster Disciple | Y |  |  | Money (GoonBlock); King Ty (LOC City); Monte (LOC City); Ken Ben (LOC City); Kuda (600); Chuck (Marshall Field MCs); Lil Loui (SedVille); Chuck (SedVille); Roe (GVG); Jango (Hoola Gang) | Lil E (LOC City); PookMan (Marshall Field MCs); Keno (LOC City) |
| Lil $hawn aussi connu sous le nom de «Shotta» | Shotta | Gangster Disciple |  | Y | Marcus (LOC City); Von (Killaward 078); InnocentV12 (LOC City) | C-Money (LOC City); Keno (LOC City); IgNate (LOC City); E-Man (LOC City); King Ty (LOC City); Munchie (LOC City); KD (LOC City); Mondo (LOC City); Hot Rod (LOC City); Half Mil (GVG); Ahunna Stacks (GVG); Ray (TBG); PJ (Lil4Mobb); Bae Bae (Lil4Mobb) |  |
| Magic City connu aussi sous le nom de «Big Magic» | Big Magic, City | Gangster Disciple |  | Y | Alex (LOC City); Jonathan (LOC City); Bleek (Slutty Boyz) | Tommy (SluttyBoyz); DueceDuece (SluttyBoyz); BB (SluttyBoyz); Bird Man (LOC City); IgNate (LOC City); Bad Luck (LOC City); Joe Crack (LOC City); Ice Man (LOC City); King Ty (LOC City); V12 (LOC City); Baby (LOC City); B.Lord (LOC City); Munchie (LOC City); HB (LOC City); Kane (Uptown Lawds); JuneBug (Buck Town); Lil Sam (Lil4Mobb) | Blake (LOC City); Keno (LOC City); Munchie (LOC City) |
| Mosey aussi connu sous le nom de «Mosey Duece» | Mosey Duece, Mosey World | Gangster Disciple | Y |  | Keno (LOC City) | Lil Josh (LOC City); Neil (LOC City); Rap (LOC City); MurdaMan (LOC City); V12 (LOC City); Lil Duke (GVG) | Munchie (LOC City) |
| Kemo aussi connu sous le nom de «NotThaBopper» | NotThaBopper | Gangster Disciple |  |  | EJ (Lil4Mobb); Keon (LOC City) | Derrick (LOC City); Tony (LOC City); Corkey (LOC City); Baby (LOC City); Huncho (LOC City); Prince Shorty (Lil4Mobb); Lil Sam (Lil4Mobb); Tyrese (Lil4Mobb); Cole (Lil4Mobb); Big Mike (GVG) | Terry (Lil4Mobb) |
| Lucci |  | Gangster Disciple |  |  | Vonny Mac (LOC City) |  |  |
| Spazz |  | Gangster Disciple |  | Y | Blake (LOC City); AJ (LOC City) | IceMan (LOC City); Tank Savage (LOC City); IgNate (LOC City); O Dog (LOC City); Slamma (LOC City); Trell (LOC City); Huncho (LOC City); Joe Crack (Get Rich); Chubbz (Get Rich); JuJu (Lil4Mobb); Lil Duke (GVG); ToolyMan (GVG) |  |
| Pooh Bear |  | Gangster Disciple | Y |  | Michael (TaeTown); ? (TaeTown) |  |  |
| ShottyGoCrazy |  | Gangster Disciple |  | Y |  |  | Vonny (LOC City) |
| Young Pappy connu aussi sous le nom de « 2Pap » | 2Pap | Gangster Disciple | Y |  |  | C-Money (LOC City); Mechie Mac (LOC City); Lucky (LOC City); Munchie (LOC City); Stevon (LOC City); Nooni (LOC City); PJ (Lil4Mobb); Tune (Lil4Mobb); Jermaine (Lil4Mobb); G-Ball (GVG); Lil Duke (GVG) | Teezy (Lil4Mobb) |
| Dooney Mac |  | Gangster Disciple |  |  |  | Lil Dula (Lil4Mobb); Cole (Lil4Mobb); Young Gino (GVG); Chelo (GVG); Del (GVG); Gucci (TBG); Ice Man (LOC City); V12 (LOC City); BA (LOC City); Toolie (Hoola Gang); Twin (Hoola Gang); Lil Ride (Hoola Gang) | Byro (GVG) |
| Larro Mac |  | Gangster Disciple |  |  | ??? (???) | Tune (Lil4Mobb); Craig (Lil4Mobb); Jermaine (Lil4Mobb); Meechoe (Lil4Mobb); Deally Mac (Lil4Mobb); Ahunna Stacks (GVG); Chump (Uptown Lawds); A-Lord (Uptown Lawds); Tylo (LOC City); Dinero (TBG); Bald Head (TBG) |  |
| Gino Macc |  | Gangster Disciple |  | Y |  | Dre Day (GVG); CEO (GVG); Tali (TBG); Tony Montana (TBG); Kold Kash (Uptown lawds); Bart (Lil4Mobb); Jermaine (Lil4Mobb) | Byro (GVG) |
| Dre Day |  | Gangster Disciple |  | Y | Ivan (Winthrop Latin Kings) |  |  |
| DonDon |  | Gangster Disciple |  |  | Cease (Uptown Lawds) | HardBody (GVG); Half Mil (GVG); Lil G (GVG); Darcy (GVG); EJ (Lil4Mobb); Ray (TBG); Bald Head (TBG) | DayDay (GVG) |
| Devon |  | Gangster Disciple |  | Y | Shandel (Hazel Mobb); Tommy (Adam Street); Belmont (Hazel Mobb) |  |  |
| Spud |  | Gangster Disciple |  |  |  |  | Byro (GVG); Keon (LOC City) |
| Clam | LetItBlam | Gangster Disciple |  | Y |  | D-Lo (Lil4Mobb); Mondo (LOC City); Lucky (LOC City); Slamma (LOC City); C-Dre (TBG); Darcy (GVG) |  |
| Trav |  | Gangster Disciple |  |  |  |  |  |
| D-Mac |  | Gangster Disciple |  | Y |  | Monte (LOC City); Tank Savage (LOC City); Lil Josh (LOC City); Dave (LOC City); Tylo (LOC City); Jeezy (SluttyBoyz); DMac (SluttyBoyz); BugUp (Lil4Mobb); Lil Duke (GVG); Mikey (GVG) | Jonathan (LOC City); Keno (LOC City) |
| Diddy | Puffy | Gangster Disciple |  |  |  | Mondo (LOC City); DoeBoy (LOC City); EJ (Lil4Mobb); Roger (Pottawaime Park Latin Kings) |  |
| E.O |  | Gangster Disciple |  |  |  |  | Blake Tha Snake (SluttyBoyz) |
| Fil Tha Deal |  | Gangster Disciple |  | Y |  | Curtis (SluttyBoyz); HB (LOC City); V12 (LOC City); Rap (LOC City) | Keith (Church Street) |
| Lil DJ |  | Gangster Disciple |  |  | Murda (SluttyBoyz) | Blake (LOC City); Baby (LOC City); Zay (LOC City); KD (LOC City); Dre Day (LOC City); King Ty (LOC City); Sconny (Lil4Mobb); Broom (Lil4Mobb); James (GVG) |  |
| ManMan | Freedom | Gangster Disciple |  |  |  | Lil Tut (Lil4Mobb); Nunu (Lil4Mobb); Pooh (Lil4Mobb); 2Liter (Lil4Mobb); Nathan (Lil4Mobb) | Duski (Hoola Gang) |
| MK | Lil Mike |  |  |  |  | Dean (LOC City); Boss Fredo (LOC City); Lil JayJay (LOC City); Remus (LOC City); C-Money (LOC City) |  |
| Pep |  | Gangster Disciple |  |  |  | EBE Bandz (GME/EBE); Munchie (LOC City) |  |
| Stevo |  | Gangster Disciple |  |  |  |  | Duski (Hoola Gang) |
| Streets |  | Gangster Disciple |  |  |  | Neil (LOC City); Mondo (LOC City); Barshae (LOC City); LJ (LOC City); Keno (LOC City); O Dog (LOC City); Trell (LOC City); Mexico (GVG); Dirty Redd (AMC) |  |
| Henno |  | Gangster Disciple | Y |  |  | Skone (GVG); Dough (GVG) |  |
| KayNine |  | Gangster Disciple |  | Y |  | Shaw (TBG); Judas (Uptown Lawds); Uno (GVG); Coppo (GVG) | ??? (???) |
| Midnite |  | Gangster Disciple | Y |  |  | Ado (Lil4Mobb); Deally Mac (Lil4Mobb); Red (Lil4Mobb); Swilla (Lil4Mobb); G Pops (LOC City); Keon (LOC City); Jezzel (TBG); Coppo (GVG) |  |

### POCKETTOWN

`https://privedatabase.wordpress.com/pockettown-2/` · page 7930 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Also known as:** Corey Town
- **Allies:** KTSMB
- **Enemies:** _none_
- **Notes:** Considered a legendary set for having bodies on random sets.

- **Members listed:** Lil Les est un Gangster Disciple. Il est actuellement incarcéré pour fusillade après avoir pris sur lui les charges de ses membres. Il est le frère de Rico et Rio G. Il est aussi le cousin de Big Swirl du Risky Road et de RondoNumba9 de la 600.

- **Bodies attributed to the set:** Jarvis (ABM/COB), Terrance (Sirconn City Gangsters), Julian (Sirconn City Gangsters), Tiger (Jaro City), Damion (Sirconn City Gangsters), Hitz (Hitzsquad), Mak (Roc Creek), Stanford (Sirconn City Gangsters), Ian (Sirconn City Gangsters), Nahari (Lamron), Raymond (Sirconn City Gangsters), Carlos (Sirconn City Gangsters), Steven (Sirconn City Gangsters), Roger (Sirconn City Gangsters), Tony (NoLimit 083), Jip (Out7aw City), Chris (8×13), RaRa (Sirconn City Gangsters), Mick (Boco Hood), L.C. (Sirconn City Gangsters), A-Dogg (Out7aw City), Dominique (400E Murda Drive), Jon Jon (8×13), Sutton (Sirconn City Gangsters), Lil Ant (Sirconn City Gangsters), Lil E (Sirconn City Gangsters), Dro (Murder Town), ??? (?), ??? (?), Lil Mick (Sirconn City Gangsters), Vert (Sirconn City Gangsters, tué en 2019), Butta (Gotti World), Lil Eric (Sirconn City Gangsters), Wop (HadiWay)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Jarvis (ABM/COB)Terrance (Sirconn City Gangster)Julian (Sirc |  |  |  |  |  | Big Los (NLMB) |  |
| Rico |  | Gangster Disciple |  | Y | Tiger (Jaro City); Damion (Sirconn City Gangsters) |  | Jarvis (ABM/COB) |
| Ronnie Moe |  | Gangster Disciple | Y |  | L.C. (Sirconn City Gangsters) | Jody Boi (Sirconn City Gangsters); Lil Darro (Sirconn City Gangsters); Jimmy-D (Sirconn City Gangsters); Montana (Sirconn City Gangsters); Boday (Sirconn City Gangsters); 30 Clipz (NLMB); Joc (NLMB) | John'O (Sirconn City Gangsters) |
| King Rico |  | Gangster Disciple |  | Y | ??? (?) |  |  |
| Big Meech |  | Gangster Disciple |  | Y | ??? (?) |  |  |
| Spook |  | Gangster Disciple |  |  | Lil Eric (Sirconn City Gangsters); Butta (Gotti World) |  | Fearro (Sirconn City Gangsters) |
| Lil Mike |  | Gangster Disciple |  |  | Wop (HadiWay) |  |  |
| 5ive (frère de Lil Ant et de 051 Young Money Zeko)Boss Gee ( |  |  | Y |  |  |  |  |

### POTTBLOCK

`https://privedatabase.wordpress.com/pottblock-2/` · page 7970 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Traveling Vice Lords
- **Also known as:** NoonieBlock, QuanWorld
- **Allies:** Slutty Boyz, LOC City, Clark Latin Kings, IBM, TBG, Lil4Mobb, GVG
- **Enemies:** StoneVille, TaeTown, ABM, PBG, TFG, HoolaGang, SK

- **Members listed:** Noonie était un Traveling Vice Lord. Il est décédé. Le PottBlock, l'IBM et le LOC City représentent tous les 3 le “NoonieBlock“.

- **Bodies attributed to the set:** Ray Ray (TaeTown), Yakez (TaeTown), Falon (StoneVille), Rari (StoneVille), White Boi (ABM), Steve (ABM), Puddin (OTG)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Lil Ace (TaeTown) |  |  |  |  |  |  |  |
| TayyLil DJ SavageZayCapMeloTimAdamAntwanDreboWooskie WooRico |  |  | Y |  |  |  |  |

### PSYCHO GANG

`https://privedatabase.wordpress.com/psycho-gang-2/` · page 7996 · FCK HEAD$HOT · 2020-02-05

- **Members listed:** Marlo était un Black P.Stone. Il est décédé. Il avait 15 ans. Marlo se fait tirer dessus à 7 reprises en 2020 puis se fait tabasser à mort. Il décède à l'hôpital.

### Ray Bands

`https://privedatabase.wordpress.com/ray-bands/` · page 4047 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Boss Court (Lamron)Darren (FollyBoyz)G Mouma (FollyBoyz)Otto |  |  |  |  |  |  |  |

### Raysko

`https://privedatabase.wordpress.com/raysko/` · page 3880 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Big Lonnie (051 Young Money) |  |  |  |  |  | YC Da Problem (50 Strong); Tonio (No Luv City) |  |

### REC CITY

`https://privedatabase.wordpress.com/rec-city-2/` · page 6666 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Also known as:** Tae Block
- **Allies:** _none_
- **Enemies:** _none_

- **Members listed:** 2.4BD MarcusBGBooDerrickGGInner TubeKevoKiwiLil JuanPoochieStank

### RISKY ROAD

`https://privedatabase.wordpress.com/risky-road-2/` · page 7946 · FCK HEAD$HOT · 2020-01-26

- **Nations:** 4 Corner Hustlers
- **Also known as:** Lick Squad
- **Allies:** 600
- **Enemies:** _none_
- **Notes:** Big Swirl, brother of RondoNumba9 from the 600, is a member of this set.

- **Members listed:** Big Swirl (frère de RondoNumba9 de la 600 et cousin de Rio G du KTS et Lil Les du PocketTown), BT (décédé), Lil Risky (décédé), Dre MoeMackey (décédé), JohnC3HunchoReese ReesePuncho (décédé), Churron (décédé), DoskiReese (décédé, tué en 2019)

### RMG

`https://privedatabase.wordpress.com/rmg-2/` · page 7985 · FCK HEAD$HOT · 2020-01-30

- **Nations:** Black Disciples
- **Allies:** YKN, JayloGang, TrayTown, Doggpound, G-Block
- **Enemies:** G-Ville, MayBlock, NewMoney, CuttaGang, JamariWorld

- **Members listed:** Lil G (décédé)

### ROC CREEK

`https://privedatabase.wordpress.com/roc-creek-3/` · page 7896 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Gangster Disciples
- **Allies:** Dro City
- **Enemies:** CrankTown, 800, Stony Spot, TYMB
- **Notes:** Based in Woodlawn.

- **Members listed:** Do HooMac (décédé), Ole ManVic (décédé), Scoot Boot (décédé), Hollow (décédé), Jay (décédé), OG Pat (décédé), Tookie (décédé), Renauld (décédé), Papa (décédé), Skinz (décédé), Fish (décédé)

- **Bodies attributed to the set:** Tommie (CrankTown), Damien (800), Diddy (CrankTown), MG (CrankTown), Cmac (Stony Spot), Gio (Stony Spot), DreMoe (Stony Spot), Old Head (800), Bone (CrankTown), Kush (TYMB)

### SACKBOYZ

`https://privedatabase.wordpress.com/sackboyz-2/` · page 7973 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Traveling Vice Lords
- **Also known as:** CrankTown, Stro Gang, TTU, FSG, 0725
- **Allies:** _none_
- **Enemies:** LT, SedVille, Marshfield MCs, Bejian Gang

- **Members listed:** MalikRegjoCelloCrank (décédé), Rich RichMalikBossMan LoKilla LordKing Neal (décédé), Dfoe JoeMoJo (décédé), Bear (décédé), Tay TayYangMainskiJoshClumpsTonyKMillzDayDay (décédé), CuzinLil DavStro (décédé), Chief SoReggie LordGloMikeMikeCoffeeBigLil Steve (décédé), WopT-BubbyChaseFatLordStupid DevoDrewFat Shordy (décédé), Chris BudWeenieTrayManMoneyBaggGreJosephRoyal B.DevonTellzScoShawnTony (décédé), JJBoss FendiLil RoTrell (décédé), MigoSantanaTeTe (décédé)

- **Bodies attributed to the set:** Kiddo (LT), Spook (LT), Bejian (LT), Royce (Bejian Gang), Weezy (Bejian Gang), Kenny C (SedVille), Killa (SedVille), Jamal (Marshfield MCs), Meji (Marshfield MCs)

### Scrap

`https://privedatabase.wordpress.com/scrap/` · page 3882 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Dougo (50 Strong)Dell (50 Strong) |  |  |  |  |  |  |  |

### SEDVILLE

`https://privedatabase.wordpress.com/sedville-2/` · page 7897 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Conservative Vice Lords, 4 Corner Hustlers
- **Also known as:** TTG, Gucci Gang, BlockCity, 1300, B.O.B, M.O.E, SBK, ThanaWorld, FBG
- **Allies:** TBG, Lil4Mobb, Marshall Fields MCs, GVG, D-Block, BuckTown, YH, IBM, TNG, SickoMobb, LOC City
- **Enemies:** OTE, Sac Boyz, PBG/TFG, SK, OTA, OTS, BH, AMM, E-Way, SuWu Mobb
- **Notes:** Located in the Near North Side; rapper Polo G is a member.

- **Members listed:** Polo GLil FeltonDrillaLil JustoBooMan LordLil LouiLil BlastBig MeechiBubLil FlyDreak HeadL-ChapoRudeBoiiAlLil Rondo#9Quaney ManLuh MurdaKing TayLarry BirdTimTim (décédé), Kei (décédé), Thana (décédé), Block C (décédé), Shoe Diddy (décédé), Ed (décédé), Lil Bit (décédé), Killa (décédé), Jabari (décédé), Man (décédé), J Gutta (décédé), Melvine (décédé), Frame (décédé)

- **Bodies attributed to the set:** Scooby (OTE), Lil Nation (OTE), Mac Man (OTE), Deon (OTE), Milly (OTE), Trap (OTE), G Boogie (OTE), Kobe (OTE), Tunechi (OTE), TJ (OTE), Head (OTE), L Way (OTE), 50 (OTE), Gutta (OTE), Troy (OTE), O-Dog (OTE), Tese (OTE), JayJay (SuWu Mobb), PayDay (SuWu Mobb), Cebo (SuWu Mobb), Harry (SuWu Mobb), Lil Will (SuWu Mobb), MoJo (Sac Boyz), Deebo (Sac Boyz), Stro (Sac Boyz), LeeLee (Sac Boyz), Smooche (Sac Boyz), Elroy (Sac Boyz), Joshua (Sac Boyz), MoJo (Sac Boyz), Lil Steve (Sac Boy), Juicy (Cabrini Green), Daniel (E-Way), Lil Rell (E-Way), Bamo (E-Way), Bookie Moe (OTS), G-Whiz (OTA)

### SHAWN MONEY BOYZ (SMB)

`https://privedatabase.wordpress.com/shawn-money-boyz-smb/` · page 7899 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Black Disciples
- **Allies:** AMG
- **Enemies:** TunechiVille, Brick$quad 069, BlockBurna
- **Notes:** Part of the '300' movement; known for killing rapper Lil Jojo of Brick$quad 069 in 2012.

- **Bodies attributed to the set:** DuJuan (TunechiVille), G-Tania (No Luv City), Hustle (Brick$quad 069), Jeffery (BlockBurna), Demetrius (BlockBurna), Lil Jojo (Brick$quad 069), Bam (GunnHead)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Poo Poo | PooDiddy, FreeWorld Savage | Black Disciple |  |  | DuJuan (TunechiVille); G-Tania (No Luv City); Lil Jojo (Brick$quad 069); Bam (GunnHead) | King Markey (Jaro City); Reese Gezzy (Jaro City); Marlon (No Luv City); BossJay (No Luv City); Brandon (No Luv City); Lil Alien (CMB); Kells (Brick$quad 069); Dez (Brick$quad 069); Charles (Brick$quad 069); J-Real (Brick$quad 069); King Samson (Terror Dome); 2 Shots (Wuga World) | OJ (Jaro City); Lil D (MetBoyz); Dante (Jaro City) |

### SHIELDS

`https://privedatabase.wordpress.com/shields-2/` · page 7927 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Also known as:** RowRow Boyz, Travis World
- **Allies:** No Luv City, Bird Gang
- **Enemies:** Lamron, MoeTown, MOB
- **Former enemies:** SKD, Met Boyz
- **Notes:** Based in Englewood.

- **Members listed:** Antoine est un Gangster Disciple. Il est actuellement incarcéré pour le meurtre de Tayski de Lamron.

- **Bodies attributed to the set:** Tayski (Lamron), Pierre (Lamron), 65 (Lamron), Pay Day (Lamron), Weezy (Lamron), Tece (Lamron), ??? (SKD), ??? (SKD), ??? (SKD), ??? (SKD), TayMoneyBagz (TTE, tué en 2019)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Tayski (Lamron) |  |  |  |  |  |  |  |
| Gucci |  | Gangster Disciple |  | Y | TayMoneyBagz (TTE, tué en 2019) |  |  |
| Vada |  | Gangster Disciple |  | Y | Weezy (Lamron) |  |  |
| Woo (décédé)Migo (décédé)Rusty (décédé)Malachi (décédé)Peanu |  |  | Y |  |  |  |  |

### SIRCONN CITY GANGSTERS

`https://privedatabase.wordpress.com/sirconn-city-gangsters-2/` · page 7905 · FCK HEAD$HOT · 2019-11-21

- **Members listed:** ChinaOMan (décédé), Fearro (décédé), John'O (décédé), Trife (décédé), Dominic (décédé), Mari (décédé), Terrance (décédé), Julian (décédé), Damion (décédé), Stanford (décédé), Ian (décédé), Raymond (décédé), Carlos (décédé), Steven (décédé), Roger (décédé), RaRa (décédé), L.C. (décédé), Sutton (décédé), Lil Ant (décédé), Lil E (décédé), Fearro (décédé), Lil Aaron (décédé), Robert (décédé)

- **Bodies attributed to the set:** Michael (PocketTown), Paris (MooseBlock), Darnell (MooseBlock), Marvin (PocketTown), Andrew (PocketTown), Floyd (PocketTown), Ba Ba (Will City), Xavier (PocketTown), Corey (PocketTown), Clinton (PocketTown), Daryl (MooseBlock), Moose (MooseBlock), Lil Pez (PocketTown), Duwop (PocketTown), Del (Will City), Bud (PocketTown), Tyrone (MooseBlock), Malcolm (Will City), SDub (PocketTown), Cave Man (072 HooverVille), Richie Money (Lakeside), Stanley (PocketTown), Chris (PocketTown), Lil G (PocketTown), LadySha (PocketTown), Lil Gee (PocketTown)

### SK

`https://privedatabase.wordpress.com/sk-2/` · page 7974 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Gangster Disciples, Spanish Gangster Disciples
- **Also known as:** NickoVille, Banks Gang, Boogie Block
- **Allies:** PBG/TFG
- **Enemies:** Homicide Latin Kings, Vice Lords, Latin Eagles

- **Members listed:** G Boogie (décédé), G WetEmUpG StickNicko (décédé), Kenny MacSIXTay GoonieDTGSmokieKuwopGreenyHunchoKyroBrianLil Alex (décédé), DrewG LuckGuawpShaunBanks (décédé), ChechoGabrielDee KodakG SlimeA RokCK (décédé), Lil HatchMalekNathanGage (décédé), Marc (décédé), Joey PSabatsAntonioJulioBuild (décédé)

- **Bodies attributed to the set:** Timothy (Homicide LKs), Sergio (Homicide LKs), Baby J Boy (Homicide LKs), Lil Ant (Homicide LKs), Gizmo (Homicide LKs), Seth (Homicide LKs), RahRah (Vice Lords), E Dot (Vice Lords), Lean (Vice Lords), June (Latin Eagles)

### SKEEZE WORLD

`https://privedatabase.wordpress.com/skeeze-world-2/` · page 7931 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Rappers King Yella and Drake of Chiraq are members; based in West Englewood.

- **Members listed:** King YellaDrake of ChiraqLil MoeJinoSkeeze (décédé), Vonte RichDevon (décédé), King Geno (décédé)

### SLUTTY BOYZ

`https://privedatabase.wordpress.com/slutty-boyz-2/` · page 7969 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Gangster Disciples
- **Also known as:** SBMG, MurdaGang, TayTown, PigWorld, D-Block
- **Allies:** _none_
- **Enemies:** PBG, ABM, TaeTown

- **Members listed:** ShakeyDMacTuckGameHair CutLuca BrasiWeezeGaryKeemoBDDollaWickRickyTommyBBD MoneyJeezyDoodaGold MouthKevinRichie RichChrisCobiTuneOhhgeeJizzoMaulySlutty (décédé), Tay (décédé), Pig (décédé), Murda (décédé), Bleek (décédé), Baby G (décédé), Wayne (décédé), TomTom (décédé), CrayCray (décédé), Dontae (décédé)

- **Bodies attributed to the set:** Mangul (ICG), Lil Big Man (PBG), Birdie (ABM), Pat (South End), Too Tall (TaeTown), Tony (ABM), Lil Greg (ABM), Star Boa (ABM), Osama (ABM)

### Smalls

`https://privedatabase.wordpress.com/smalls/` · page 3883 · FCK HEAD$HOT · 2020-04-22

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Bankroll Q (051 Young Money) |  |  |  |  |  | Duke (No Luv City); Gunplay (No Luv City); G Rasto (No Luv City); Izzy (No Luv City); Quack (Dumpstreet); Law (051 Young Money) |  |

### SMASHVILLE

`https://privedatabase.wordpress.com/smashville-2/` · page 7987 · FCK HEAD$HOT · 2020-01-30

- **Nations:** Gangster Disciples
- **Allies:** SDub, PA, ABM, SMB, 87th Cutthroat
- **Enemies:** Terror Dome, QuietMoney, G-Ville, Foster Park, DuckTown, MachetteVille, CrossAshland

- **Members listed:** CJ est un Gangster Disciple.

- **Bodies attributed to the set:** Glenn (New Money 080 KillaWard)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Glenn (New Money 080 KillaWard) |  |  |  |  |  |  |  |
| Ty (décédé)Pat (décédé) Mello (décédé) Jay (décédé) Nuk (déc |  |  | Y |  |  |  |  |

### Snap D

`https://privedatabase.wordpress.com/snap-d/` · page 1187 · FCK HEAD$HOT · 2020-03-28

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Brian Thomas (MurderVille) |  |  |  |  |  | Antonio McGee (MurderVille) |  |
| RÉSUMÉ DU JUGEMENT DE SNAP D: Jugement de Snap D |  |  |  |  |  |  |  |

### SOUTH KING DRIVE (SKD)

`https://privedatabase.wordpress.com/south-king-drive-skd/` · page 7928 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Gangster Disciples
- **Allies:** Geo Drive, MetBoyz, Von World, MOB
- **Enemies:** _none_
- **Notes:** SKD is short for South King Drive.

- **Members listed:** JaydDon DollarsBooda (décédé), Q OriginalHell Vell (décédé), Nick NittiG RellMeechiBig OppGeo (décédé), BittaShawty RedMulaBlack Boy (décédé), ScooterBustaDala LosoTelly (décédée), BroskyYattaTwilla (décédé), BDoubleMizzy (décédé)

### SQUIRTTOWN

`https://privedatabase.wordpress.com/squirttown-2/` · page 7898 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Gangster Disciples, Black Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Former allies:** Front$treet
- **Notes:** No longer active; today the set exists only to honor its deceased members.

- **Members listed:** Squirt (décédé), Jizzle (décédé, il représentait aussi la Brick City), Curt (décédé), Black Boy (décédé), BJ (décédé), Slo-Folkz (décédé), Corey (décédé)

### Stello

`https://privedatabase.wordpress.com/stello/` · page 4750 · FCK HEAD$HOT · 2020-05-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Hottie (Jaro City)MoeJoe (ChiefTown)Lil Scrapp (MOB) |  |  |  |  |  | 305 (Jaro City); Blocks (Jaro City); Krump (MuBu) |  |

### STL/EBT

`https://privedatabase.wordpress.com/stl-ebt/` · page 242 · FCK HEAD$HOT · 2020-03-26

- **Members listed:** BGSkoK.I. (décédée), WeeWeeSo IceyLil DonLil B (décédé), TakiDrizzyChickenFBG Brick (décédé), BossTrell (décédé), FBG YoungWooskiTooka (décédé), King Lil JayButtaDutchieFBG DuckManny FreshCray CrayCheChoC-BallFBG CashCantGetRight (décédé), BlinkBillionaire BlackBig DeeCelloDale (décédé), Day DayDieselDoc (décédé), Fay FayFlameJialeJyronKing ColeLil PLuckyMeechieModell (décédé), MoonHeadMr.HotSauce (décédé), NaroPharoahRastaRicoRoRoTy (décédé), SpoonVonnaWaldoZoe (décédé), Keonte (décédé), Marcus (décédé), Carl (décédé), Michael (décédé), Robert (décédé), Lil Arron (décédé)

- **Bodies attributed to the set:** Ty (TYMB), Jimmie (TYMB), Larry (TYMB), Lee (TYMB), Solomon (TYMB), Lil Chris (TYMB), Rozelle (TYMB), Ray (TYMB), Lil James (TYMB), Fella (WIIIC City), Reezy (WIIIC City), Odee (WIIIC City), D-Thang (600), Patoon (O'Block), Sheroid (O'Block), J-Money (O'Block), Sam (O'Block), HK (O'Block), Jawan (Chris World), Moe (Tyquan World), Rico (Nicko Gang), Valentino (Nicko Gang), Copo (Will City), Levonne (RMG), True (Zone7), Juicy (MetLife), P-Nut (Saint World)

### STL/EBT

`https://privedatabase.wordpress.com/stl-ebt-2/` · page 7484 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Gangster Disciples
- **Allies:** Jaro City, Tyquan World, DDG, 757, 051 Young Money, MOB, E-Block, SkeezeWorld, IMM, PBG/TFG, OTE
- **Enemies:** O'Block, TYMB, Chris World, Nicko Gang, 400E Murda Drive, 600, MME, NLMB, Will City, Zone7, Lamron, Front$treet
- **Notes:** STL (Saint Lawrence) and EBT (Eberhart) merged into one set, based in Woodlawn.

- **Bodies attributed to the set:** Ty (YMB), Jimmie (TYMB), Larry (TYMB), Lee (TYMB), Solomon (TYMB), Lil Chris (TYMB), Rozelle (TYMB), Ray (TYMB), Lil James (TYMB, tué en 2018), Fella (WIIIC City), Reezy (WIIIC City), Odee (WIIIC City), Patoon (O'Block), Sheroid (O'Block), J-Money (O'Block), Sam (O'Block), HK (O'Block, tué en 2017), Jawan (Chris World), Moe (Tyquan World), Rico (Nicko Gang), Valentino (Nicko Gang), Copo (Will City), Levonne (RMG), True (Zone7), Juicy (MetLife)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Billionaire Black | Clout Lord, #4 | Gangster Disciple |  |  |  | Lil Marc (051 Young Money) |  |
| Blink |  | Gangster Disciple |  | Y | Fella (WIIIC City) | Solo Dolo (TYMB); Manny (TYMB); Renzo (TYMB); Donnell (TYMB); Gyroskie (TYMB); Gutta (TYMB) | Larry (TYMB) |
| CantGetRight | ManMan | Gangster Disciple | Y |  | Rico (Nicko Gang); Valentino (Nicko Gang); Sam (O'Block); Big A (O'Block) | Dookie (TYMB); King Doda (TYMB); FaceSixO (600); Manny (600); Quono (Front$treet); Block Poppa (Front$treet); Man (O'Block); Lil Gooch (O'Block); Woo Thang (DukeSquad) | LA (MetLife) |
| FBG Cash |  | Gangster Disciple |  |  |  | Lil C (TYMB); Mechie Boy (TYMB); King Von (O'Block); Tway (O'Block); Lil Allan (O'Block) |  |
| C-Ball |  | Gangster Disciple |  | Y | Larry (TYMB) | Face (TYMB); Jaw (TYMB); Obama (TYMB); Kush (TYMB); Manny (TYMB); Little (TYMB); Suge (TYMB); Maine Thang (TYMB); Kenny Mac (Chris World); Dizzle (O'Block); Willie (O'Block) | Ty (TYB) |
| CheCho |  | Gangster Disciple |  | Y |  | Nuke (TYMB); Quetin (TYMB); Timbo (TYMB); Cortney (TYMB); Cord (TYMB); Odee (WIIIC City); BossTop (O'Block); Slick (O'Block) | Stanley (TYMB) |
| Cray Cray | Crasillio | Gangster Disciple |  |  |  | Boss Shawn (TYMB); Vontay (TYMB); Migo (TYMB); Big Dre (TYMB); Duke (TYMB) | Solomon (TYMB) |
| Manny Fresh | Ty | Gangster Disciple |  |  | Moe (Tyquan World); Lil James (TYMB, tué en 2018) |  |  |
| FBG Duck, connu aussi sous le nom de «Big Clout» et «#3» | Big Clout, #3 | Gangster Disciple |  |  |  | MoneyMan (TYMB); Little (TYMB); Phat B (TYMB); Demo (TYMB); Air Kelso (TYMB); Jr (TYMB); Wooda (Chris World); Edai (600); Tay600 (600); Booka (600); Lil Reese (Lamron); BossTop (O'Block); T-Roy (O'Block); Young (O'Block, après la mort de FBG Brick); Bre (O'Block, après la mort de FBG Brick) | Odee (WIIIC City) |
| Dutchie | #2, DJ | Gangster Disciple |  |  | Juicy (MetLife) | Jhari (TYMB); King Zo (TYMB); Drillie (TYMB); MoneyMan (TYMB); Big J (Chris World); Wooda (Chris World); T-Roy (O'Block); Delo (O'Block) | Jizzle (SquirtTown); Odee (WIIIC City); Sheroid (O'Block); Jawan (Chris World) |
| Butta | #26, Tunechi | Gangster Disciple |  |  | Copo (Will City) | Drillie (TYMB); Peevan (TYMB); Chief Keef (O'Block/Front$treet); GBE Capo (Front$treet); DJ Kenn (Front$treet); Lil $avage (Front$treet); Doowop (NLMB); T-Roy (O'Block); BJ (O'Block); KD (O'Block); J-Money (O'Block); Odie (O'Block); Trey (O'Block); BooMan (GeoDrive); Memo600 (600); BossMoo (60); Abo (800); Big Mike (800); Jtay (MME, il a essayé de venger Lil Jeff); BD Rick (WillCity); Freaky (Brick$quad 069); J Da Kidd (MitchBlock) | Odee (WIIIC City); Jizzle (SquirtTown); Johnny (Chris World) |
| King Lil Jay | #00, Clout Lord, WTO | Gangster Disciple |  | Y |  | Snika Bar (TYMB); Dion (TYMB); Tay600 (600); Boowop (600); Boowop (600); 600Breezy (600); BallOut (Lamron); Day Day (Lamron); Wudae (Lamron); T-Roy (O'Block); OTF Ikey (O'Block); BossTop (O'Block); Smuk (Front$treet); Doowop (NLMB); Lil Pink (PNP, set de filles); Jadah (PNP, set de filles); Rocko (051 Young Money); Yonnie (MME, il a tenté de venger Lil Jeff); J Da Kidd (MitchBlock); Freaky (Brick$quad 069); BD Rick (Will City) | Levonne (RMG); Odee (WIIIC City) |
| Tooka | fumer sur un ennemi mort, fumant sur Lil Moe, Ty et Lil Chris, Man Down | Gangster Disciple | Y |  |  | Vontay (TYMB); Peevan (TYMB); Cortney (TYMB); Lil Moe (Lamron) |  |
| Wooski | WoopWoop, King Opp, B.O.N. | Gangster Disciple |  |  | Reezy (WIIIC City); Patoon (O'Block); HK (O'Block) | Zero (TYMB); Kecey (TYMB); Donnell (TYMB); Molly (TYMB); Rayski (TYMB); Delo (O'Block); T-Roy (O'Block); Prince Dre (O'Block); King Von (O'Block); KD (O'Block); Boobie (O'Block); Young (O'Block); Muwop (O'Block); Gleesh (O'Block); Louie (O'Block); Duke (O'Block); DQ (O'Block); Muwop (O'Block); DQ (O'Block); E-Dogg (O'Block); Boss Money (O'Block); C-Bang (O'Block); DQ (O'Block); Quawn (MetLife); Lil Matt (DOD); M-Thang (600); Memo600 (600); Makado (600); Porkey (600); CapFck12 (600); Nino (Front$treet); Shawn (Front$treet); Steve (Lamron); Lil Dirk (400E Murda Drive); Johnny Dang (400E Murda Drive); Quan (400E Murda Drive); Magurt (Doggpound); Famous (BlackGate); Cortez (BuckTown); G-Curry (MurdaTown) | Odee (WIIIC City); White White (O'Block); Dudity (Doggpound); Darius (Evans Mobb) |
| FBG Young | Mello, #1 | Gangster Disciple |  |  |  | Lil Prince (800) | Odee (WIIIC City) |
| BossTrell | BT | Gangster Disciple | Y |  | D-Thang (600); Sheroid (O'Block); Jawan (TYMB); Juicy (MetLife) | Jitta (TYMB); Kush (TYMB); Cortize (TYMB); Lil Chris (TYMB); Maine Thang (TYMB); Obama (TYMB); 600Breezy (600); Stello (600); AK (Brick City/600); L'A Capone (600); Tay600 (600); C-Murda (O'Block); B-Mike (O'Block); Scotty (O'Block); Shauno (O'Block); T-Slick (Front$treet); Rude Boi (NLMB) | Ray (TYMB) |
| FBG Brick | #30 | Black Disciple | Y |  |  | Jhari (TYMB); Ro Ro (TYMB); Meechie Boy (TYMB); Big Lo (WIIIC City); Odee (WIIIC City); C-Murda (O'Block); Duke (O'Block); T-Roy (O'Block); Prince Dre (O'Block); King Von (O'Block); Marcus (O'Block); Casper (O'Block); Lil Khori (O'Block); T-Man (O'Block); Quawn (MetLife); 600Breezy (600); Booka (600); Memo600 (600); Lil JB (Nicko Gang); Meechy (Front$treet); Pat (NLMB, il lui a tiré dessus 15 fois mais Pat a survécu) | Odee (WIIIC City); Sheroid (O'Block); Patoon (O'Block); Big A (O'Block); T-Roy (O'Block) |
| Chicken | Big Chick | Gangster Disciple |  | Y | Ty (YMB); Lee (TYMB) | Ivery (TYMB); Trell (TYMB); Dookie (TYMB); Jaw (TYMB); Bohon (TYMB); Ray Rilla (O'Block); J-Money (O'Block) | Jimmie (TYMB) |
| Drizzy |  | Gangster Disciple |  | Y |  | Donnell (TYMB); Zero (TYMB); Boss Town (TYMB); Air Kelso (TYMB); Boss Money (O'Block); Prince Dre (O'Block); Scudd (O'Block) | Reezy (WIIIC City) |
| Lil B |  | Black Disciple | Y |  | Levonne (RMG); Johnny (Chris World); J-Money (O'Block) | Snika Bar (TYMB); MoneyMan (TYMB); Ro Ro (TYMB); Outlaw (TYMB); Lil C (TYMB); Dion (TYMB); Joey (O'Block); Carlito (O'Block); Big Boss (Chris World); Smooth (Chris World); D.Rose (600); Inky D (600); TeTe (Zone7) | Ray (TYMB) |
| Lil Don |  | Gangster Disciple |  | Y |  | Nico (TYMB); Boss Twon (TYMB); EBK Glock (TYMB); Air Kelso (TYMB); Mike (TYMB) | Lil Chris (TYMB) |
| So Icey |  | Gangster Disciple |  |  | Solomon (TYMB); True (Zone7); Ray (TYMB) | Manny (TYMB); Trell (TYMB); Migo (TYMB); Vontay (TYMB); Phat B (TYMB); Cortney (TYMB); Jitta (TYMB); Lil C (TYMB); BossTop (O'Block); Trey5 (O'Block); Slick (O'Block); Boobie (O'Block); Bruh Bruh (O'Block/THF46); Lil Jalen (DOD); King Black (Zone7); King Kevin (SMB); Bart (SmashVille); Big Trell (Dro City) | Reezy (WIIIC City) |
| Taki |  | Gangster Disciple |  | Y | Jimmie (TYMB); Jerromey (German Church Road); Devon (German Church Road); Shawnice (German Church Road) | Quetin (TYMB); Kelz (TYMB); Thump (TYMB); Obama (TYMB); Kecey (TYMB) | TY (YMB) |
| WeeWee | Weezy | Gangster Disciple |  | Y | Lil Chris (TYMB) | Kelz (TYMB); Cord (TYMB); Jaw (TYMB); Nuke (TYMB); Timbo (TYMB); Big Dre (TYMB); Jamoe (TYMB); Bohon (TYMB) | Lee (TYMB) |
| K.I | Snoop, Tyquan | Gangster Disciple | Y |  | Odee (WIIIC City); Innocent (O'Block); Dealer de drogue (Chicago) | Lil C (TYMB); E-Dogg (O'Block); King Von (O'Block); Travis (O'Block); T-Roy (O'Block); Sharona (O'Block); Big A (O'Block); Scudd (O'Block); Ronn Taylor (O'Block); D.Rose (600); Makado (600); S.Dot (600); Rickey (Chris World); Law (DOD); Boss Smooth (800); Wonno (800); Big Mike (800); Oshay (Whiz City); Pig (GeoDrive); Salo (Lamron) | Jizzle (SquirtTown); Sheroid (O'Block); Patoon (O'Block); Juicy (MetLife); J-Money (O'Block); Blood Money (Front$treet) |
| BG |  | Gangster Disciple |  | Y |  |  | Ty (YMB) |
| Sko |  | Gangster Disciple |  |  | Jaydo (O'Block) |  |  |

### STONY SPOT

`https://privedatabase.wordpress.com/stony-spot-2/` · page 7929 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Black P.Stones
- **Allies:** _none_
- **Enemies:** TYMB, Roc Creek, RowLife, D-Town, AAB, O'Block (new generation)
- **Notes:** Based in Woodlawn.

- **Members listed:** BooneFerroGucciJon JonKariiKGMattMeechy (décédé), SonTana MoeTim ThangTwonnCMac (décédé), Gio (décédé), Dre Moe (décédé)

- **Bodies attributed to the set:** Manky (TYMB), Scoot Boot (Roc Creek), Hollow (Roc Creek), Lee (RowLife), DV (D-Town), Jay (Roc Creek), OG Pat (Roc Creek), Tookie (Roc Creek), D-Money (D-Town), JuMoney (AAB)

### SUWU MOBB

`https://privedatabase.wordpress.com/suwu-mobb-2/` · page 7962 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Titanic Stones
- **Allies:** OTS, Stoneville, BuckTown, Sane Gang, SK
- **Enemies:** 1200, OTE, OTA, SedVille, E-Way, AMM, Mafia Murda City
- **Notes:** Located in the Near North Side.

- **Members listed:** Nino BrownLeeTylerDionCJLil FinCubanLil ChrisDukeKay DawgShaadDVDGSwervoSmoovBun BunRellT.OBambinoMouth2 SticksDough BoyTukoDream ChaserBubEscobarKewonFrank NittiTwinNuskiDae DaeSavageLil Harry (décédé), Jay Jay (décédé), Lucky (décédé), Lil E (décédé), Don D (décédé), FIO (décédé), D Nice (décédé), Matt (décédé), Black (décédé), Lil Will (décédé), Cat (décédé), Malachi (décédé), Kam (décédé), Lafee (décédé), Gutta (décédé), Banks (décédé), Floyd (décédé)

- **Bodies attributed to the set:** Lil Ed (1200), Skoonie (1200), Bankroll Juice (1200), Ronnie (1200), Queen Kia (1200), Pat G (1200), Von (1200), Moses Da Po (AMM), Dont Shoot Em (AMM), Joe Buck (OTE), Reese D (OTE), Geo (OTE), Ro-Sko (OTE), Kwa (OTE), Man (SedVille)

### SUWU TTB

`https://privedatabase.wordpress.com/suwu-ttb-2/` · page 7900 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Black P.Stones, Gangster Disciples
- **Allies:** 051 Young Money, Met Boyz, STL/EBT, Jaro City, MuBu, Dro City
- **Enemies:** THF 46, OBN, Welch World, O'Block, 757
- **Notes:** Based in Bronzeville/Oakland; the enmity with the 757 is recent.

- **Bodies attributed to the set:** Lil Tim (Welch World), Darius (OBN), G Gotti (Welch World), Wop (Welch World), Hadiya Pendleton (Innocente)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| TTB Nez | qu'il n'était pas un BD, OTF600 | Gangster Disciple |  |  |  | Funky (Welch World); L'A Capone (600); Jusblow (600); Gucci Da Menace (THF 46); Toine (THF 46); O'Block Ocho (O'Block) | Black (THF 46); Trayvon (THF 46) |
| Smoke |  | Gangster Disciple |  |  |  | G-Alpo (Welch World); Roo (Welch World); Man (Welch World); Moochie (OBN); King Bleek (OBN); TP (THF 46); Richie Jerk (Tyquan World); OnSight (Nicko Gang) |  |

### SWIFT CITY

`https://privedatabase.wordpress.com/swift-city-2/` · page 7984 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Milwaukee Kings
- **Allies:** Koz Park YLOCs, Koz Park Insane Albany, Motherland YLOCs, Sin City YLOCs, Cicero Assassins, Monticello YLOCs
- **Enemies:** Grand City, Mobile and Dickens, Grimy Gang, Belden City, Evil Side Latin Brothers, Death Trap
- **Former allies:** Death Trap

- **Members listed:** Fred Dawg était un Milwaukee King. Il était un haut gradé. Il est décédé.

- **Bodies attributed to the set:** Ratas D (Death Trap), Vato (Death Trap), Crispin (Affilié Death Trap), Rico (Latin Brothers), Bebo (Latin Brothers), Lil Face (Latin Brothers), Lil Jay (Last 4 Corner Hustlers), AK (Belden City), Choco (Belden City), Lil Earz (Belden City), No Good (Simon City Royals), King Chico (Latin Kings), ChiChi (Latin Kings), ElK (C-Note)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Choco (Belden City) |  |  |  |  |  | David (Latin Kings); Cholo D (Death Trap); Peso D (Death Trap) |  |
| Ghost |  |  |  | Y |  | Porkey D (Death Trap); FleeJay (Death Trap); Guero (Belden City) | Crispin (Affilié Death Trap) |
| Lil Hector |  |  |  | Y | Ratas D (Death Trap) | Spooky D (YLOC); Chito 4 (Last 4 Corner Hustlers) |  |
| Guero |  | Latin Kings | Y |  | King Chico (Latin Kings) | Willy (Familia Stones) |  |
| Joseph | Lil Joe |  | Y |  |  | Marco (Death Trap) |  |
| June Bug |  |  | Y |  |  | Shysty B (Latin Brothers) |  |
| King Baby |  |  | Y |  | ChiChi (Latin Kings); ElK (C-Note) | Terror (Latin Kings); Lighting (Latin Kings); Big E (Almighty Latin Eagles); Jose (Almighty Latin Eagles); Dominic (Belden City) |  |
| Mousey |  |  | Y |  |  | Mikey (Last 4 Corner Hustler); OnSight (Belden City) |  |
| Niko |  |  | Y |  |  |  |  |
| Rico |  |  | Y |  |  |  |  |
| Rusty |  |  | Y |  |  |  |  |
| Swift |  |  | Y |  |  | Leo (Death Trap); Lil TT (Death Trap); Flakko (Last 4 Corner Hustlers) |  |
| Trap God |  |  | Y |  |  |  |  |
| Saints |  |  |  | Y | Crispin (Affilié Death Trap) | Damarco (Belden City); LJ (Belden City) |  |
| ??? |  |  |  | Y |  |  |  |
| SilentJBShadowBow WowChilla |  |  |  |  |  |  |  |

### TAETOWN

`https://privedatabase.wordpress.com/taetown-2/` · page 7961 · FCK HEAD$HOT · 2020-01-27

- **Nations:** 4 Corner Hustlers
- **Also known as:** Ace World, JamRock Ville, BMG
- **Allies:** _none_
- **Enemies:** LOC City, Insane Block, SluttyBoyz
- **Notes:** Based in Evanston; formerly called 'South End' before Tae died.

- **Members listed:** Tae (décédé), Lil Ace (décédé), Junior (décédé), Yakez (décédé), Pat (décédé), Dirty (décédé), Dashaun (décédé), RayRay (décédé), TooTall (décédé), Aquan (décédé), JamRock (décédé)

- **Bodies attributed to the set:** Rocket (LOC City), Big Marty (LOC City), Lil Harlem (LOC City), Montana (LOC City), Paul (LOC City), Noonie (PottBlock), Quan (PottBlock), Dashaun (South End), Keith (IBM), Jacob (IBM), Trizzy (IBM), Murda (Slutty Boyz)

### TAY CITY

`https://privedatabase.wordpress.com/tay-city-2/` · page 7901 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Insane Gangster Disciples
- **Allies:** _none_
- **Enemies:** 600
- **Former allies:** 600
- **Notes:** Based in Englewood; was friendly with the 600 through Duke Da Beast and S.Dot's closeness, but turned hostile (became BDK) after Lil Jojo's death.

- **Members listed:** Duke Da Beast (demi-frère de Snowball), Snowball (demi-frère de Duke Da Beast), Baby Stone (décédé), Big E (il joue au basketball à la Shorter University et il est dans une école prestigieuse), Stello BrazyBrett (décédé), Christian (décédé)

- **Bodies attributed to the set:** Travon (DOD), Stank (OBN)

### TEDAMOBB

`https://privedatabase.wordpress.com/tedamobb-2/` · page 7995 · FCK HEAD$HOT · 2020-02-05

- **Nations:** New Breeds
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Rappers Lil Randy and Prince Glo are members.

- **Members listed:** Ed est un New Breed. Il est actuellement incarcéré pour le meurtre de son ami Huncho, du même set.

- **Bodies attributed to the set:** Huncho (TedaMobb)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Huncho (TedaMobb) |  |  |  |  |  |  |  |

### TERROR DOME

`https://privedatabase.wordpress.com/terror-dome/` · page 7924 · FCK HEAD$HOT · 2020-01-25

- **Nations:** Black P.Stones
- **Allies:** G-Ville, BogusBogus (FaceWorld), Foster Park, CrossAshland, DuckTown, MayBlock, QuietMoney
- **Enemies:** Killaward 078, Lamron, SMB, RebLuv, StainCity, SmashVille, 87th Cutthroat, Mike City, 7200

- **Members listed:** Black Moe était un Renegade Gangster Disciple du New Money 080 KillaWard. Il représentait aussi le BBG Terror Dome. Il était le cousin de Boonie Moe du même set (et Lamron)

- **Bodies attributed to the set:** Clifton (Killaward), Ramon (Killaward), Mario (Killaward), Anthony (Killaward), Kevin (Killaward), Cali (Killaward), Geno (Killaward), Cello (Killaward), Tina (Killaward), Hot (Reb Luv), Devone (Killaward), Jaylo (Killaward), Dean (Killaward), Joe Joe (Killaward), Ty (Smashville), Darius (Killaward), Saieed (Smashville), George (CTG), Will (Killaward), Mone (CTG)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Cali (New Money 080 KillaWard) |  |  |  |  |  | ??? (New Money 080 KillaWard) |  |
| Gotti Moe |  | Black P.Stone |  |  | Tina (New Money 080) |  |  |
| T-Time |  | Black P.Stone | Y |  |  |  |  |
| Tez Poe |  | Black P.Stone |  |  |  |  | Tyshawn Lee (enfant de 9 ans) |
| Boone Doty |  | Black P.Stone |  |  | Tyshawn Lee (enfant de 9 ans) | KD (New Money 080 KillaWard) |  |
| BDT (décédé)JoeyKaydoeKing SamsonPeanut (décédé)KevoMo Bodie |  |  | Y |  |  |  |  |

### The God Father

`https://privedatabase.wordpress.com/the-god-father/` · page 4183 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Lil Harvey (Lamron)Anthony (Lamron)Innocente |  |  |  |  |  |  |  |

### THF 44

`https://privedatabase.wordpress.com/thf-44-2/` · page 7902 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Mickey Cobras
- **Allies:** THF 46
- **Enemies:** Princeton Mobb, 051 Young Money
- **Notes:** D.Rose of the 600 has referenced (dissed) them in a song before.

- **Members listed:** DoeBoy est un Mickey Cobra. Il est actuellement incarcéré pour un triple meurtre.

- **Bodies attributed to the set:** Tony (Princeton Mobb), Greg (Princeton Mobb), Vic (Princeton Mobb), Jay (Princeton Mobb), Ant (Princeton Mobb), Tyrone (Princeton Mobb), Ayanna (Princeton Mobb affiliée)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Ayanna (PMBMB affiliée)Ant (PMBMB)Tyrone (PMBMB) |  |  |  |  |  |  |  |

### THF 46

`https://privedatabase.wordpress.com/thf-46-2/` · page 7493 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Black Disciples
- **Allies:** THF 44, BlackGate, O'Block, OBN, MurdaTown, Welch World, 5th Ward, GuttaVille, DrexSide, Lamron, 600, Lowelife
- **Enemies:** 051 Young Money, 757, SuWu TTB, MOB, SKD, Geo Drive, FreeSmoke, TouchMoney, MuBu, 800, Jaro City, STL/EBT, TYMB, BocoHood, Glo Gang (GBE)
- **Notes:** THF 46 stands for Trigga Happy Family; based in Woodlawn.

- **Bodies attributed to the set:** Zeko (051 Young Money), Dominic (TouchMoney), OJay (Met Boyz), Jamar (757), Jamonie (SuWu TTB), Peter (SuWu TTB), Tu Tu (SuWu TTB), Ice (Met Boyz), Renzo (Met Boyz), Tay (SuWu TTB), Big Freaky (051 Young Money), Goon (TouchMoney), Don Juan (SuWu TTB), Rell (757), T-Berg (051 Young Money), Snoop (757), PD (TouchMoney), Lil Chief (051 Young Money), Sonny (757), Big A (051 Young Money), Wank (051 Young Money), Mall (GeoDrive), Shawt Mac (051 Young Money), Hell Vell (SKD), EBoi (MOB), Curt Mac (MuBu), Romell (TouchMoney), Krump (MuBu), Vedo (TouchMoney), Juke (Bloods d'Atlanta)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Bayzoo | Bay Bay“, «30 Poppa, Mr.051K | Mickey Cobras |  |  | Dominic (TouchMoney); Vedo (TouchMoney); Jamar (757); Juke (Bloods d'Atlanta) | Big Freaky (051 Young Money); Lance (051 Young Money); Pooh Man (051 Young Money); Oochie (051 Young Money); Freeky (051 Young Money); Rosé (051 Young Money); Chop (051 Young Money); J. Rock (051 Young Money); Rocko (051 Young Money); Marcus (051 Young Money); Rosé (051 Young Money); Rocko (051 Young Money); Frump (051 Young Money); Montana (051 Young Money); Paris (051 Young Money); Pooh Man (051 Young Money); Wacko (051 Young Money); Big Freaky (051 Young Money); Kiddo Da Drilla (051 Young Money); Shanno (051 Young Money); Reggie (MetBoyz); Buck Wild (MetBoyz); Boss (SuWu TTB); Rob (757); Kano (Jigdogs); Ricardo (Jigdogs) | Peter (SuWu TTB); Krump (MuBu); Tyriq (Bloods d'Atlanta) |
| Bruh Bruh |  | Black Disciple |  | Y | Renzo (Met Boyz) | Row (MetBoyz); BirdMan (MetBoyz); Rell (MetBoyz); Devo (MetBoyz); Lil Kenny (MetBoyz); Marcus (051 Young Money); Rocko (051 Young Money); Montana (051 Young Money); Aero (051 Young Money); Boom (051 Young Money); Rock (051 Young Money); Freeky (051 Young Money); Creed (Jaro City); Richy Rich (Jaro City); Lil Joe (Jaro City); Tay (No Luv City); Two Hot (SuWu TTB) | Jamar (757) |
| Lil T |  | Black Disciple |  |  | Sonny (757); Krump (MuBu) | Keyso (051 Young Money); Chop (051 Young Money); Kymeon (051 Young Money); B.A. (051 Young Money); Melly (051 Young Money); Melly (051 Young Money, 2018); Obama (757); Tajae (757); Flock (757); Double (Geo Drive); Fatz (800) | Flock (SuWu TTB) |
| Loco |  | Black Disciple | Y |  |  | Murda (757); Geno (757); TayMoney (TouchMoney) |  |
| Mooda | Mooski“, «M Double O, Mooda Crowd | Black Disciple |  | Y |  | Twilla No THF (051 Young Money); Ronno (757); Jefe (757); Dionta (TouchMoney); Smoke (SuWu TTB) |  |
| Raheem |  | Black Disciple |  |  |  | West (Geo Drive); Ario (051 Young Money); Melly (051 Young Money) |  |
| TP, qui est le diminutif de «Two Pistolz» | Two Pistolz | Black Disciple |  |  | Peter (SuWu TTB) | Boom (051 Young Money); Chop (051 Young Money); Marcus (051 Young Money); Pooh Man (051 Young Money); Woo (051 Young Money); Leak (051 Young Money); Stunna (SuWu TTB); Poone (SuWu TTB); EDay (MetBoyz) | Tay (SuWu TTB); Big Freaky (051 Young Money); Shawt Mac (051 Young Money) |
| 007 |  | Black Disciple |  |  | T-Berg (051 Young Money) | Melly (051 Young Money); Kiddo Da Drilla (051 Young Money); Sly (051 Young Money) | Snoop (757) |
| Akee | Kee | Black Disciple |  | Y | Zeko (051 Young Money) |  |  |
| B.A |  | Black Disciple |  | Y |  |  |  |
| Big Dave |  | Black Disciple |  |  |  | T-Streetz (051 Young Money); J. Rock (051 Young Money); Big Noah (051 Young Money); Marcus (051 Young Money); Anrilla (051 Young Money); Lil Danny (051 Young Money); Marley (757); JR (757) |  |
| Billa |  |  |  |  | —— (——); —— (——) | Rocko (051 Young Money); Montana (051 Young Money); White Mike (051 Young Money); Lil Ant (051 Young Money); Wacko (051 Young Money); Bubz (SuWu TTB); Mono LaFlair (SuWu TTB) |  |
| Bob-O |  | Black Disciple |  |  | Big Freaky (051 Young Money); Lil Chief (051 Young Money); Rell (757) | Shawt Mac (051 Young Money); Mally (051 Young Money); Lil Marc (051 Young Money); Ario (051 Young Money); Tristo (051 Young Money); Woo (051 Young Money); Millz (051 Young Money); Neef (757); KC (MuBu); King Louie (MuBu); Binky (MetBoyz); Lil Ron (SuWu TTB); TTB Kelz (SuWu TTB); GBE Capo (Front$treet) | Jamar (757); Renzo (Met Boyz); Big A (051 Young Money) |
| Buckey | BuckShot | Black Disciple |  |  | PD (TouchMoney) | Wacko (051 Young Money); Chop (051 Young Money); Lil Ant (051 Young Money); Koro (051 Young Money); Woo (051 Young Money); Boss (SuWu TTB); TTB Nez (SuWu TTB); Lil Fresh (757) | Shawt Mac (051 Young Money); Curt Mac (MuBu) |
| Da Da |  | Black Disciple |  |  | Jamonie (SuWu TTB); Ice (Met Boyz) | Benz (MetBoyz); Reggie (MetBoyz); Los (051 Young Money); T-Streetz (051 Young Money); Freaky (051 Young Money); T-Lowe (051 Young Money); Kiddo Da Drilla (051 Young Money); Lil Ant (051 Young Money); Lil Danny (051 Young Money); TTB Nez (SuWu TTB); Trap Munna (SuWu TTB); Qwano (SuWu TTB) |  |
| Dre Money |  | Black Disciple |  | Y | Big A (051 Young Money) | Ario (051 Young Money); Woo (051 Young Money); Twilla No THF (051 Young Money); TTB Nez (SuWu TTB) | Jamonie (SuWu TTB) |
| Fat Shorty |  | Black Disciple |  |  | Hell Vell (SKD) | Freeky (051 Young Money); Millz (051 Young Money); T-Lowe (051 Young Money); TTB Tez (SuWu TTB); Black (SuWu TTB); Icke (757); Jaquese (TouchMoney); Re-Up (800) |  |
| G-Baby |  | Black Disciple |  | Y | Mall (Geo Drive) | Millz (051 Young Money); Matt Money (051 Young Money); Woo (051 Young Money); Lil Fresh (757); James (757); TTB Nez (SuWu TTB); Smoke (SuWu TTB); Lil Chance (800); Lil Jock (800); Sko (800); Lil Ray (Geo Drive) |  |
| Gino |  | Black Disciple |  |  | Curt Mac (MuBu); Romell (TouchMoney) | Remy (051 Young Money); Priboy (051 Young Money); Ario (051 Young Money); Melly (051 Young Money); Sly (051 Young Money); Matt (MetBoyz); Dru (MetBoyz); Ronno (757); Dion (TYMB); Phatty (MuBu) | Lil Chief (051 Young Money); Mall (GeoDrive); Hell Vell (SKD) |
| Gucci Da Menace | Slushy The Killer | Black Disciple |  | Y | EBoi (MOB); Willie (Gangster Disciple) | Duke (757); GunSmoke Gudda (757); WyteBread (757); BirthMark (TouchMoney); Oochie (051 Young Money); Kymeon (051 Young Money); Shaggy (SuWu TTB); Lil Mike (Geo Drive) |  |
| Kese The Killer | KTK, White Boy | Black Disciple |  | Y | Tu Tu (SuWu TTB) |  |  |
| Lil Ant |  | Black Disciple |  | Y |  | Law (051 Young Money); Lil Josh (051 Young Money); Andrilla (051 Young Money); Melly (051 Young Money); TTB Nez (SuWu TTB); Montana (TouchMoney); Tuwop (FreeSmoke); FYB DJ (Jaro City) | Big A (051 Young Money); Ayanna (PMBMB affiliée); Ant (PMBMB); Tyrone (PMBMB) |
| Lil Gudda |  | Mickey Cobras |  | Y |  | DJ Money (051 Young Money); Aero (051 Young Money); Tony (051 Young Money); P-Cat (MetBoyz); Tunchie (MetBoyz); Kane (MetBoyz); Black (SuWu TTB) |  |
| Mack |  | Black Disciple |  | Y | Goon (TouchMoney) |  |  |
| Puncho |  | Black Disciple |  | Y |  | Rock (051 Young Money); Mally (051 Young Money); Ario (051 Young Money); Akachi (MetBoyz); Grandson (SuWu TTB) | OJay (Met Boyz) |
| Rome |  | Black Disciple |  | Y | Shawt Mac (051 Young Money) | Montana (051 Young Money); Lil Mick (051 Young Money); Remy (051 Young Money); Matt Money (051 Young Money); Keyso (051 Young Money); Law (051 Young Money); Devo (757); Lil Marcus (TYMB); Krump (MuBu); King Louie (MuBu); Reese (SuWu TTB) | T-Berg (051 Young Money) |
| SaSa |  | Black Disciple |  |  | Tay (SuWu TTB) |  | Wank (051 Young Money) |
| Slushy The Killer | Slick, STK | Black Disciple |  |  | Snoop (757) | Kiddo Da Drilla (051 Young Money); Hassan (051 Young Money); TTB Fathead (SuWu TTB); BeBe (FreeSmoke); Freaky J (FreeSmoke); Spatch (757); Pooh (757); Eddie Moe (TouchMoney); Boss Tez (TouchMoney) |  |
| Twilla aussi connu sous le nom de «Twilla The Killer» | Twilla The Killer, TTK | Black Disciple |  |  | T-Berg (051 Young Money) | Montana (051 Young Money); Big A (051 Young Money); Lil Marc (051 Young Money); Rockhead (051 Young Money); KD (051 Young Money); Meiko (MetBoyz); Lil Kenny (MetBoyz); Kenny (SuWu TTB); Twano (757); Goon (TouchMoney) | Lil Marc (051 Young Money) |
| Westbrook |  | Black Disciple |  | Y | Wank (051 Young Money) | Rosé (051 Young Money); Hassan (051 Young Money); Lil Danny (051 Young Money); KD (051 Young Money); Louie (757); BA (757); Mac (757); JR (757); Reese (SuWu TTB); Jarod (SuWu TTB); Eddie Moe (TouchMoney) |  |

### Tone Bone

`https://privedatabase.wordpress.com/tone-bone/` · page 4148 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Tece (Lamron) |  |  |  |  |  |  | Anthony (Lamron); Lil Moe (Lamron) |

### TOUCHMONEY

`https://privedatabase.wordpress.com/touchmoney-2/` · page 7967 · FCK HEAD$HOT · 2020-01-27

- **Nations:** Gangster Disciples
- **Allies:** JigDogs
- **Enemies:** Dell Mob, THF 46, OBN

- **Members listed:** DMacJaqueseBajonGoon (décédé), QuizPD (décédé), TayMoneyDiontaTerrickLil Touch (décédé), TreyFiveBirthMarkGucci (décédé), JoshAaron (décédé), Polo MacEddie MoeT.O.Boss TezRomell (décédé), Montana (décédé)

### Triggah900

`https://privedatabase.wordpress.com/triggah900/` · page 4243 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Five Star (FollyBoyz)Luda (FollyBoyz)D.Rose (600)Maintain (F |  |  |  |  |  |  |  |

### TYMB

`https://privedatabase.wordpress.com/tymb-2/` · page 7495 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Black Disciples
- **Allies:** SnoBlock, Lowelife, MTV, SMB, Whiz City
- **Enemies:** THF46, Dell Mob, Met Boyz, MadVille, 800, Tyquan World, Jaro City, Stony Spot, Roc Creek, CrankTown, STL/EBT, MuBu, AMG, RowLife, Chris World, Zone7, Brick$quad 069, CMB, 400E Murda Drive, E-Block, Doggpound, PocketTown, Drill City, Mixx Mobb
- **Former allies:** Lamron, WIIIC City
- **Notes:** Based in Woodlawn; many members claim 'EBK'; formerly ran a shooter crew together with Lamron; some members associate with the 051 Young Money and allies, others with O'Block.

- **Bodies attributed to the set:** Carl (STL/EBT), Michael (STL/EBT), Robert (STL/EBT), Tooka (STL/EBT), Doc (STL/EBT), Lil Arron (STL/EBT), Ty (STL/EBT), OJ (Jaro City), Lil D (Jaro City), Dalvin (Jaro City), Tommy (Jaro City), Dashea (Jaro City), Munchie (BlockBurna), Kenny Mac (Chris World), Jesse (Chris World), Pluto (Lamron), Scoota (Zone7), Tavon (Zone7), Reo (Zone7), DewDat (Zone7), BabyJ (Drill City), Remus (Drill City), King Shorty (Drill City), Lil Boss (800), Lil Ant (Mixx Mobb), Kay Kay (Mixx Mobb), Snoop (Mixx Mobb), Kise (MadVille), Big T (Roc Creek)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Big Dre |  | Black Disciple |  |  | King Shorty (Drill City); Ty (STL/EBT, tué en 2018) | Cello (STL/EBT); Dutchie (STL/EBT); Wooski (STL/EBT); Motor (Jaro City); Marcus (Jaro City); Gucci (Jaro City); Lil Darrell (Jaro City); Lil Ears (Drill City); Tino (Drill City); Washy (Drill City); Wooda (Chris World); Dello (MixxMobb); Foota (Zone7); Lil Twan (Tyquan World); Prince (757); Nello (E-Block); KG (Stony Spot) | Scoota (Zone7) |
| Lil Chris | Chris World | Black Disciple | Y |  |  |  |  |
| TY | TYMB | Black Disciple | Y |  | Dalvin (Jaro City) | Tilgo (Jaro City); Drizzy (STL/EBT) |  |
| Zero |  | Black Disciple |  | Y |  | Nate (STL/EBT); King Pre (Zone7); Big J (Chris World); J Boogie (Chris World); WooWoo (Chris World); Big Reggie (Drill City); Johnny Jacket (400E Murda Drive); Big Guy (CrankTown) | Ty (STL/EBT) |
| Cortize |  | Black Disciple |  | Y | Doc (STL/EBT); Dashea (Jaro City) | Reese Gezzy (Jaro City); TuTu (Jaro City); Rock (Jaro City); Art (CMB); WeeWee (STL/EBT); FBG Duck (STL/EBT); Face (STL/EBT); Spoon (STL/EBT); Blue (STL/EBT); D Money (No Luv City); Boss Veze (50 Strong); Rickey (Chris World); D-Thang (MixxMobb) | Tooka (STL/EBT) |
| Cortney | Youngest In Charge | Gangster Disciple |  |  | Tooka (STL/EBT); Lil Arron (STL/EBT) | Chicken (STL/EBT); Lil Don (STL/EBT); Moonhead (STL/EBT); BossTrell (STL/EBT); Torrance (Jaro City); Wayne (Jaro City); Martavius (No Luv City); Shotz (Drill City) | Doc (STL/EBT) |
| Drillie |  | Black Disciple |  | Y | Lil Ant (Mixx Mobb) | Gucci (Jaro City); Jalen (Chris World); Lil De'Seann (MixxMobb); Bandz (MixxMobb); Shauny (MixxMobb); Kiddo Da Drilla (051 Young Money); Fatz (800); Traa (THF 46); Tank Montana (Drill City) | Kay Kay (Mixx Mobb) |
| Face |  | Black Disciple |  |  | OJ (Jaro City); Lil D (Jaro City); Munchie (Brick$quad 069) | Roc (Jaro City); Lil Panky (Jaro City); Weedy (Jaro City); Boss AJ (CMB); Shoe (No Luv City); Quinny Mac (No Luv City); Nate (STL/EBT); Cray Cray (STL/EBT); Killa Tell (Brick$quad 069); Ant Ant (Brick$quad 069); King Pre (Zone7); Jimbo (Zone7) | Robert (STL/EBT); Tommy (Jaro City); Tooka (STL/EBT); Scoota (Zone7) |
| Jhari |  | Black Disciple |  |  | Kenny Mac (Chris World) | Waldo (STL/EBT); Wooski (STL/EBT); Boo Bear (Chris World); WooWoo (Chris World); Jalen (Chris World); GuGu (Drill City); Yon Yon (400E Murda Drive); Gussi (400E Murda Drive) | Reo (Zone7) |
| Jitta |  | Black Disciple |  |  | Scoota (Zone7); Reo (Zone7) | Lil Darrell (Jaro City); Lil P (STL/EBT); Jimmy (Chris World); Squeeze (Drill City); Leaky (Drill City); Lil Law (Drill City); Gucci (Stony Spot); Leak (051 Young Money) | Kenny Mac (Chris World) |
| Kelz |  | Black Disciple |  | Y | Carl (STL/EBT) |  |  |
| Manny | Murda Manny | Black Disciple |  |  | Robert (STL/EBT); Zael (Zone7) |  | Tooka (STL/EBT) |
| Money Man |  | Black P.Stone |  | Y | Tavon (Zone7) | FYB DJ (Jaro City); Jyron (STL/EBT); Antwon (Chris World); Tank Montana (Drill City); Ickey (Drill City); Big Mike (800); Finesse (THF 46); Shag (Zone7) | Scoota (Zone7) |
| Obama | Obama World | Black Disciple | Y |  |  | Travo (Jaro City); P5 (Jaro City); So Icey (STL/EBT); 8Ball (CMB) | Robert (STL/EBT); Tooka (STL/EBT) |
| Outlaw |  | Black Disciple |  | Y | Lil Boss (800) | FatzMack (Drill City); TeTe (Zone7); Dolpho (THF 46); Lil Vic (MixxMobb); OJ (MixxMobb); King Kevo (RowLife); Romie Romey (Doggpound); Spoon (400E Murda Drive); J Boogie (Chris World); Big Boss (Chris World) | Tavon (Zone7) |
| Ro Ro |  | Black Disciple |  |  | Snoop (Mixx Mobb); Remus (Drill City) | Brick (STL/EBT); Lil Mike (Jaro City); Boss Saw (Chris World); Randy (Chris World); Boss Smooth (800); Tim Thang (Stony Spot); Grizzly (MixxMobb); Doro (MixxMobb); Shannon (Zone7); Leaky (Drill City) | Reo (Zone7) |
| Snicka Bar |  | Black Disciple |  |  |  |  |  |
| Trell |  | Black Disciple |  | Y | Michael (STL/EBT) | Hottie (Jaro City) |  |

### TYQUAN WORLD

`https://privedatabase.wordpress.com/tyquan-world-2/` · page 7485 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Gangster Disciples, Black P.Stones
- **Allies:** Jaro City, STL/EBT, PaxTown, DDG, Stony Spot
- **Enemies:** O'Block, 600, Front$treet, 800, DukeSquad, Nicko Gang, TYMB, Saint World, Savage Squad, MooseBlock
- **Notes:** Most members come from Jaro City or STL/EBT; the set was formed after the death of 'Tyquan' from Jaro City.

- **Bodies attributed to the set:** Capo (Front$treet), Jayski (Savage Squad), Melvo (Nicko Gang), June (Nicko Gang), Cheno (O'Block), Chris (O'Block), Big A (O'Block), T-Roy (O'Block), Valentino (MooseBlock), Carlos (Saint World), P-Nut (Saint World), LA (MetLife), Melly (051 Young Money, tué en 2019), Lil TQ (O'Block, tué en 2019), Jaydo (O'Block, tué en 2020), Innocent (tué en 2020)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Coby |  | Gangster Disciple | Y |  | ??? (???); ??? (???) |  |  |
| L.C | 007 | Gangster Disciple |  |  |  | Fatz (800); Porkey (600); Demon (Nicko Gang); Lil Fro (Front$treet); Quono (Front$treet); Toon (Front$treet); Joey (O'Block); Bobo (O'Block) | Melvo (Nicko Gang) |
| Lil Bubba |  | Black P.Stone |  |  | Valentino (MooseBlock); Carlos (Saint World); P-Nut (Saint World); Jaydo (O'Block, tué en 2020) | Abo (800); Boss Smooth (800); Big Mike (800); Lil Jock (800); GloWop (Front$treet); Boss Money (O'Block); Marcus (O'Block); Odie (O'Block); Traa (THF 46); BiteDown (600); Chief Domo (600); Inky D (600); Waldo (600) |  |
| Lil Cho |  | Gangster Disciple |  |  |  | Day Day (Nicko Gang); Jaydo (O'Block); Shauno (O'Block); MeatBall (Front$treet) | Jaydo (O'Block) |
| Lil Mook | Murda Mook, Mook Gon Murk Em | Black P.Stone |  |  |  | Jero (800); Lil So (Front$treet); Vinceo (Front$treet); Scudd (O'Block); Boss Shon (O'Block); King Von (O'Block); OnSight (Nicko Gang); Porkey (600) |  |
| Lil Twan |  | Black P.Stone |  |  |  | Lil Dee (600); DQ (O'Block); Muwop (O'Block); Duke (O'Block); Marcus (O'Block); Nate (Front$treet); Meechy (Front$treet); Quono (Front$treet) | Rico (Nicko Gang); Sam (O'Block) |
| Richie Jerk |  | Black P.Stone |  |  |  | Truey (800); Trey (Front$treet); DQ (O'Block); Johno (O'Block); Demarlow (O'Block); Gleesh (O'Block); Boowop (600) | Capo (Front$treet) |
| G.I. Joe | Geo | Gangster Disciple |  | Y | Chris (O'Block); LA (MetLife); Big A (O'Block) | Tis (O'Block); Muwop (O'Block); Trey5 (O'Block); Solo (O'Block); Lil Khori (O'Block); HK (O'Block); C-Murda (O'Block); Shawn (Front$treet); Kado (JuiceWorld) |  |
| Poppie |  | Black P.Stone | Y |  | Cheno (O'Block) | Po Lo (800); Big Mike (800); Lil Los (Front$treet); Mooch (Front$treet); Meechy (Front$treet); Muwop (O'Block); KD (O'Block); Man (O'Block); Leak (051 Young Money) |  |
| TB | Bico, Big TB | Gangster Disciple | Y |  | Capo (Front$treet); Melvo (Nicko Gang); T-Roy (O'Block) | Lil Nuke (800); Wonno (800); Lil Mista (MooseBlock); BuckyMoe (MooseBlock); Polo (MooseBlock); Lil Los (Front$treet); Maino (Front$treet); Quono (Front$treet); Boss Gottie (Front$treet); Indiana Johnny (Front$treet); Lil JB (Nicko Gang); Man (O'Block); Quano (O'Block); Dmacc (O'Block); Jusblow (600); CapFck12 (600); L'A Capone (600); Cdai (600); Tay600 (600); Booka (600); Lil Dee (600); Wooh Thang (DukeSquad) | Cheno (O'Block); Chris (O'Block) |
| 2Times |  | Black P.Stone |  |  | Jayski (Savage Squad) | ??? (TYMB); ??? (TYMB); ??? (TYMB); ??? (TYMB); ??? (TYMB); ??? (TYMB); ??? (TYMB) | Jaydo (O'Block) |
| Nate |  | Gangster Disciple |  | Y | Melly (051 Young Money) |  |  |

### TYQUAN WORLD

`https://privedatabase.wordpress.com/tyquan-world/` · page 245 · FCK HEAD$HOT · 2020-03-26

- **Nations:** Gangster Disciples, Black P.Stones
- **Allies:** _none_
- **Enemies:** _none_

- **Members listed:** L.CLil BubbaLil ChoLil MookLil TwanRichie Jerk (décédé), G.I. JoePoppie (décédé), TB (décédé), 2TimesNateAnton (décédé), Venzel (décédé), Chief MexicoChunkyD-MoneyDomoDotDroDupreeHersheyKesyLJ LouieMally-GMoe (décédé), Nickel BagPoloPooh PoohPooneyTylerWhite Mike (décédé)

- **Bodies attributed to the set:** Capo (Front$treet), Jayski (Savage Squad), Melvo (Nicko Gang), June (Nicko Gang), Cheno (O'Block), Chris (O'Block), Big A (O'Block), T-Roy (O'Block), Valentino (MooseBlock), Carlos (Saint World), P-Nut (Saint World), LA (MetLife), Melly (051 Young Money), Lil TQ (O'Block), Jaydo (O'Block), Innocent (tué en 2020), Taynod (The Ave)

### Tyto

`https://privedatabase.wordpress.com/tyto/` · page 1772 · FCK HEAD$HOT · 2020-04-10

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Tuta (DamenVille) |  |  |  |  |  |  |  |

### TYTOLAND

`https://privedatabase.wordpress.com/tytoland/` · page 7993 · FCK HEAD$HOT · 2020-02-01

- **Nations:** Vice Lords
- **Allies:** LordsVille
- **Enemies:** LOC City, DamenVille
- **Notes:** Based in the Back of the Yards.

- **Bodies attributed to the set:** ??? (DamenVille), ??? (DamenVille), ??? (DamenVille), ??? (DamenVille), ??? (DamenVille)

### VON WORLD

`https://privedatabase.wordpress.com/von-world-2/` · page 7990 · FCK HEAD$HOT · 2020-01-30

- **Nations:** Gangster Disciples
- **Allies:** MOB
- **Enemies:** BlackGate, Dipset (Front$treet), 600
- **Notes:** Formerly called 'Bully Gang'; renamed after Von's death.

- **Members listed:** Darro est un Gangster Disciple. Il est le grand frère de Senio du même set. Il est actuellement incarcéré.

- **Bodies attributed to the set:** ??? (BlackGate), ??? (BlackGate), ??? (BlackGate), ??? (BlackGate), ??? (Dipset), ??? (Dipset), Musi (Dipset)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Musi (Dipset, poignardé à mort) |  |  |  |  |  |  |  |
| Senio |  | Gangster Disciple |  |  |  |  | Musi (Dipset) |
| Crazy Bob |  | Gangster Disciple |  | Y | KD (Welch World) |  | Musi (Dipset) |
| Bully (décédé) Von (décédé) |  |  | Y |  |  |  |  |

### W.B

`https://privedatabase.wordpress.com/w-b/` · page 874 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Gangster Disciples
- **Allies:** LOC City, DamenVille
- **Enemies:** _none_
- **Notes:** W.B stands for Winchester Wolcott Boyz.

- **Members listed:** Tray (décédé), Shaq (décédé)

- **Bodies attributed to the set:** Jacob (Just-Us), Kevin (Just-Us), Marlin (FollyBoyz), Scrapp (ArtGang), GMarlo (JackBoys), Gary Miller (LordsVille), Sugar Ray (LordsVille)

### Waldo

`https://privedatabase.wordpress.com/waldo/` · page 4751 · FCK HEAD$HOT · 2020-05-11

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Brick (STL/EBT)Coby (STL/EBT) |  |  |  |  |  | Rell Rell (Jaro City); FYB Duke (Jaro City); Pooh Pooh (Tyquan World); Quinny Mac (MOE); Jefe (757); Cease (800); Rosé (051 Young Money) |  |

### WELCH WORLD

`https://privedatabase.wordpress.com/welch-world-3/` · page 6528 · FCK HEAD$HOT · 2019-11-21

- **Nations:** Gangster Disciples, Black Disciples
- **Allies:** _none_
- **Enemies:** 757, SuWu TTB, 051 Young Money
- **Notes:** Formerly called 'So Icy' until Welch was killed; a very old set that produced well-known people such as Tay600, Billionaire Black and his brother Richie Jerk.

- **Bodies attributed to the set:** Mario (757), Kerron (757), Kamane (757), Cliff (SuWu TTB), Curtis (051 Young Money), Maine (757), Cess (757), Neef (757)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Tay Savage | Badass | Black Disciple |  | Y | Kamane (757); Cess (757); Neef (757) | Jizzle (757); Marley (757); Jefe (757); Twano (757); Nikko (757); Frump (051 Young Money); Montana (051 Young Money); Shawt Mac (051 Young Money); Tadoe (Front$treet); D.A. (SuWu TTB); Boss (SuWu TTB); Rex (Lamron) | Kerron (757); Vedo (TouchMoney) |

### WHIZ CITY

`https://privedatabase.wordpress.com/whiz-city-2/` · page 7941 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Black Disciples
- **Allies:** _none_
- **Enemies:** 8Tre Mobb, Drill City, Evans Mobb, MixxMobb, Hitzsquad
- **Notes:** Full name Whiz City BrainDead; based in Chatham.

- **Bodies attributed to the set:** Cliff (8Tre Mobb), Marley (8Tre Mobb), Jeremy (Drill City), Gutta (Evans Mobb), CT (8Tre Mobb), Steven (Evans Mobb), LJ (MixxMobb), Big Meech (Drill City), Maurice (MixxMobb), Jello (Evans Mobb), Jonathan (MixxMobb), Jacc (Hitzsquad), Meechie (MixxMobb), Story (Evans Mobb), Lil Arron (Hitzsquad), Beanz (MixxMobb), Lynell (Hitzsquad)

### WIIIC CITY

`https://privedatabase.wordpress.com/wiiic-city/` · page 240 · FCK HEAD$HOT · 2020-03-26

- **Nations:** Black Disciples
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Formerly called 'BlockHeads' in the 1990s, then W(ild) I(nsane) IIC(razy) City; today known as O'Block, and in the early 2000s shared its neighborhood with No Luv City.

- **Members listed:** Tokyo G (décédé), Snap DBay Bay (décédé), Odee (décédé), CainCameronDanaJosephBang ManReezy (décédé), Fella (décédé), Keta (décédée), Spike (décédé)

- **Bodies attributed to the set:** Brian Thomas (MurderVille), Jeremy (Jaro City), Keonte (JigDogs), Mook (Jaro City)

### WIIIC CITY/O’BLOCK

`https://privedatabase.wordpress.com/wiiic-city-oblock/` · page 6273 · FCK HEAD$HOT · 2019-11-07

- **Nations:** Black Disciples
- **Allies:** 600, Front$treet, Nicko Gang, BlackGate, AAB, THF 46, DukeSquad, Lamron, D-Town, SMB, Will City, 400E Murda Drive, NLMB
- **Enemies:** STL/EBT, Tyquan World, MOB, Jaro City, SuWu TTB, No Luv City, Stony Spot, MuBu, Brick$quad 069, E-Block, PBG/TFG
- **Former enemies:** Brick City
- **Notes:** Formerly known as WIIIC City before member Odee was killed; the new generation represents 'Jmacc Block' for slain member Jmacc of MetLife; was once at war with Brick City (predecessor of the 600) though the two never killed each other.

- **Bodies attributed to the set:** Femme (dans la Wild 100's), Jeremy (Jaro City), Dirty Rell (Jaro City), Keonte (JigDogs), Mook (Jaro City), Marcus (STL/EBT), P5 (Jaro City), Reggie (SKD), Modell (STL/EBT), BossTrell (STL/EBT), Stunna (SuWu TTB), K.I. (STL/EBT), Malcolm (FMG), Twink (Jaro City), Lil Ho (Jaro City), Poppie (Tyquan World), Brick (STL/EBT), TB (Tyquan World), GFredeo (Jaro City), CantGetRight (STL/EBT), Tyriq (Bloods d'Atlanta)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| DQ |  | Black Disciple |  |  |  | Boone (Stony Spot); Gucci (Stony Spot); Lil Mook (Tyquan World); Poppie (Tyquan World); Cray Cray (STL/EBT, 2018) | Brick (STL/EBT); Coby (Tyquan World) |
| Duke |  | Black Disciple |  | Y | Poppie (Tyquan World); CantGetRight (STL/EBT) | Keion (Jaro City); Montae (Jaro City); Rell Rell (Jaro City); Boom (STL/EBT); FBG Cash (STL/EBT); Pharoah (STL/EBT); Richie Jerk (Tyquan World); LJ (Tyquan World) | Brick (STL/EBT); Coby (Tyquan World); Troy (Innocent) |
| E-Dogg |  | Black Disciple |  | Y | Twink (Jaro City); Brick (STL/EBT); GFredeo (Jaro City) | CashCoon (Jaro City); Twink (Jaro City); Keion (Jaro City); Gucci (Jaro City); Fat Shawty (Jaro City); Lil Scrapp (MOB); Shell Da Don (MOB); Waldo (STL/EBT); Zoe (STL/EBT); Drizzy (STL/EBT); Naro (STL/EBT); YP (STL/EBT); Lucky (STL/EBT); Wooski (STL/EBT); Sko (STL/EBT); LJ (Tyquan World); Lil Cho (Tyquan World); Wonno (800) | Lil Ho (Jaro City); Coby (Tyquan World); CantGetRight (STL/EBT) |
| King Von | Silk, Malcolm | Black Disciple |  |  | Modell (STL/EBT); Malcolm (FMG); Tyriq (Bloods d'Atlanta) | Battiay (G-Ville); KD (G-Ville); Santana (G-Ville); Diesel (STL/EBT); Wooski (STL/EBT); Wooski (STL/EBT); BossTrell (STL/EBT); Miles (STL/EBT); Manny Fresh (STL/EBT); Spoon (STL/EBT); FBG Butta (STL/EBT); Skinny (Jaro City); Tyquan (Jaro City); FYB DJ (Jaro City); Hari (Jaro City); CeeJay (Brick$quad 069); Richie Jerk (Tyquan World); Freeky (051 Young Money); Woo (051 Young Money); Rocko (051 Young Money); Boo (Bloods d'Atlanta); ??? (Bloods d'Atlanta); ??? (Bloods d'Atlanta) | P5 (Jaro City); K.I. (STL/EBT) |
| Odee | O'Block | Black Disciple | Y |  | Jeremy (Jaro City) | M.Dot (Jaro City); Lil Worka (Jaro City); Baby D (Jaro City); DipLow (Jaro City); Tilgo (Jaro City); Mr. Hot Sauce (STL/EBT); Diesel (STL/EBT); K.I. (STL/EBT); FBG Butta (STL/EBT); Lil B (STL/EBT); Gotti (RagTown) | Mook (Jaro City) |
| Patoon |  | Black Disciple | Y |  |  | V-Mac (Jaro City); Ruby (Jaro City); Big Dee (STL/EBT); Diesel (STL/EBT) | Mook (Jaro City) |
| Bang Man |  | Black Disciple |  | Y | Keonte (JigDogs); Mook (Jaro City) | 305 (Jaro City); Joe (Jaro City); BK (Jaro City); Baby D (Jaro City); Motor (Jaro City); ABM Tay (Jaro City); So Icey (STL/EBT); BossTrell (STL/EBT) |  |
| Big A |  | Black Disciple | Y |  | Billy (innocent); K.I. (STL/EBT) | Wayne (Jaro City); Lil Joe (Jaro City); Kaliff (Jaro City); Naro (STL/EBT); Billionaire Black (STL/EBT); Drizzy (STL/EBT); BossTrell (STL/EBT); Meechie (STL/EBT); K.I. (STL/EBT); Cray Cray (STL/EBT); FBG Butta (STL/EBT); Hershey (Tyquan World); E-Boogie (E-Town); Jaydee (E-Town) | P5 (Jaro City) |
| B-Mike | 15 ou 16 fois | Black Disciple |  | Y |  | Skinny (Jaro City); Booman (Jaro City); Gucci (Jaro City); FBG Brick (STL/EBT); FBG Duck (STL/EBT) | Malcolm (FMG) |
| Boss Money |  | Black Disciple |  |  | Stunna (SuWu TTB) | FBG Cash (STL/EBT); FBG Butta (STL/EBT); CantGetRight (STL/EBT); Twilla No THF (051 Young Money); Jodi (Jaro City); FYB J Mane (Jaro City) | K.I. (STL/EBT) |
| BossTop |  | Black Disciple |  |  |  | Marquis (Jaro City); Dion (Jaro City); Chief Ty (Jaro City); Weedy (Jaro City); 50Shot (Jaro City); Nate (STL/EBT); George (STL/EBT) | Jeremy (Jaro City); BossTrell (STL/EBT) |
| Chief Keef | Sosa | Black Disciple |  |  |  | Fathead (051 Young Money); Twilla No THF (051 Young Money); FYB J Mane (Jaro City); NumbaNine (Jaro City); FBG Butta (STL/EBT); Meechie (STL/EBT); Myro (MOB); Dooski Tha Man (MOB); Malcolm (MetBoyz) |  |
| C-Murda |  | Black Disciple |  | Y | Dirty Rell (Jaro City) | Ray Ray (Jaro City); Reese Gezzy (Jaro City); Lil Herl (Jaro City); Kaliff (Jaro City); Day Day (STL/EBT) | Mook (Jaro City) |
| Gleesh |  | Black Disciple |  |  | Lil Ho (Jaro City, oncle de 600Breezy) | D-Bo (CMB); Kobe (Jaro City); LJ (Tyquan World); Hershey (Tyquan World) | Brick (STL/EBT); Coby (Tyquan World); GFredeo (Jaro City); TB (Tyquan World) |
| HK | Gucci | Black Disciple | Y |  | Brick (STL/EBT); TB (Tyquan World) | Pharoah (STL/EBT); Wooski (STL/EBT); 2Times (Tyquan World); Domo (Tyquan World); Pooh Pooh (Tyquan World); D-Money (Tyquan World); Ronte (Jaro City); Marcus (Jaro City); Skinny (Jaro City, la fusillade de sa mort); Wooski (STL/EBT, la fusillade de sa mort) | Poppie (Tyquan World); Coby (Tyquan World); Lil Ho (Jaro City) |
| J-Money |  | Black Disciple | Y |  | Reggie (SKD); P5 (Jaro City) | Face (STL/EBT); Booman (STL/EBT); Rasta (STL/EBT); Drizzy (STL/EBT); K.I. (STL/EBT); Rico (STL/EBT); 50Shot (Jaro City); Torrance (Jaro City); Blocks (Jaro City); Rell Rell (Jaro City); James (Jaro City); Lil Darrell (Jaro City); Cheddah (E-Block); Renzo (MetBoyz) | Jeremy (Jaro City); BossTrell (STL/EBT); Modell (STL/EBT); Lil Jojo (Brick$quad 069) |
| Marcus |  | Black Disciple |  |  |  | 007 (Jaro City); Travo (Jaro City); Dot (Tyquan World); Dupree (Tyquan World) | Lil Ho (Jaro City) |
| Trey5 |  | Black Disciple |  | Y | Marcus (STL/EBT); Brick (STL/EBT) | BG (STL/EBT); Jacorey (STL/EBT); Naro (STL/EBT); Jyron (STL/EBT); Rasta (STL/EBT); FBG Duck (STL/EBT); Flame (STL/EBT); 50Shot (Jaro City); Lil Bubba (Tyquan World) | Keonte (JigDogs); Coby (Tyquan World) |
| T-Roy | Baby Boy | Black Disciple | Y |  | BossTrell (STL/EBT) | Lil Don (STL/EBT); FBG Butta (STL/EBT); C-Ball (STL/EBT); So Icey (STL/EBT); BossTrell (STL/EBT); Meechie (STL/EBT); Lil Jay (STL/EBT); Billionaire Black (STL/EBT); Dutchie (STL/EBT); K.I. (STL/EBT); Big Dee (STL/EBT); RoRo (STL/EBT); FBG Butta (STL/EBT); Flash (Jaro City); Rock (Jaro City); NumbaNine (Jaro City); Santana (Jaro City); Bud (Jaro City); Tell (Jaro City); GFredeo (Jaro City); Lil Darrell (Jaro City); Ario (051 Young Money); Ke Ke (051 Young Money); Mally (051 Young Money); Juju (MOB); Lil Twan (Tyquan World) | Doc (STL/EBT); Modell (STL/EBT); Stunna (SuWu TTB); Billy (innocent) |
| Lil Drilla |  | Black Disciples | Y |  |  |  |  |
| Boss Man |  | Black Disciple |  |  |  | Hershey (Tyquan World); Dot (Tyquan World); Lil Cho (Tyquan World); Dallo (Stony Spot) |  |
| C-Bang |  | Black Disciple |  |  |  | NumbaNine (Jaro City); Mazi (Jaro City) |  |
| D-Bandz |  | Black Disciple |  |  |  | Matt (Stony Spot); 2Times (Tyquan World) |  |
| Jaydo |  | Black Disciple | Y |  |  | Chuncky (Tyquan World); Polo (Tyquan World); KG (Stony Spot) |  |
| Johno |  | Black Disciple |  |  |  | Hershey (Tyquan World); Son (Stony Spot) |  |
| Man |  | Black Disciple |  |  |  | Dot (Tyquan World); Bobby (Stony Spot) |  |
| Cheno |  | Black Disciple | Y |  |  | Lil James (TYMB) |  |
| Muwop |  | Black Disciple |  |  | Innocent | Lil Bobo (MOB) | CantGetRight (STL/EBT) |

### WUGA WORLD

`https://privedatabase.wordpress.com/wuga-world-2/` · page 7951 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Gangster Disciples
- **Allies:** _none_
- **Enemies:** Faceworld, DOD, Lowelife, Doggpound, MacBlock, SMB
- **Notes:** Based in Englewood; rappers Rico Recklezz and Lil Mister are members; in early 2020 they assaulted TTE/OTF member DeDe.

- **Members listed:** Stain est un Insane Gangster Disciple. Il est actuellement incarcéré pour le meurtre de Dwayne.

- **Bodies attributed to the set:** Elroy (Doggpound), Tyrone (Doggpound), Odie (SMB), White Boy (FaceWorld), Kenneth (MayBlock), Big AL (Lowelife), Dearie (Doggpound), Dimitre (DOD), Johnny (SMB), Polo Da Don (Doggpound), Daniel (MayBlock), Dwayne (7-Deuce), Lil Drilla (O'Block), DZero (Doggpound)

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Polo Da Don (Doggpound)Dwayne (7-Deuce) |  |  |  |  |  | Ace Boogie (Doggpound); Cuddo (Doggpound); Lil D (Lowelife); Lil Varney (Lamron); Ken Ken (Lamron); Poo Poo (SMB) |  |
| Rico Recklezz | Lil Mister | Black P.Stone |  |  |  | Meeche (Doggpound); Man Man (Doggpound); Water (Lamron); Choppa (Lamron) |  |
| 2 ShotsBD (décédé, tué par la police)B-Dub (décédé)RioWuga ( |  |  | Y |  |  |  |  |

### YOUNG MONEY ARTGANG

`https://privedatabase.wordpress.com/young-money-artgang/` · page 870 · FCK HEAD$HOT · 2020-03-28

- **Nations:** Mickey Cobras, Black P.Stones
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Set dates back to the 1980s.

- **Members listed:** FTO BigGuyScrapp (décédé), Art (décédé), InkMikey DBugBlock (décédé), Lil T (décédé)

- **Bodies attributed to the set:** Tray (W.B 057)

### Zo

`https://privedatabase.wordpress.com/zo-2/` · page 4046 · FCK HEAD$HOT · 2020-04-23

| Member | Aliases | Nation | Dead | Locked | Bodies | Shootings | Assists |
|---|---|---|---|---|---|---|---|
| Jimmy (FuckTown)Bobby (FollyBoyz)Johnny (FollyBoyz) |  |  |  |  |  | Twon (Lamron); Choppa (Lamron); Booda Moe (FollyBoyz); Caddy Mac (FollyBoyz); MoneyMan (FollyBoyz); Five Star (FollyBoyz); G Doodie (FollyBoyz); 50Shot Mall (FollyBoyz); Folly Fatz (FollyBoyz); NickNick (FollyBoyz); Scale (FollyBoyz); STK (THF 46); Famous Mac (MOB); Freeky (051 Young Money); EA (FuckTown); Muwop (O'Block) | Molly (FollyBoyz) |

### ZOLAND

`https://privedatabase.wordpress.com/zoland/` · page 627 · FCK HEAD$HOT · 2020-03-27

- **Nations:** 4 Corner Hustlers, Gangster Disciples, Black P.Stones
- **Allies:** _none_
- **Enemies:** _none_
- **Notes:** Also known as ABM; formerly called 'Chestnut'; mostly 4 Corner Hustlers with a minority of Gangster Disciples and Black P.Stones members.

- **Members listed:** Zo (décédé), Queen Lady Sha (décédée), Big Zo (décédé), Snugg (décédé), Pooh Bear (décédé), Kenny G (décédé), Iceberg (décédé)

### ZONE7

`https://privedatabase.wordpress.com/zone7-2/` · page 7945 · FCK HEAD$HOT · 2020-01-26

- **Nations:** Gangster Disciples
- **Allies:** _none_
- **Enemies:** TYMB, MTV, Whiz City
- **Notes:** Based in Grand Crossing.

- **Members listed:** Scoota (décédé), Tavon (décédé), Reo (décédé), DewDat (décédé)

- **Bodies attributed to the set:** Jalen (Whiz City), BoLo (TYMB), Lil Skud (MTV)

---

## Other Chicago pages (227)

Chicago pages with no set bio and no member block: person stubs, empty pages, indexes.

| Page | Title | Kind | Text |
|---|---|---|---|
| 291 | 757 | person | ROC NATION LAWLESS THE AVE |
| 2561 | 8-TRAY | empty |  |
| 852 | 87TH CUTTHROATS | empty |  |
| 858 | 9-0 ASHLAND | empty |  |
| 861 | 9-5 MOB | empty |  |
| 860 | 9-TRAY | empty |  |
| 869 | A-BLOCK | empty |  |
| 275 | AAB | empty |  |
| 276 | ABM | empty |  |
| 836 | ADA PARK | empty |  |
| 1055 | ALTGELD MURRAY GARDENS | empty |  |
| 278 | AMG | empty |  |
| 279 | BASHVILLE | empty |  |
| 560 | BBG TERROR DOME | empty |  |
| 280 | BEAM TEAM | empty |  |
| 281 | BLACKGATE | empty |  |
| 282 | BLACKMOB | empty |  |
| 1035 | BLOODSTONES | empty |  |
| 284 | BOCO HOOD | empty |  |
| 867 | BOOGIE WORLD | empty |  |
| 241 | BRICK CITY | empty |  |
| 347 | BRICK$QUAD 069 | empty |  |
| 285 | BRICKYARD | empty |  |
| 873 | BSC | empty |  |
| 359 | BUFF CITY | empty |  |
| 1033 | BURNSIDE | empty |  |
| 360 | BWST | empty |  |
| 1813 | By | person | Byron “ By ” Berry était un Gangster Disciple . Il était le frère de Beeski de Lamron . Il est tué le 7 Avril 2020 . |
| 837 | C-TOWN | empty |  |
| 851 | C.A | empty |  |
| 361 | CCG | empty |  |
| 1022 | CEDWORLD | empty |  |
| 856 | CENTRAL CITY | empty |  |
| 1028 | CHIEFTOWN | empty |  |
| 847 | CHILL CITY | empty |  |
| 1027 | CHOPBLOCK | empty |  |
| 1940 | Chris | person | Chris est un Blood . |
| 362 | CHRIS WORLD | empty |  |
| 879 | CHUNKYCITY | empty |  |
| 363 | CMB | empty |  |
| 838 | COOPVILLE | empty |  |
| 364 | CRANK TOWN | empty |  |
| 365 | CUTTAGANG | empty |  |
| 800 | D-TOWN | empty |  |
| 348 | D.O.D | empty |  |
| 367 | DEATHROW 085 | empty |  |
| 368 | DELL MOB | empty |  |
| 7317 | DISCOGRAPHIE | admin | Nous ne prenons en compte que les mixtapes, albums ou EPs officiels, même les projets collaboratifs, posthumes ou publiés par un beatmaker. En revanche, il n’y a pas de compilation. JHE Rooga (MOB) I  |
| 389 | DOGGPOUND | empty |  |
| 868 | DOONSQUAD | empty |  |
| 798 | DREXSIDE | empty |  |
| 391 | DRILL CITY | empty |  |
| 390 | DRO CITY | person | SNOBLOCK – TPG ROC CREEK BNC SAWBLOCK |
| 1736 | Dub | person | Richard Langston , aussi connu sous le nom de “ Rich ” ou de “ Blow “, est un Blood . |
| 859 | DUCKTOWN | empty |  |
| 799 | DUKESQUAD | empty |  |
| 392 | DUMPSTREET | empty |  |
| 393 | E-BLOCK | empty |  |
| 848 | E-SPOT | empty |  |
| 402 | EBE | empty |  |
| 394 | EVANS MOBB | empty |  |
| 395 | FACEWORLD 069 | empty |  |
| 396 | FACEWORLD 079 | empty |  |
| 4106 | Famous Dex | person | Famous Dex est un Gangster Disciple . C’est un rappeur. Il a commencé en ayant était un affilié du Fly Boy Gang et en traînant avec STL/EBT . Il était l’une des personnes présentes lorsque BossTop d’  |
| 854 | FINNTOWN | empty |  |
| 1024 | FLIN BOYZ | empty |  |
| 397 | FOSTER PARK | empty |  |
| 398 | FREE SMOKE | empty |  |
| 1043 | FROGANG | empty |  |
| 244 | FRONT$TREET | empty |  |
| 1048 | FSG | empty |  |
| 2136 | FTO BigGuy | person | FTO BigGuy aussi connu sous le nom de “ Khalil ” est un Mickey Cobra . Il était proche de Scrapp . C’est un rappeur. Il est le beau-frère de BenzZoe de BlackGate . |
| 1039 | FUCKCITY | empty |  |
| 399 | G-VILLE | empty |  |
| 400 | GEO DRIVE | empty |  |
| 1030 | GHETTOWORLD | empty |  |
| 1051 | GHOSTMOBB | empty |  |
| 4334 | Glo Gang | empty |  |
| 401 | GME | empty |  |
| 403 | GOONIE GANG | empty |  |
| 846 | GOONTOWN 10-5 | empty |  |
| 1041 | GUCCIGANG | empty |  |
| 404 | GUNHEAD | empty |  |
| 405 | GUTTAVILLE | empty |  |
| 407 | GUWOPGANG 075 | empty |  |
| 406 | GVG | empty |  |
| 436 | HARVEY WORLD | empty |  |
| 437 | HELLA BANDZ | empty |  |
| 1056 | HITZSQUAD | empty |  |
| 438 | HOOLA GANG | empty |  |
| 440 | IMM | empty |  |
| 876 | INSANE CITY | empty |  |
| 441 | JIGDOGS | empty |  |
| 442 | KEDIZE HOMICIDE KINGS | empty |  |
| 444 | KILLAWARD | person | NEW MONEY 080 YKN 078 JAYLO WORLD 075TH |
| 445 | KIMO GANG | empty |  |
| 7989 | KIMO GANG | person | Le Kimo Gang est un set de Mickey Cobras . |
| 443 | KTS | empty |  |
| 877 | L-BLOCK | empty |  |
| 844 | LACK CITY | empty |  |
| 446 | LAKESIDE | empty |  |
| 447 | LAMRON | empty |  |
| 1026 | LEXVILLE | empty |  |
| 448 | LIL4MOBB | empty |  |
| 7702 | LISTE DES RAPPEURS (CHICAGO) + LEURS SETS | person | A – 15 (S-Dub City/PStreet/BaberBlock) 15 – P Street Baby Air Kelso (TYMB) Air Kelso – In My City Ayoo KD (WillyVille) Ayoo KD – Card Crackers ABK Bobo (ABK) ABK BoBo – Pigs Hot Ayoo (JMG) Andrilla (0 |
| 224 | LISTE DES SETS | city-index | OTF Glo Gang 1200 808 757 600 8X13 3000ST 5TH WARD LIFE 800 YOUNG MONEY 400E MURDA DRIVE 051 YOUNG MONEY 50 STRONG 8-TRAY 9-TRAY 9-0 ASHLAND 9-5 MOB 8TRE MOBB 87TH CUTTHROATS 5TH WARD AAB ABM ABK A-BL |
| 449 | LOC CITY | empty |  |
| 834 | LONDON TOWN | empty |  |
| 473 | LOWELIFE | empty |  |
| 845 | MAIN CITY | empty |  |
| 1042 | MAPLEWOOD | empty |  |
| 474 | MARSHALL FIELD MCs | empty |  |
| 841 | MAUL TOWN | empty |  |
| 857 | MAYBLOCK | empty |  |
| 480 | MBAM | empty |  |
| 475 | MET BOYZ | empty |  |
| 4349 | MetLife | empty |  |
| 853 | MIKE CITY | empty |  |
| 476 | MITCH BLOCK | empty |  |
| 477 | MIXX MOBB | empty |  |
| 1031 | MMG | empty |  |
| 478 | MNA | empty |  |
| 1047 | MNS | empty |  |
| 1049 | MOA | empty |  |
| 246 | MOB | empty |  |
| 875 | MONEYBLOCK | empty |  |
| 481 | MOOSEBLOCK | empty |  |
| 1052 | MOTHERLAND | empty |  |
| 482 | MTG | empty |  |
| 483 | MTV | empty |  |
| 484 | MURDATOWN | empty |  |
| 863 | NATEVILLE | empty |  |
| 485 | NICKO GANG | empty |  |
| 274 | NLMB | empty |  |
| 486 | NO LIMIT 083 | empty |  |
| 487 | NO LIMIT 087 | empty |  |
| 490 | NOSEDMOBB | empty |  |
| 513 | OBN | empty |  |
| 514 | OTE | empty |  |
| 515 | OUT7AW CITY | empty |  |
| 516 | P-BLOCK | empty |  |
| 840 | PACOLAND | empty |  |
| 835 | PALMER PARK | empty |  |
| 517 | PAXTOWN | empty |  |
| 518 | PBG | empty |  |
| 1053 | PIRATEGANG | empty |  |
| 520 | POCKETTOWN | empty |  |
| 1227 | Pooh Bear | person | David “ PB ” ou “ Pooh Bear ” Phillips était un membre du ZoLand . C’était un 4 Corner Hustler . Il était aussi un rappeur. Il est tué le 22 Février 2020 . ARTICLE DE SA MORT: David “PB” Philips |
| 1046 | POPPYGANG | empty |  |
| 521 | POTTBLOCK | empty |  |
| 1040 | PRINCETONMOBB | empty |  |
| 4888 | Privacy Policy | person | Who we are Our website address is: . What personal data we collect and why we collect it Comments When visitors leave comments on the site we collect the data shown in the comments form, and also the  |
| 522 | PSYCHO GANG | empty |  |
| 864 | QUIETMONEY | empty |  |
| 1034 | QUILLBLOCK | empty |  |
| 862 | RACKCITY | empty |  |
| 839 | RAG TOWN | empty |  |
| 866 | REBLUV | empty |  |
| 523 | REC CITY | empty |  |
| 843 | RICOBLOCK | empty |  |
| 524 | RISKY ROAD | empty |  |
| 525 | RMG | empty |  |
| 3655 | Roc | person | Rodney Yeargi , aussi connu sous le nom de “ Doughboy Roc “, était membre du groupe “ Doughboyz Cashout “. Il a été tué le 9 Octobre 2017 à l’âge de 29 ans . Il est considéré par beaucoup comme étant  |
| 999 | ROC CREEK | empty |  |
| 526 | ROC CREEK | empty |  |
| 1038 | ROOKIEVILLE 11-5 | empty |  |
| 1036 | RUDEVILLE | empty |  |
| 1021 | S-DUB | empty |  |
| 1065 | S.O.A | empty |  |
| 527 | SACKBOYZ | empty |  |
| 1913 | SAVAGE SQUAD | empty |  |
| 2147 | Scrapp | person | Scrapp était un Mickey Cobra . Il est décédé . Après sa mort, la Young Money ArtGang adopte le nom de “ Scrapp Gang ” pour lui rendre hommage. Il était proche de FTO BigGuy . |
| 528 | SEDVILLE | empty |  |
| 530 | SHIELDS | empty |  |
| 1045 | SICKOMOBB | empty |  |
| 833 | SIN CITY | empty |  |
| 550 | SIRCONN CITY GANGSTERS | empty |  |
| 551 | SK | empty |  |
| 566 | SKD | empty |  |
| 563 | SKEEZE WORLD | empty |  |
| 564 | SLUTTY BOYZ | empty |  |
| 565 | SMASHVILLE | empty |  |
| 871 | SQUADVILLE | empty |  |
| 567 | SQUIRTTOWN | empty |  |
| 865 | STAIN CITY | empty |  |
| 1037 | STATEBOYZ | empty |  |
| 849 | STONE TEZ | empty |  |
| 568 | STONY SPOT | empty |  |
| 2115 | Sugar Ray | person | Sugar Ray était un Insane Vice Lord . Il est décédé . Après sa mort, son cousin Kasper , qui est un officier de police se venge en usant de ses droits d’agent. Il prend part pour le set LordsVille en  |
| 569 | SUWU MOBB | empty |  |
| 570 | SUWU TTB | empty |  |
| 571 | SWIFT CITY | empty |  |
| 1771 | T-Baby | person | T-Baby est un Gangster Disciple . Il est actuellement incarcéré . Le W.B 057 était prêt à tuer T-Baby parce que ce dernier donnait trop d’informations dans ses musiques. La police l’a arrêté avant par |
| 2213 | Tae | person | Tae est actuellement incarcéré . |
| 4239 | TaeDogg | person | TaeDogg aussi connu sous le nom de “ Javonta ” est un Gangster Disciple . Il est originaire de la THF 44 et il est toujours proche d’eux. |
| 4154 | Tay | person | Tay est un Gangster Disciple . |
| 573 | TAY CITY | empty |  |
| 881 | TAYTOWN | empty |  |
| 558 | TEDAMOBB | empty |  |
| 1020 | TERROR TOWN | empty |  |
| 519 | TFG | empty |  |
| 559 | THF 44 | empty |  |
| 561 | THF 46 | empty |  |
| 1186 | Tokyo G | person | Tokyo G était un Black Disciple de la WIIIC City . Il est tué le 23 Septembre 1996 dans le quartier de MurderVille ( STL/EBT ). |
| 1044 | TONIOMOBB | empty |  |
| 562 | TOUCHMONEY | empty |  |
| 850 | TRAYTOWN | empty |  |
| 3836 | Tra’Don | person | Sanders aussi connu sous le nom de “ Tra’Don ” était un Gangster Disciple . Il est décédé . Il était proche du 50 Strong . |
| 1032 | TRIPLE B’Z | empty |  |
| 1181 | Ty | person | Tyrone “ Ty ” White était un Gangster Disciple de MurderVille . C’était un OG . Il est tué le 10 Juin 2018 . |
| 575 | TYMB | empty |  |
| 576 | TYTO LAND | empty |  |
| 1050 | UNDERTAKERS | empty |  |
| 577 | VON WORLD | empty |  |
| 578 | WELCH WORLD | empty |  |
| 1025 | WHITEWHITE GANG | empty |  |
| 579 | WHIZ CITY | empty |  |
| 2540 | Will | person | Darryl Gooden , aussi connu sous le nom de “ Big Will ” ou de “ George ” était un des lieutenants des PA Boys à Atlanta . |
| 801 | WILL CITY | empty |  |
| 581 | WUGA WORLD | empty |  |
| 1023 | YMM | empty |  |
| 1112 | YOSHI CITY | empty |  |
| 580 | YOUNG LORDS | empty |  |
| 7968 | YOUNG LORDS | person | Les Young Lords sont un set de GayLords . Ils sont situés dans l’ Uptown . C’est l’un des plus vieux sets GayLords encore présent, ils ont près de 50 ans d’existence . |
| 878 | YOUNGWORLD | empty |  |
| 1226 | Zo | person | Lorenzo “ Zo ” McKeithen était un 4 Corner Hustler du Chestnut . Il est tué le 5 Juin 2009 . Après sa mort, le Chestnust se renomme en “ ZoLand ” pour lui rendre hommage. |
| 608 | ZONE7 | empty |  |
