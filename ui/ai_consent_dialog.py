"""
AI Consent Dialog
Shows terms and conditions for AI feature usage
"""
import tkinter as tk
from tkinter import ttk
from utils.config_helper import set_ai_consent


class AIConsentDialog:
    """Dialog for AI feature consent"""

    def __init__(self, parent):
        self.result = False  # Track if user accepted

        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AI Funkció - Felhasználási Feltételek")
        self.dialog.geometry("600x550")
        self.dialog.resizable(False, False)  # Not resizable
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (550 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Configure grid weights
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)

        self._create_widgets()

        # Wait for dialog to close
        parent.wait_window(self.dialog)

    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container frame
        container = tk.Frame(self.dialog, bg="#F5F5F5")
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Configure container grid
        container.grid_rowconfigure(2, weight=1)  # Text area expands
        container.grid_columnconfigure(0, weight=1)

        # Title
        title_label = tk.Label(
            container,
            text="🤖 AI Összefoglaló Funkció",
            font=("Segoe UI", 14, "bold"),
            bg="#F5F5F5",
            fg="#333"
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Subtitle
        subtitle_label = tk.Label(
            container,
            text="Kérjük, olvassa el az alábbi tájékoztatót",
            font=("Segoe UI", 9),
            bg="#F5F5F5",
            fg="#666"
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(0, 15))

        # Text frame with scrollbar
        text_frame = tk.Frame(container, bg="#FFFFFF", relief=tk.SOLID, borderwidth=1)
        text_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 15))

        # Configure text frame grid
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Text widget
        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#333",
            padx=15,
            pady=15,
            yscrollcommand=scrollbar.set,
            state='normal'
        )
        text_widget.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=text_widget.yview)

        # Insert consent text (PLACEHOLDER - you will replace this)
        consent_text = """
A SZEMÉLYES ADATOK KEZELÉSÉRE VONATKOZÓ ADATVÉDELMI NYILATKOZAT
 
A Sortify az alkalmazást használó felhasználók adatait kezeli.
Az adatok kezelésével összefüggésben társaságunk ezúton tájékoztatja a felhasználókat az alkalmazás használata alkalmával kezelt személyes adatokról, a személyes adatok kezelése körében követett elveiről és gyakorlatáról, a személyes adatok védelme érdekében tett szervezési és technikai intézkedéseiről, valamint az érintettek jogai gyakorlásának módjáról és lehetőségeiről. Az alkalmazás üzemeltetője vállalja, hogy a rögzített személyes adatokat bizalmasan, az adatvédelmi jogszabályokkal és nemzetközi ajánlásokkal összhangban, a jelen nyilatkozatnak megfelelően kezeli, harmadik fél számára a jelen nyilatkozat elfogadásával adja át.
Az adatkezelés jogalapja
Az adatkezelésre a Sortify alkalmazást használók önkéntes hozzájárulásával kerül sor. Az alkalmazás használata magában foglalja a felhasználási feltételek (ideértve az adatkezelési rendelkezések) elfogadását is.
A felhasználó az adatai kezelésével kapcsolatos hozzájárulását az alkalmazás szolgáltatásainak igénybevételével, az alkalmazás elindításával és az ott megjelenő adatkezelési tájékoztató elfogadásával adja meg.
A személyes adatok kezelésére az Európai Parlament és Tanács 2016/679 rendelete (GDPR) 6. cikk (1) b) pontja alapján a felek között létrejött szerződés teljesítéséhez szükséges adatként kerül sor.
Kezelt adatok
Az adatkezelő a fenti célból a felhasználás során rendelkezésre bocsátott alábbi adatokat kezeli.
1. 
Név
Email cím
Gmail authentikáció

Az alkalmazás használata során hozzáférhető adatokat a mesterséges intelligencia (a továbbiakban: AI) is kezeli, az AI minden bejövő e-mail tartalmát automatikusan elemzi, amely személyes adatok nagy mennyiségű technikai feldolgozását jelenti.
Az alkalmazás által végzett automatizált e-mail-címkézéshez igénybe vett AI alapú megoldás profilalkotást valósíthat meg.
Az e-mailek tartalma - az alkalmazás felhasználási módja okán - továbbításra kerülhet a feldolgozás során használt külső AI-szolgáltatóhoz, amely adatfeldolgozóként jár el.
Az adatfeldolgozó egyes e‑mail‑feldolgozási folyamataiban – különösen a beérkező levelek automatikus kategorizálása és összefoglalása során – külső mesterségesintelligencia‑szolgáltatót vesz igénybe.
Ennek keretében az oktatókhoz, ügyintézőkhöz érkező e‑mailek bizonyos adatai (különösen: feladó neve és e‑mail címe, címzettek, a levél tárgya és szöveges tartalma) továbbításra kerülhetnek a szolgáltató részére, kizárólag ezen funkciók nyújtása céljából.
Amennyiben a Sortify alkalmazást munkáltatói (céges) e‑mail‑fiókhoz kapcsolják, a munkavállaló a munkaszerződés és a vonatkozó belső szabályzatok elfogadásával tudomásul veszi, hogy a céges e‑mail‑fiók elsődlegesen munkavégzési célokat szolgál. A céges e‑mail‑fiókba érkező és onnan küldött üzenetek – ideértve azok személyes adatot tartalmazó részeit is – a munkáltató jogos érdekén alapuló, automatizált ellenőrzés és AI‑alapú feldolgozás tárgyát képezhetik (pl. levelek kategorizálása, ügyintézési feladatok szervezése céljából). A magáncélú levelezésre a céges e‑mail‑fiók ilyen esetben nem, vagy csak a munkáltató szabályzataiban meghatározott korlátok között használható.
Amennyiben az AI által végzett email feldolgozáshoz a felhasználó nem járul hozzá, az alkalmazás használatát mellőznie kell. 
Az adatkezelés célja
A felhasználás során kezelt adatok használata az alkalmazás működtetéséhez, a felhasználó email címkézésének megvalósítása érdekében szükséges. 
Az adatkezelés időtartama
A felhasználás során megadott személyes adatok kezelése a regisztrációval kezdődik és az adatok törléséig tart. Az adatok törlésére akkor kerül sor, amikor azokra a létrejött szerződés teljesítése körében szükség már nincsen, így Ptk. elévülésről szóló rendelkezései (6: 21 – 6: 25 §), illetve Számviteli tv. 169. § (2) alapján az adatokat az utolsó szerződés keltétől számított 5 évig, a keletkező bizonylatokat az utolsó szerződés keltétől számított 8 évig őrzi meg.
Adatbiztonság
Az adatkezelő minden szükséges lépést megtesz, hogy biztosítsa a Felhasználók által megadott személyes adatok biztonságát mind a hálózati kommunikáció során, mind az adatok tárolása, őrzése során. Az AI általi adatkezelésért az alkalmazott mesterséges intelligencia üzemeltetője felelős az AI adatkezelési tájékoztatójában foglaltak szerint. 
Az adatvédelmi nyilatkozat egyoldalú módosításának lehetősége
Az adatkezelő fenntartja a jogot, hogy jelen adatvédelmi nyilatkozatot a Felhasználók előzetes értesítése mellett egyoldalúan módosítsa. A módosítás hatályba lépését követően a felhasználó ráutaló magatartással elfogadja a hatályos módosított adatvédelmi nyilatkozatot. A módosítás nem érintheti a jogszabályokban előírt adatvédelmi kötelezettségeket.
 A Felhasználó jogai és érvényesítésük
 
1.) A Felhasználó jogosult arra, hogy
a) az adatkezeléssel összefüggő tényekről az adatkezelés megkezdését megelőzően tájékoztatást kapjon (a továbbiakban: előzetes tájékozódáshoz való jog),
b) kérelmére személyes adatait és az azok kezelésével összefüggő információkat az adatkezelő a rendelkezésére bocsássa (a továbbiakban: hozzáféréshez való jog),
c) kérelmére, valamint az e fejezetben meghatározott további esetekben személyes adatait az adatkezelő helyesbítse, illetve kiegészítse (a továbbiakban: helyesbítéshez való jog),
d) kérelmére, valamint az e fejezetben meghatározott további esetekben személyes adatai kezelését az adatkezelő korlátozza (a továbbiakban: az adatkezelés korlátozásához való jog),
e) kérelmére, valamint az e fejezetben meghatározott további esetekben személyes adatait az adatkezelő törölje (a továbbiakban: törléshez való jog)
 
2.) A jogok érvényesítése általánosságban
Az adatkezelő a Felhasználó jogai érvényesülésének elősegítése érdekében bármely értesítést és tájékoztatást könnyen hozzáférhető és olvasható formában, lényegre törő, világos és közérthetően megfogalmazott tartalommal teljesíti, és a Felhasználó által benyújtott, az őt megillető jogosultságok érvényesítésére irányuló kérelmet annak benyújtásától számított legrövidebb idő alatt, de legfeljebb huszonöt napon belül elbírálja és döntéséről a Felhasználót írásban vagy ha a Felhasználó a kérelmet elektronikus úton nyújtotta be, elektronikus úton értesíti.
Az adatkezelő a Felhasználó jogainak érvényesülésével kapcsolatban meghatározott feladatait – a 2011. évi CXII törvényben (Info tv.) meghatározott kivételekkel - ingyenesen látja el.
 
3.) Az előzetes tájékozódáshoz való jog érvényesülése
Az előzetes tájékozódáshoz való jog érvényesülése érdekében az adatkezelő az általa végzett adatkezelési műveletek megkezdését megelőzően (a Felhasználó regisztrációja során) – jelen tájékoztató rendelkezésre bocsátásával - haladéktalanul a Felhasználó rendelkezésére bocsátja
a) az adatkezelő és - ha valamely adatkezelési műveletet adatfeldolgozó végez, az adatfeldolgozó - megnevezését és elérhetőségeit,
b) a tervezett adatkezelés célját és
c) a Felhasználót megillető jogok, valamint azok érvényesítése módjának ismertetését.
d) az adatkezelés jogalapjáról,
e) a kezelt személyes adatok megőrzésének időtartamáról, ezen időtartam meghatározásának szempontjairól,
f) a kezelt személyes adatok továbbítása vagy tervezett továbbítása esetén az adattovábbítás címzettjeinek - ideértve a harmadik országbeli címzetteket és nemzetközi szervezeteket - köréről,
g) a kezelt személyes adatok gyűjtésének forrásáról és
h) az adatkezelés körülményeivel összefüggő minden további érdemi tényről.
 
4.) A hozzáféréshez való jog érvényesülése
Az adatkezelés során profilalkotásra nem kerül sor.
A Felhasználó személyes adatainak kezelésével összefüggésben felmerülő adatvédelmi incidensek bekövetkezése esetén tájékoztatást nyújt Felhasználó részére az incidens körülményeiről, azok hatásairól és az azok kezelésére tett intézkedésekről.
(3) A Felhasználó hozzáféréshez való jogának érvényesítését az adatkezelő az elérni kívánt céllal arányosan korlátozhatja vagy megtagadhatja, ha ezen intézkedés elengedhetetlenül szükséges az Info tv. 16. §-ban meghatározott valamely érdek biztosításához. Ilyen esetben az adatkezelő írásban, haladéktalanul tájékoztatja a Felhasználót a hozzáférés korlátozásának vagy megtagadásának tényéről, továbbá jogi és ténybeli indokairól, kivéve, ha ez a törvény 16. §-ban meghatározott valamely érdek érvényesülését veszélyezteti, valamint a Felhasználót megillető jogokról, valamint azok érvényesítésének módjáról, így különösen arról, hogy Felhasználó a hozzáféréshez való jogát a Hatóság közreműködésével is gyakorolhatja.
 
5.) A helyesbítéshez való jog érvényesülése
Adatkezelő, ha az általa kezelt személyes adatok pontatlanok, helytelenek vagy hiányosak, azokat - különösen a Felhasználó kérelmére - haladéktalanul pontosítja vagy helyesbíti, illetve ha az az adatkezelés céljával összeegyeztethető, a Felhasználó által rendelkezésére bocsátott további személyes adatokkal vagy a Felhasználó által a kezelt személyes adatokhoz fűzött nyilatkozattal kiegészíti (a továbbiakban együtt: helyesbítés).
Adatkezelő mentesül a fenti kötelezettség alól, ha a pontos, helytálló, illetve hiánytalan személyes adatok nem állnak rendelkezésére és azokat Felhasználó sem bocsátja a rendelkezésére, vagy a Felhasználó által rendelkezésére bocsátott személyes adatok valódisága kétséget kizáróan nem állapítható meg.
 
6.) Az adatkezelés korlátozásához való jog érvényesülése
Ha Felhasználó vitatja az adatkezelő által kezelt személyes adatok pontosságát, helytállóságát vagy hiánytalanságát, és a kezelt személyes adatok pontossága, helytállósága vagy hiánytalansága kétséget kizáróan nem állapítható meg, a fennálló kétség tisztázásának időtartamára; vagy ha az adatok törlésének lenne helye, de a Felhasználó írásbeli nyilatkozata vagy az adatkezelő rendelkezésére álló információk alapján megalapozottan feltételezhető, hogy az adatok törlése sértené a Felhasználó jogos érdekeit, a törlés mellőzését megalapozó jogos érdek fennállásának időtartamára; továbbá ha az adatok törlésének lenne helye, de az adatkezelő vagy más közfeladatot ellátó szerv által vagy részvételével végzett, jogszabályban meghatározott vizsgálatok vagy eljárások - így különösen büntetőeljárás - során az adatok bizonyítékként való megőrzése szükséges, ezen vizsgálat vagy eljárás végleges, illetve jogerős lezárásáig; végül abban az esetben, ha az adatok törlésének lenne helye, de a dokumentációs kötelezettség teljesítése céljából az adatok megőrzése szükséges, az Info tv-ben meghatározott időpontig az Iroda az alábbi adatkezelési műveletekre korlátozza az adatkezelést:
Az adatkezelés korlátozásának időtartama alatt a korlátozással Felhasználó személyes adatokkal az adatkezelő a tároláson túl egyéb adatkezelési műveletet kizárólag a Felhasználó jogos érdekének érvényesítése céljából vagy törvényben, nemzetközi szerződésben, illetve az Európai Unió kötelező jogi aktusában meghatározottak szerint végezhet.
 
7.) A törléshez való jog érvényesítése
Az adatkezelő haladéktalanul törli a Felhasználó személyes adatait, ha
a) az adatkezelés jogellenes, így különösen, ha az adatkezelés a jogszabályokban rögzített alapelvekkel ellentétes, célja megszűnt, vagy az adatok további kezelése már nem szükséges az adatkezelés céljának megvalósulásához, törvényben, nemzetközi szerződésben vagy az Európai Unió kötelező jogi aktusában meghatározott időtartama eltelt, vagy jogalapja megszűnt és az adatok kezelésének nincs másik jogalapja,
b) a Felhasználó az adatkezeléshez adott hozzájárulását visszavonja vagy személyes adatainak törlését kérelmezi, kivéve, ha az adatok kezelése az 5. § (1) bekezdés a) vagy c) pontján vagy (2) bekezdés b) pontján alapul,
c) az adatok törlését jogszabály, az Európai Unió jogi aktusa, a Hatóság vagy a bíróság elrendelte.
 
8.) Eljárás a Felhasználó kérelmével kapcsolatosan
Ha az adatkezelő az általa kezelt személyes adatokat helyesbíti, törli vagy ezen adatok kezelését korlátozza, az adatkezelő ezen intézkedés tényéről és annak tartalmáról értesíti azon adatkezelőket és adatfeldolgozókat, amelyek részére az adatot ezen intézkedését megelőzően továbbította, annak érdekében, hogy azok a helyesbítést, törlést vagy az adatok kezelésének korlátozását a saját adatkezelésük tekintetében végrehajtsák. 
A Felhasználót megillető jogok, valamint azok érvényesítésének móda:
 Jogainak érvényesítése érdekében a Felhasználó
a.) a Nemzeti Adatvédelmi és Információszabadság Hatóság ( a továbbiakban Hatóság, székhely:1024 Budapest, Szilágyi Erzsébet fasor 22/C., honlap: www.naih.hu) vizsgálatát kezdeményezheti az adatkezelő intézkedése jogszerűségének vizsgálata céljából, ha az adatkezelő az őt megillető jogainak érvényesítését korlátozza vagy ezen jogainak érvényesítésére irányuló kérelmét elutasítja, valamint
b) a Hatóság adatvédelmi hatósági eljárásának lefolytatását kérelmezheti, ha megítélése szerint személyes adatainak kezelése során az adatkezelő, illetve az általa megbízott vagy rendelkezése alapján eljáró adatfeldolgozó megsérti a személyes adatok kezelésére vonatkozó, jogszabályban vagy az Európai Unió kötelező jogi aktusában meghatározott előírásokat.
c) A Felhasználó az adatkezelő ellen bírósághoz fordulhat, ha megítélése szerint az adatkezelő a személyes adatait a személyes adatok kezelésére vonatkozó, jogszabályban vagy az Európai Unió kötelező jogi aktusában meghatározott előírások megsértésével kezeli. Azt, hogy az adatkezelés a személyes adatok kezelésére vonatkozó, jogszabályban vagy az Európai Unió kötelező jogi aktusában meghatározott előírásoknak megfelel, az adatkezelő köteles bizonyítani. A pert a Felhasználó - választása szerint - a lakóhelye vagy tartózkodási helye szerint illetékes törvényszék előtt is megindíthatja. A perben fél lehet az is, akinek egyébként nincs perbeli jogképessége. A perbe a Hatóság a Felhasználó pernyertessége érdekében beavatkozhat.
Ha a bíróság a keresetnek helyt ad, a jogsértés tényét megállapítja és az adatkezelőt, illetve az adatfeldolgozót a jogellenes adatkezelési művelet megszüntetésére, az adatkezelés jogszerűségének helyreállítására, illetve a Felhasználó jogai érvényesülésének biztosítására pontosan meghatározott magatartás tanúsítására kötelezi, és szükség esetén egyúttal határoz a kártérítés, sérelemdíj iránti igényről is.
  
Adatvédelmi incidens
 
Az adatkezelő az általa kezelt adatokkal összefüggésben felmerült adatvédelmi incidens kapcsán rögzíti az adatvédelmi incidens jellegét, beleértve a Felhasználók körét és hozzávetőleges számát, valamint az incidenssel Felhasználó adatok körét és hozzávetőleges mennyiségét. Rögzíti továbbá az adatvédelmi incidensből eredő, valószínűsíthető következményeket; végül pedig az adatkezelő által az adatvédelmi incidens kezelésére tett vagy tervezett - az adatvédelmi incidensből eredő esetleges hátrányos következmények mérséklését célzó és egyéb – intézkedéseket.
Adatkezelő az adatvédelmi incidenst haladéktalanul, de legfeljebb az adatvédelmi incidensről való tudomásszerzését követő hetvenkét órán belül köteles bejelenteni a Hatóságnak.
Az adatvédelmi incidenst nem kell bejelenteni, ha valószínűsíthető, hogy az nem jár kockázattal a Felhasználók jogainak érvényesülésére.
A bejelentési kötelezettség keretei között az adatkezelő a Hatóság által e célra biztosított elektronikus felületen
a) ismerteti az adatvédelmi incidens jellegét, beleértve - ha lehetséges - a Felhasználók körét és hozzávetőleges számát, valamint az incidenssel Felhasználó adatok körét és hozzávetőleges mennyiségét,
b) tájékoztatást nyújt az adatvédelmi tisztviselő vagy a további tájékoztatás nyújtására kijelölt más kapcsolattartó nevéről és elérhetőségi adatairól,
c) ismerteti az adatvédelmi incidensből eredő, valószínűsíthető következményeket, és
d) ismerteti az adatkezelő által az adatvédelmi incidens kezelésére tett vagy tervezett - az adatvédelmi incidensből eredő esetleges hátrányos következmények mérséklését célzó és egyéb - intézkedéseket.
Ha valamely fenti információ a bejelentés időpontjában nem áll az adatkezelő rendelkezésére, azzal az adatkezelő a bejelentést annak benyújtását követően utólag egészíti ki.
 
Az adatkezelés módja és biztonsága
 
Az Adatkezelő gondoskodik az adatok biztonságáról, és megteszi azokat a technikai és szervezési intézkedéseket és kialakítja azokat az eljárási szabályokat, amelyek a GDPR, valamint az Infotv., továbbá az egyéb jogszabályokban előírt adat- és titokvédelmi szabályok érvényre juttatásához szükségesek. Az Adatkezelő a személyes adatokat védi a jogosulatlan hozzáféréstől; megváltoztatástól; továbbítástól; nyilvánosságra hozataltól; vagy véletlen törléstől, megsemmisítéstől; sérüléstől; valamint az alkalmazott technika megváltozásából fakadó hozzáférhetetlenné válástól.
 
Az Adatkezelő különös hangsúlyt fektet a különböző nyilvántartásokban elektronikusan kezelt adatállományok védelmére annak érdekében, hogy a különböző nyilvántartásokban tárolt adatok – kivéve, ha azt törvény lehetővé teszi - közvetlenül ne legyenek összekapcsolhatók és a Felhasználóhoz rendelhetők.
 
A személyes adatok automatizált feldolgozása során biztosítja az Adatkezelő:
a jogosulatlan adatbevitel megakadályozását;
a rendszerek jogosulatlan személyek általi használatát;
annak ellenőrizhetőségét és megállapíthatóságát, hogy a személyes adatokat adatátviteli berendezés alkalmazásával mely szerveknek továbbították vagy továbbíthatják;
annak ellenőrizhetőségét és megállapíthatóságát, hogy mely személyes adatokat,
mikor és ki vitte be az automatikus adatfeldolgozó rendszerekbe;
a telepített rendszerek üzemzavar esetén történő helyreállíthatóságát
 
Az adatkezelő:
Név: GI5A
Székhelye: 1011 Budapest, Milton F. u. 5.
Cégjegyzékszáma: 01-02-321568
Adószáma: 1234469-2-41
Email: teszt@gi5a.com"""

        text_widget.insert('1.0', consent_text.strip())
        text_widget.config(state='disabled')

        # Buttons frame (bottom right corner)
        button_frame = tk.Frame(container, bg="#F5F5F5")
        button_frame.grid(row=3, column=0, sticky="e")

        # Use ttk style for clean buttons
        style = ttk.Style()
        style.configure("Consent.TButton", font=("Segoe UI", 10))

        # Decline button
        btn_decline = ttk.Button(
            button_frame,
            text="Elutasítom",
            style="Consent.TButton",
            command=self._on_decline
        )
        btn_decline.grid(row=0, column=0, padx=(0, 10))

        # Accept button
        btn_accept = ttk.Button(
            button_frame,
            text="Elfogadom",
            style="Consent.TButton",
            command=self._on_accept
        )
        btn_accept.grid(row=0, column=1)

    def _on_accept(self):
        """User accepted consent"""
        self.result = True
        set_ai_consent(True)
        print("[INFO] AI consent ACCEPTED")
        self.dialog.destroy()

    def _on_decline(self):
        """User declined consent"""
        self.result = False
        print("[INFO] AI consent DECLINED")
        self.dialog.destroy()

    def get_result(self) -> bool:
        """Get dialog result

        Returns:
            True if accepted, False if declined
        """
        return self.result


def show_ai_consent_dialog(parent) -> bool:
    """Show AI consent dialog and return result

    Args:
        parent: Parent window

    Returns:
        True if user accepted, False if declined
    """
    dialog = AIConsentDialog(parent)
    return dialog.get_result()
