from vepar import *
import csv

subskript = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


class PrekidBreak(NelokalnaKontrolaToka):
    """Signal koji šalje naredba break."""


class PrekidContinue(NelokalnaKontrolaToka):
    """Signal koji šalje naredba continue."""


class T(TipoviTokena):
    # Tokeni za modalne formule
    NEG, KONJ, DISJ, O_OTV, O_ZATV = "~&|()"
    KOND, BIKOND = "->", "<->"
    BOX, DIAMOND = "[]", "<>"

    class PVAR(Token):
        def optim(self):
            return self

        def ispis(self):
            return self.sadržaj.translate(subskript)

        def optim1(self):
            return self

        def vrijednost(self, w):
            return self in w.činjenice

        def pozovi(self):
            return self

    class TRUE(Token):
        literal = "T"

        def vrijednost(self, w):
            return True

        def ispis(self):
            return self.literal

        def pozovi(self):
            return self

    class FALSE(Token):
        literal = "F"

        def vrijednost(self, w):
            return False

        def ispis(self):
            return self.literal

        def pozovi(self):
            return self

    # Tokeni za svijetove i modele
    FORSIRA, NEFORSIRA, VRIJEDI, NEVRIJEDI = "|=", "|~", "=|", "~|"

    class SVIJET(Token):
        sljedbenici: "set(T.SVIJET)"
        činjenice: "set(T.PVAR)"

        def vrijednost(self):
            return self.sadržaj

        def ispis(self):
            za_ispis = self.sadržaj + ": {"
            for sljedbenik in self.sljedbenici:
                za_ispis += " " + sljedbenik.sadržaj
            za_ispis += "; "
            for pvar in self.činjenice:
                za_ispis += pvar.sadržaj + " "
            za_ispis += "} "
            return za_ispis.translate(subskript)

    class MODEL(Token):
        pvars: "set(T.PVAR)"
        nosač: "set(T.SVIJET)"

        def vrijednost(self):
            return self.sadržaj

        def ispis(self):
            za_ispis = self.sadržaj + ": {"
            for svijet in self.nosač:
                za_ispis += " " + svijet.sadržaj
            za_ispis += "; "
            for pvar in self.pvars:
                za_ispis += pvar.sadržaj + " "
            za_ispis += "} "
            return za_ispis.translate(subskript)

        def nađi_svijet(self, naziv):
            for svijet in self.nosač:
                if svijet.sadržaj == naziv:
                    return svijet
            return nenavedeno

        def nađi_pvar(self, naziv):
            for pvar in self.pvars:
                if pvar.sadržaj == naziv:
                    return pvar
            return nenavedeno

    class IMED(Token):
        def vrijednost(self):
            return str(self.sadržaj[1:-1])

    # Tokeni za jezik
    TOČKAZ, ZAREZ, V_OTV, V_ZATV, UPITNIK = ";,{}?"
    FOR, IF, ELSE, WHILE, FUN = "for", "if", "else", "while", "fun"
    ISPIŠI, UNESI, KORISTI, VRATI = "ispiši", "unesi", "koristi", "vrati"
    INT, NAT, FORMULA = "int", "nat", "formula"
    JEDNAKO, PLUS, MINUS, PUTA, NA = "=+-*^"
    JJEDNAKO, PLUSP, PLUSJ, MINUSM, MINUSJ = "==", "++", "+=", "--", "-="
    MANJE, MMANJE, VEĆE = "<", "<<", ">"

    class BROJ(Token):
        def vrijednost(self):
            return int(self.sadržaj)

        def ispis(self):
            return self.sadržaj

    class IME(Token):
        def vrijednost(self):
            return rt.mem[self][0] if fun == "__main__" else rt.lm[fun][self][0]

        def tip_varijable(self):
            return rt.mem[self][1] if fun == "__main__" else rt.lm[fun][self][1]

        def ispis(self):
            if self.tip_varijable() ^ {T.INT, T.NAT}:
                return self.vrijednost()
            else:
                return self.vrijednost().ispis()

    class IMEF(IME):
        pass

    class CONTINUE(Token):
        literal = "continue"

        def izvrši(self):
            raise PrekidContinue

    class BREAK(Token):
        literal = "break"

        def izvrši(self):
            raise PrekidBreak


# donje dvije klase sluze samo za lijepo ispisivanje poruke prilikom nekompatibilnih tipova
# napravio sam to tako da se lako moze prosirivati kada nove tipove budemo ubacivali
class Tip(enum.Enum):
    N = "NAT"
    Z = "INT"


class GreskaTipova:
    def krivi_tip(self, ime, tip1, tip2):
        raise SemantičkaGreška(
            f"IME '{ime}': tipovi ne odgovaraju: {tip1.name} vs. {tip2.name}"
        )


@lexer
def ml(lex):
    for znak in lex:
        if znak.isspace():
            lex.zanemari()
        elif znak == "[":
            lex >> "]"
            yield lex.token(T.BOX)
        elif znak == "<":
            if lex >= ">":
                yield lex.token(T.DIAMOND)
            elif lex >= "<":
                yield lex.token(T.MMANJE)
            elif lex >= "-":
                lex >> ">"
                yield lex.token(T.BIKOND)
            else:
                yield lex.token(T.MANJE)
        elif znak.isdecimal():
            lex.prirodni_broj(znak)
            yield lex.token(T.BROJ)
        elif znak == "-":
            if lex >= ">":
                yield lex.token(T.KOND)
            elif lex >= "-":
                yield lex.token(T.MINUSM)
            elif lex >= "=":
                yield lex.token(T.MINUSJ)
            elif lex >= "|":
                lex >> "|"
                yield lex.token(T.VRIJEDI)
            else:
                yield lex.token(T.MINUS)
        elif znak == "+":
            if lex >= "+":
                yield lex.token(T.PLUSP)
            elif lex >= "=":
                yield lex.token(T.PLUSJ)
            else:
                yield lex.token(T.PLUS)
        elif znak == "~":
            if lex >= "|":
                yield lex.token(T.NEVRIJEDI if lex >= "|" else T.NEVRIJEDI)
            else:
                yield lex.token(T.NEG)
        elif znak == "=":
            if lex >= "|":
                yield lex.token(T.VRIJEDI)
            else:
                yield lex.token(T.JJEDNAKO if lex >= "=" else T.JEDNAKO)
        elif znak == "|":
            if lex >= "=":
                yield lex.token(T.FORSIRA)
            elif lex >= "~":
                yield lex.token(T.NEFORSIRA)
            elif lex >= "|":
                if lex >= "-":
                    yield lex.token(T.FORSIRA)
                elif lex >= "~":
                    yield lex.token(T.NEFORSIRA)
            else:
                yield lex.token(T.DISJ)
        elif znak == "/":
            lex >> "/"
            lex - "\n"
            lex.zanemari()
        elif znak == "#":
            lex >> str.isalpha
            lex * {str.isalnum, "_"}
            yield lex.token(T.IME)
        elif znak == "$":
            lex + {str.isalnum, "_"}
            yield lex.token(T.PVAR)
        elif znak == "@":
            lex + {str.isalnum, "_"}
            yield lex.token(T.SVIJET)
        elif znak == "_":
            lex + {str.isalnum, "_"}
            yield lex.token(T.IMEF)
        elif znak.isupper():
            lex * {str.isalnum, "_"}
            yield lex.literal_ili(T.MODEL)
        elif znak == '"' or znak == "'":
            lex + (lambda char: char != znak and char != ".")
            lex >> "."
            lex >> "m"
            lex >> "i"
            lex >> "r"
            lex >> znak
            yield lex.token(T.IMED)
        elif znak.isalnum():
            lex * {str.isalnum, "_"}
            yield lex.literal_ili(T.IME)
        else:
            yield lex.literal(T)


### BKG ###

# start -> naredbe naredba
# naredbe -> '' | naredbe naredba | naredbe funkcija
# naredba -> petlja | grananje | pridruživanje TOČKAZ | deklaracija TOČKAZ | BREAK TOČKAZ | CONTINUE TOČKAZ
# naredba -> ispis TOČKAZ | unos TOČKAZ | forsira TOČKAZ | vrijedi TOČKAZ | provjera TOČKAZ | koristi TOČKAZ
# naredba -> SPREMI MODEL TOČKAZ | poziv_funkcije TOČKAZ | vrati TOČKAZ | TOČKAZ

# funkcija -> FUN IMEF O_OTV parametri? O_ZATV blok
# parametri -> tip IME | parametri ZAREZ tip IME
# poziv_funkcije -> IMEF O_OTV IME* O_ZATV
# pridruživanje -> IME (formule) JEDNAKO poziv_funkcije TOČKAZ
# vrati -> VRATI (TRUE | FALSE) TOČKAZ

# petlja -> for blok | FOREACH (SVIJET | PVAR) blok
# for -> FOR O_OTV IME# JEDNAKO izraz TOČKAZ IME# for_operator izraz TOČKAZ IME# promjena O_ZATV
# for_operator -> MANJE | VEĆE
# blok -> V_OTV naredbe V_ZATV | naredba

# izraz -> član | izraz (PLUS|MINUS) član
# član -> faktor | član PUTA faktor | član DIJ faktor | član OSTATAK faktor
# faktor -> baza | baza NA faktor | MINUS faktor
# baza -> BROJ | IME(aritmetičkog tipa) | O_OTV izraz O_ZATV
# promjena -> PLUSP | MINUSM | PLUSJ izraz | MINUSJ izraz
# varijabla -> IME | BROJ

# grananje -> IF O_OTV uvjet O_ZATV blok (ELSE blok)?
# uvjet -> varijabla | varijabla if_operator varijabla | IME (formule) JJEDNAKO IME (formule) | provjera
# if_operator -> JJEDNAKO | MANJE | VEĆE

# ispis -> ISPIŠI varijable
# varijable -> '' | varijable MMANJE ispis_varijabla
# ispis_varijabla -> IME | BROJ | NR

# tip -> INT | NAT | FORMULA
# pridruživanje -> IME (aritmetičkog tipa) JEDNAKO izraz
# pridruživanje -> IME (formule) JEDNAKO IME (formule) | IME (formule) JEDNAKO poziv_funkcije
# deklaracija -> tip (formule) IME JEDNAKO formula | tip (aritm.) IME JEDNAKO izraz

# formula -> PVAR | TRUE | FALSE | IME (formule)
# formula -> NEG formula | DIAMOND formula | BOX formula | O_OTV formula binvez formula O_ZATV
# binvez -> KONJ | DISJ | KOND | BIKOND

# forsira -> SVIJET (FORSIRA | NEFORSIRA) PVAR
# forsira -> SVIJET (FORSIRA | NEFORSIRA) V_OTV lista_pvar V_ZATV
# lista_pvar -> PVAR | PVAR ZAREZ lista_pvar

# vrijedi -> PVAR (VRIJEDI | NEVRIJEDI) SVIJET
# vrijedi -> PVAR (VRIJEDI | NEVRIJEDI) V_OTV lista_svijet V_ZATV
# lista_svijet -> SVIJET | SVIJET ZAREZ lista_svijet

# provjera -> formula UPITNIK SVIJET
# koristi -> KORISTI MODEL V_OTV lista_svijet TOČKAZ lista_pvar V_ZATV
# unos -> MODEL lista_datoteka
# lista_datoteka -> '' | lista_datoteka MMANJE IMED


class P(Parser):
    def start(p):
        p.funkcije = Memorija(redefinicija=False)
        naredbe = [p.naredba()]
        while not p > KRAJ:
            if p >= T.FUN:
                funkcija = p.funkcija()
                p.funkcije[funkcija.ime] = funkcija
            naredbe.append(p.naredba())
        return Program(naredbe)

    def naredba(p):
        if p > T.FOR:
            return p.for_petlja()
        if p > T.ISPIŠI:
            return p.ispis()
        if p > T.IF:
            return p.grananje()
        if p > {T.INT, T.NAT, T.FORMULA}:
            return p.deklaracija()
        if ime := p >= T.IME:
            if p >= T.JEDNAKO:
                return p.pridruživanje(ime)
            if p >= T.UPITNIK:
                return p.provjera(ime)
        if p > T.SVIJET:
            return p.forsira()
        if p > T.PVAR:
            return p.vrijedi()
        if p > T.KORISTI:
            return p.koristi()
        if p > T.UNESI:
            return p.unos()
        if p >= T.VRATI:
            return Vrati(p.formula())
        if br := p >= T.BREAK:
            p >> T.TOČKAZ
            return br
        if cont := p >= T.CONTINUE:
            p >> T.TOČKAZ
            return cont
        return p.formula()

    def koristi(p):
        p >> T.KORISTI
        model = p >> T.MODEL
        model.nosač = set()
        model.pvars = set()
        p >> T.V_OTV
        svijet = p >> T.SVIJET
        svijet.sljedbenici = set()
        svijet.činjenice = set()
        model.nosač.add(svijet)
        while p >= T.ZAREZ:
            svijet = p >> T.SVIJET
            svijet.sljedbenici = set()
            svijet.činjenice = set()
            model.nosač.add(svijet)
        p >> T.TOČKAZ
        pvar = p >> T.PVAR
        model.pvars.add(pvar)
        while p >= T.ZAREZ:
            pvar = p >> T.PVAR
            model.pvars.add(pvar)
        p >> T.V_ZATV
        p >> T.TOČKAZ
        return Koristi(model)

    def unos(p):
        p >> T.UNESI
        datoteke = []
        while p >= T.MMANJE:
            datoteke.append(p >> T.IMED)
        p >> T.TOČKAZ
        return Unos(datoteke)

    def funkcija(p):
        ime_funkcije = p >> T.IMEF
        p >> T.O_OTV
        parametri = []
        if param_tip := p >= {T.INT, T.NAT, T.FORMULA}:
            param_ime = p >> T.IME
            parametri.append([param_ime, param_tip])
        while p >= T.ZAREZ:
            parametri.append([p >> {T.INT, T.NAT, T.FORMULA}, p >> T.IME])
        p >> T.O_ZATV
        return Funkcija(ime_funkcije, parametri, p.blok())

    def provjera(p, ime):
        w = p >> T.SVIJET
        p >> T.TOČKAZ
        return Provjera(w, ime)

    def for_petlja(p):
        kriva_varijabla = SemantičkaGreška(
            "Sva tri dijela for-petlje moraju imati istu varijablu"
        )

        p >> T.FOR, p >> T.O_OTV
        i = (
            p >> T.IME
        )  # NAPOMENA: mozda ovdje ipak stavit uvjet da ime mora imati # kao prvi znak
        p >> T.JEDNAKO
        početak = p.izraz()  ## u AST for_petlja pazimo ako se vrati ime formule
        p >> T.TOČKAZ

        if (p >> T.IME) != i:
            raise kriva_varijabla
        for_operator = p >> {
            T.MANJE,
            T.VEĆE,
        }  # ovdje se lako doda ako hocemo podrzati jos neke operatore
        granica = p.izraz()  ## u AST for_petlja pazimo ako se vrati ime formule
        p >> T.TOČKAZ

        if (p >> T.IME) != i:
            raise kriva_varijabla
        if minus_ili_plus := p >= {T.PLUSP, T.MINUSM}:
            promjena = nenavedeno
        elif minus_ili_plus := p >> {T.PLUSJ, T.MINUSJ}:
            promjena = p.izraz()  ## u AST for_petlja pazimo ako se vrati ime formule
        p >> T.O_ZATV

        blok = p.blok()
        return For_Petlja(
            i, početak, for_operator, granica, promjena, minus_ili_plus, blok
        )

    # blok može biti ili jedna naredba ili {naredbe*} !!!
    def blok(p):
        naredbe = []
        if p >= T.V_OTV:
            while not p >= T.V_ZATV:
                naredbe.append(p.naredba())
        else:
            naredbe.append(p.naredba())

        return Blok(naredbe)

    def ispis(p):
        p >> T.ISPIŠI
        varijable = []
        while p >= T.MMANJE:
            varijable.append(p >> {T.IME, T.BROJ, T.SVIJET, T.MODEL})
        p >> T.TOČKAZ
        return Ispis(varijable)

    def grananje(p):
        p >> T.IF, p >> T.O_OTV
        uvjet = p.uvjet()
        p >> T.O_ZATV
        if_blok = p.blok()
        else_blok = nenavedeno
        if p >= T.ELSE:
            else_blok = p.blok()
        return Grananje(uvjet, if_blok, else_blok)

    def uvjet(p):
        lijeva_strana = p >> {T.IME, T.BROJ}
        op = p >> {
            T.JJEDNAKO,
            T.MANJE,
            T.VEĆE,
            T.UPITNIK,
        }  # ovdje se dodaju if_operatori ako zelimo prosiriti
        desna_strana = p >> {T.IME, T.BROJ, T.SVIJET}
        return Uvjet(lijeva_strana, op, desna_strana)

    def pridruživanje(p, ime_varijable):
        # provjera koji nam je tip s lijeve strane (samo formule još dolaze)
        if ime_varijable.sadržaj[0] == "#":  ## ako pridružujemo aritmetičkom izrazu
            vrijednost = p.izraz()
        elif ime_varijable.sadržaj[0].islower():  ## ako pridružujemo formuli
            vrijednost = p.formula()
        else:
            raise SintaksnaGreška(
                f"Pridruživanje nije podržano za varijablu {ime_varijable.sadržaj}"
            )
        p >> T.TOČKAZ
        return Pridruživanje(ime_varijable, vrijednost)

    def deklaracija(p):
        tip = p >> {
            T.INT,
            T.NAT,
            T.FORMULA,
        }  # kad budemo imali vise tipova, onda cemo imati p > {T.INT, T.FORMULA...}
        ime = p >> T.IME
        p >> T.JEDNAKO
        if tip ^ {T.INT, T.NAT}:  ## ako deklariramo aritmetički izraz
            vrij = p.izraz()
        elif tip ^ T.FORMULA:  ## ako deklariramo varijablu
            vrij = p.formula()
        else:
            raise SintaksnaGreška(f"Za tip {tip} nije podržana deklaracija!")
        p >> T.TOČKAZ
        return Deklaracija(tip, ime, vrij)

    def izraz(p):
        t = p.član()
        while op := p >= {T.PLUS, T.MINUS}:
            t = Op(op, t, p.član())
        return t

    def član(p):
        t = p.faktor()
        while op := p >= T.PUTA:
            t = Op(op, t, p.faktor())
        return t

    def faktor(p):
        if op := p >= T.MINUS:
            return Op(op, nenavedeno, p.faktor())
        baza = p.baza()
        if p >= T.NA:
            return Potencija(baza, p.faktor())
        else:
            return baza

    def baza(p):
        if elementarni := p >= {T.BROJ, T.IME}:
            return elementarni
        elif p >> T.O_OTV:
            u_zagradi = p.izraz()
            p >> T.O_ZATV
            return u_zagradi

    def formula(p):
        if varijabla := p >= {T.PVAR, T.IME}:
            return varijabla
        elif konstanta := p >= {T.TRUE, T.FALSE}:
            return konstanta
        elif p > {T.BOX, T.DIAMOND, T.NEG}:
            klasa, ispod = p.unvez(), p.formula()
            return klasa(ispod)
        elif p >= T.O_OTV:
            l, klasa, d = p.formula(), p.binvez(), p.formula()
            p >> T.O_ZATV
            return klasa(l, d)
        elif ime_funkcije := p >= T.IMEF:
            vrijednosti = []
            p >> T.O_OTV
            if arg := p >= T.IME:
                vrijednosti.append(arg)
            while p >= T.ZAREZ:
                vrijednosti.append(p >> T.IME)
            p >> T.O_ZATV
            return Poziv(p.funkcije[ime_funkcije], vrijednosti)
        raise SintaksnaGreška("Nepoznata naredba")

    def unvez(p):
        if p >= T.NEG:
            return Negacija
        elif p >= T.DIAMOND:
            return Diamond
        elif p >= T.BOX:
            return Box
        else:
            raise p.greška()

    def binvez(p):
        if p >= T.KONJ:
            return Konjunkcija
        elif p >= T.DISJ:
            return Disjunkcija
        elif p >= T.KOND:
            return Kondicional
        elif p >= T.BIKOND:
            return Bikondicional
        else:
            raise p.greška()

    def forsira(p):
        w = p >> T.SVIJET
        simb = p >> {T.FORSIRA, T.NEFORSIRA}
        lista_pvar = []
        if p >= T.V_OTV:
            lista_pvar.append(p >> T.PVAR)
            while p >= ZAREZ:
                lista_pvar.append(p >> T.PVAR)
            p >> T.V_ZATV
        else:
            lista_pvar.append(p >> T.PVAR)
        p >> T.TOČKAZ
        return Forsira(w, lista_pvar, simb)

    def vrijedi(p):
        pvar = p >> T.PVAR
        simb = p >> {T.VRIJEDI, T.NEVRIJEDI}
        lista_svijet = []
        if p >= T.V_OTV:
            lista_svijet.append(p >> T.SVIJET)
            while p >= ZAREZ:
                lista_svijet.append(p >> T.SVIJET)
            p >> T.V_ZATV
        else:
            lista_svijet.append(p >> T.SVIJET)
        p >> T.TOČKAZ
        return Vrijedi(pvar, lista_svijet, simb)


class Program(AST):
    naredbe: "barem jedna naredba"

    def izvrši(program):
        try:
            for naredba in program.naredbe:
                naredba.izvrši()
        except PrekidBreak:
            raise SemantičkaGreška("Nedozvoljen break izvan petlje!")
        except PrekidContinue:
            raise SemantičkaGreška("Nedozvoljen continue izvan petlje!")


class Koristi(AST):
    model: T.MODEL

    def izvrši(self):
        rt.mem["using"] = self.model


class Unos(AST):
    datoteke: "list(T.IMED)"

    def izvrši(self):
        for dat in self.datoteke:
            with open(dat.vrijednost(), newline="") as csv_dat:
                reader = csv.reader(csv_dat, delimiter=" ")
                prvi_red = next(reader)
                tip = prvi_red[0][:3]
                if tip == "rel":
                    svjetovi = []
                elif tip == "val":
                    pvars = []
                else:
                    raise IOError('Neispravan tip datoteke: mora biti "rel" ili "val".')
                    return -1
                if tip == "rel":
                    for i in range(1, len(prvi_red)):
                        if novi := rt.mem["using"].nađi_svijet("@" + prvi_red[i]):
                            if novi in svjetovi:
                                raise IOError("Svijet se navodi dvaput.")
                            else:
                                svjetovi.append(novi)
                        else:
                            raise IOError("Svijet nije deklariran.")
                else:
                    for i in range(1, len(prvi_red)):
                        if nova := rt.mem["using"].nađi_pvar("$" + prvi_red[i]):
                            if nova in pvars:
                                raise IOError(
                                    "Propozicionalna varijabla navodi se dvaput."
                                )
                            else:
                                pvars.append(nova)
                        else:
                            raise IOError("Propozicionalna varijabla nije deklarirana.")
                for redak in reader:
                    lijevi = rt.mem["using"].nađi_svijet("@" + redak[0])
                    for i in range(1, len(redak)):
                        if str.upper(redak[i][0]) in ["T", "1", "Y", "I", "D", "O"]:
                            if tip == "rel":
                                lijevi.sljedbenici.add(svjetovi[i - 1])
                            else:
                                lijevi.činjenice.add(pvars[i - 1])
                        elif str.upper(redak[i][0]) in ["F", "0", "N", "L", "N", "X"]:
                            if tip == "rel":
                                lijevi.sljedbenici.discard(svjetovi[i - 1])
                            else:
                                lijevi.činjenice.discard(pvars[i - 1])
                        else:
                            raise IOError("Neispravna oznaka istinitosti u tablici.")


class Funkcija(AST):
    ime: "T.IMEF"
    parametri: "[IME, TIP]*"
    blok: "naredba*"

    def pozovi(self, vrijednosti):
        if len(vrijednosti) != len(self.parametri):
            raise GreškaIzvođenja(
                f"{self.ime} mora primiti {len(self.parametri)} parametara!"
            )
        fun = self.ime
        rt.lm[self.ime] = Memorija()
        for i in range(len(vrijednosti)):
            Deklaracija(
                self.parametri[i][1], self.parametri[i][0], vrijednosti[i]
            ).izvrši()
        ret = T.FALSE
        try:
            self.blok.izvrši()
        except Povratak as exc:
            ret = exc.preneseno
        del rt.lm[self.ime]
        fun = "__main__"
        return ret


class Poziv(AST):
    funkcija: "Funkcija"
    vrijednosti: "IME*"

    def pozovi(self):
        return self.funkcija.pozovi([arg.vrijednost() for arg in self.vrijednosti])


class Vrati(AST):
    povratna_vrij: "formula"

    def izvrši(self):
        raise Povratak(self.povratna_vrij.pozovi())


class For_Petlja(AST):
    varijabla: "IME"
    početak: "izraz"
    operator: "(<|>)"  # mogli bi bit još podržani <= ili >=, ali nije da time dobivamo na ekspresivnosti jezika; eventualno dodati !=
    granica: "izraz"
    promjena: "izraz?"
    predznak: "(+|-)"
    blok: "naredba*"

    def izvrši(petlja):
        # je formula s desne strane semantička ili sintaksna greška?
        neadekvatna_desna_strana = SemantičkaGreška(
            "Greška: nad formulama nisu definirane aritmetičke operacije!"
        )
        kv = petlja.varijabla

        # donja tri uvjeta provjeravaju da se s desne strane ne nađe formula
        if petlja.početak ^ T.IME and petlja.početak.sadržaj[0] != "#":
            raise neadekvatna_desna_strana
        elif petlja.granica ^ T.IME and petlja.granica.sadržaj[0] != "#":
            raise neadekvatna_desna_strana
        elif petlja.promjena ^ T.IME and petlja.promjena.sadržaj[0] != "#":
            raise neadekvatna_desna_strana

        memo = rt.mem if fun == "__main__" else rt.lm[fun]
        memo[kv] = [
            petlja.početak.vrijednost()
        ]  # NAPOMENA: ovdje ime moze biti bilo koje i ne mora biti deklarirano (vidjet sta ako neko unese formulu npr.); vidi jel stvara probleme
        while (
            memo[kv][0] < petlja.granica.vrijednost()
            if petlja.operator ^ T.MANJE
            else memo[kv][0] > petlja.granica.vrijednost()
        ):
            try:
                petlja.blok.izvrši()
            except PrekidBreak:
                break
            except (
                PrekidContinue
            ):  # nazalost dupliciram kod radi ispravnog rada continue, kasnije mozemo popraviti
                prom = petlja.promjena
                if petlja.predznak ^ T.MINUSJ or petlja.predznak ^ T.MINUSM:
                    memo[kv][0] -= prom.vrijednost() if prom else 1
                else:
                    memo[kv][0] += prom.vrijednost() if prom else 1
                continue
            prom = petlja.promjena
            if petlja.predznak ^ T.MINUSJ or petlja.predznak ^ T.MINUSM:
                memo[kv][0] -= prom.vrijednost() if prom else 1
            else:
                memo[kv][0] += prom.vrijednost() if prom else 1


class Blok(AST):
    naredbe: "naredba*"

    def izvrši(blok):
        for naredba in blok.naredbe:
            naredba.izvrši()


class Ispis(AST):
    varijable: "IME*"

    def izvrši(ispis):
        for varijabla in ispis.varijable:
            if varijabla ^ {T.INT, T.NAT, T.FORMULA, T.BROJ, T.IME}:
                print(varijabla.ispis(), end=" ")
            elif varijabla ^ {T.SVIJET}:
                if svijet := rt.mem["using"].nađi_svijet(varijabla.sadržaj):
                    print(svijet.ispis())
                else:
                    raise SemantičkaGreška(
                        f"Svijet {varijabla.sadržaj} nije deklariran."
                    )
            elif varijabla ^ {T.MODEL}:
                if rt.mem["using"].sadržaj == varijabla.sadržaj:
                    print(rt.mem["using"].ispis())
                else:
                    raise SemantičkaGreška(
                        f"Model {varijabla.sadržaj} nije trenutno u uporabi."
                    )
            else:
                raise SemantičkaGreška("Neočekivana varijabla za ispis!")
            ## ovo dobro ispisuje int, nat i formula; PAZI ZA MODEL I SVIJET


class Uvjet(AST):
    lijeva: "(IME|BROJ)"
    operator: "(==|<|>|?)"
    desna: "(IME|BROJ)"

    def ispunjen(
        uvjet,
    ):  # NAPOMENA: možda ovo dolje moze ostati i za tip formula (iako je glupo, bolje za njih samo ==, ali lako promijenimo sto zelimo); ponovno: definirati metodu vrijednost za formulu na koji nacin vec zelimo
        # ovo ispod prolazi za formule i s jedne i druge strane
        if uvjet.lijeva ^ T.IME and uvjet.lijeva.sadržaj[0].islower():
            if uvjet.operator ^ T.JEDNAKO:
                if uvjet.desna ^ T.IME and not uvjet.desna.sadržaj[0].islower():
                    raise SemantičkaGreška(
                        "Uspoređivanje formule s nekompatibilnim tipom!"
                    )
                else:
                    return uvjet.lijeva.ispis() == uvjet.desna.ispis()
            elif uvjet.operator ^ T.UPITNIK:
                if not uvjet.desna ^ T.SVIJET:
                    raise SemantičkaGreška("Provjera formule na nekompatibilnom tipu!")
                else:
                    return Provjera(uvjet.desna, uvjet.lijeva).vrijednost()
            else:
                raise SemantičkaGreška("Nepodržan operator na tipu formula!")

        # ovo ispod bez problema prolazi za aritmetičke vrijednosti s lijeve i desne strane
        if uvjet.operator ^ T.JJEDNAKO:
            return uvjet.lijeva.vrijednost() == uvjet.desna.vrijednost()
        elif uvjet.operator ^ T.VEĆE:
            return uvjet.lijeva.vrijednost() > uvjet.desna.vrijednost()
        elif uvjet.operator ^ T.MANJE:
            return uvjet.lijeva.vrijednost() < uvjet.desna.vrijednost()
        else:
            raise SintaksnaGreška("Nepodržan if-uvjet!")


class Grananje(AST):
    uvjet: "log"
    onda: "naredba"
    inače: "naredba"

    def izvrši(grananje):
        if grananje.uvjet.ispunjen():
            grananje.onda.izvrši()
        elif grananje.inače:
            grananje.inače.izvrši()


class Pridruživanje(AST):
    varijabla: "IME"
    vrij: "(varijabla | BROJ)"

    def izvrši(pridruživanje):
        memo = rt.mem if fun == "__main__" else rt.lm[fun]
        if pridruživanje.varijabla in memo:
            if (
                pridruživanje.varijabla.sadržaj[0] == "#"
            ):  # ovo se odnosi na pridruživanje aritmetičkim varijablama (int, nat)
                if pridruživanje.vrij ^ T.IME and pridruživanje.vrij.sadržaj[0] != "#":
                    raise SemantičkaGreška(
                        "Greška: nepravilno pridruživanje aritmetičkoj varijabli!"
                    )
                elif (
                    memo[pridruživanje.varijabla][1] ^ T.NAT
                    and pridruživanje.vrij.vrijednost() < 0
                ):
                    greska = GreskaTipova()
                    greska.krivi_tip(pridruživanje.varijabla.sadržaj, Tip.N, Tip.Z)
                else:
                    memo[pridruživanje.varijabla][0] = pridruživanje.vrij.vrijednost()
            elif pridruživanje.varijabla.sadržaj[
                0
            ].islower():  # ovo se odnosi na pridruživanje formulama
                if (
                    pridruživanje.vrij ^ T.IME
                    and not pridruživanje.vrij.sadržaj[0].islower()
                ):
                    raise SemantičkaGreška(
                        "Greška: nepravilno pridruživanje varijabli formula!"
                    )
                else:
                    memo[pridruživanje.varijabla][0] = pridruživanje.vrij.pozovi()
        else:
            return memo[
                pridruživanje.varijabla
            ]  # jer ovo vraca bas ono upozorenje koje nam treba


class Deklaracija(AST):
    tip: "neki od podrzanih tipova"
    ime: "IME"
    vrij: "varijabla | BROJ"

    # prilikom deklaracije, kljucevi se preslikavaju u listu s dva elementa (par): vrijednost, tip
    def izvrši(deklaracija):
        memo = rt.mem if fun == "__main__" else rt.lm[fun]
        if deklaracija.ime in memo:  ## ako se dogodila redeklaracija
            raise deklaracija.ime.redeklaracija()
        elif deklaracija.tip ^ {T.NAT, T.INT}:  ## ako deklariramo aritmeticki tip
            if deklaracija.tip ^ T.NAT and deklaracija.vrij.vrijednost() < 0:
                tip1 = Tip.N
                tip2 = Tip.Z
                greska = GreskaTipova()
                greska.krivi_tip(deklaracija.ime.sadržaj, tip1, tip2)
            elif not deklaracija.ime.sadržaj[0] == "#":
                raise SemantičkaGreška("Neispravan naziv varijable aritmetičkog tipa!")
            elif deklaracija.vrij ^ T.IME and not deklaracija.vrij.sadržaj[0] == "#":
                raise SemantičkaGreška(
                    f"Nepodudaranje tipova prilikom deklaracije aritmetičke varijable {deklaracija.ime.sadržaj}!"
                )
            else:
                memo[deklaracija.ime] = [deklaracija.vrij.vrijednost(), deklaracija.tip]
        elif deklaracija.tip ^ T.FORMULA:  ## ako deklariramo formulu
            if deklaracija.vrij ^ T.IME and not deklaracija.vrij.sadržaj[0].islower():
                raise SemantičkaGreška(
                    f"Nepodudaranje tipova prilikom deklaracije formule {deklaracija.ime.sadržaj}!"
                )
            elif (
                not deklaracija.ime.sadržaj.islower()
                or deklaracija.ime.sadržaj[0] == "#"
            ):
                raise SemantičkaGreška("Neispravan naziv varijable tipa formula!")
            else:
                memo[deklaracija.ime] = [deklaracija.vrij.pozovi(), deklaracija.tip]
        else:
            raise SemantičkaGreška(
                "Nepodržani tip varijable!"
            )  # ne bi smjelo do ovoga doći jer za to imamo provjeru u odg. metodi


class Op(AST):
    op: "T"
    lijevo: "izraz?"
    desno: "izraz"

    def vrijednost(self):
        if self.lijevo is nenavedeno:
            l = 0
        else:
            l = self.lijevo.vrijednost()
        o, d = self.op, self.desno.vrijednost()
        if o ^ T.PLUS:
            return l + d
        elif o ^ T.MINUS:
            return l - d
        elif o ^ T.PUTA:
            return l * d


class Potencija(AST):
    baza: "elementarni | izraz"
    eksponent: "faktor"

    def vrijednost(self):
        return self.baza.vrijednost() ** self.eksponent.vrijednost()


class Unarna(AST):
    ispod: "formula"

    def optim(self):
        klasa = type(self)
        ispod_opt = self.ispod.optim()
        if ispod_opt ^ Negacija and self ^ Negacija:
            return ispod_opt.ispod
        else:
            return klasa(ispod_opt)

    def optim1(self):
        klasa = type(self)
        if isinstance(self, Diamond):
            ispod_opt = self.ispod.optim1()
            nova_klasa = Negacija(ispod_opt)
            nova_klasa = Box(nova_klasa)
            return Negacija(nova_klasa)
        else:
            return self

    def __eq__(self, o):
        return jednaki(self.ispod, o.ispod)

    def ispis(self):
        return self.veznik + self.ispod.ispis()

    # provjeri ovo
    def izvrši(self):
        return self.ispis()

    def pozovi(self):
        return self


class Negacija(Unarna):
    veznik = "¬"

    def vrijednost(self, w):
        return not self.ispod.vrijednost(w)


class Diamond(Unarna):
    veznik = "◆"

    def vrijednost(self, w):
        for sljedbenik in w.sljedbenici:
            if self.ispod.vrijednost(sljedbenik):
                return True
        return False


class Box(Unarna):
    veznik = "■"

    def vrijednost(self, w):
        for sljedbenik in w.sljedbenici:
            if not self.ispod.vrijednost(sljedbenik):
                return False
        return True


class Binarna(AST):
    lijevo: "formula"
    desno: "formula"

    def optim(self):
        klasa = type(self)
        lijevo_opt = self.lijevo.optim()
        desno_opt = self.desno.optim()
        return klasa(lijevo_opt, desno_opt)

    def optim1(self):
        lijevo_opt = self.lijevo.optim1()
        desno_opt = self.desno.optim1()
        if isinstance(self, Konjunkcija):
            nova_klasa = Negacija(desno_opt)
            nova_klasa = Kondicional(lijevo_opt, nova_klasa)
            return Negacija(nova_klasa)
        elif isinstance(self, Disjunkcija):
            nova_klasa = Negacija(lijevo_opt)
            return Kondicional(nova_klasa, desno_opt)
        elif isinstance(self, Bikondicional):
            lijeva_klasa = Kondicional(lijevo_opt, desno_opt)
            desna_klasa = Kondicional(desno_opt, lijevo_opt)
            desna_klasa = Negacija(desna_klasa)
            nova_klasa = Kondicional(lijeva_klasa, desna_klasa)
            return Negacija(nova_klasa)
        else:
            return self

    def __eq__(self, o):
        return jednaki(self.lijevo, o.lijevo) and jednaki(self.desno, o.desno)

    def ispis(self):
        return "(" + self.lijevo.ispis() + self.veznik + self.desno.ispis() + ")"

    # provjeri ovo
    def izvrši(self):
        return self.ispis()

    def pozovi(self):
        return self


class Disjunkcija(Binarna):
    veznik = "∨"

    def vrijednost(self, w):
        return self.lijevo.vrijednost(w) or self.desno.vrijednost(w)


class Konjunkcija(Binarna):
    veznik = "∧"

    def vrijednost(self, w):
        return self.lijevo.vrijednost(w) and self.desno.vrijednost(w)


class Kondicional(Binarna):
    veznik = "→"

    def vrijednost(self, w):
        return self.lijevo.vrijednost(w) <= self.desno.vrijednost(w)


class Bikondicional(Binarna):
    veznik = "↔"

    def vrijednost(self, w):
        return self.lijevo.vrijednost(w) == self.desno.vrijednost(w)


class Provjera(AST):
    svijet: T.SVIJET
    ime: "ime formule"

    def izvrši(self):
        if svijet := rt.mem["using"].nađi_svijet(self.svijet.sadržaj):
            t = " ⊩ " if self.ime.vrijednost().vrijednost(svijet) else " ⊮ "
            print(svijet.sadržaj + t + self.ime.vrijednost().ispis())
        else:
            raise SemantičkaGreška(f"Svijet {self.svijet.sadržaj} nije deklariran.")

    def vrijednost(self):
        if svijet := rt.mem["using"].nađi_svijet(self.svijet.sadržaj):
            return self.ime.vrijednost().vrijednost(svijet)
        else:
            raise SemantičkaGreška(f"Svijet {self.svijet.sadržaj} nije deklariran.")


class Forsira(AST):
    svijet: T.SVIJET
    pvars: "list(T.PVAR)"
    simbol: "T.FORSIRA | T.NEFORSIRA"

    def izvrši(self):
        if svijet := rt.mem["using"].nađi_svijet(self.svijet.sadržaj):
            for pvar in self.pvars:
                if self.simbol ^ T.FORSIRA:
                    svijet.činjenice.add(pvar)
                elif self.simbol ^ T.NEFORSIRA:
                    svijet.činjenice.discard(pvar)
        else:
            raise SemantičkaGreška(f"Svijet {self.svijet.sadržaj} nije deklariran.")


class Vrijedi(AST):
    pvar: T.PVAR
    svjetovi: "list(T.SVIJET)"
    simbol: "T.VRIJEDI | T.NEVRIJEDI"

    def izvrši(self):
        for s in self.svjetovi:
            if svijet := rt.mem["using"].nađi_svijet(s.sadržaj):
                if self.simbol ^ T.VRIJEDI:
                    svijet.činjenice.add(self.pvar)
                elif self.simbol ^ T.NEVRIJEDI:
                    svijet.činjenice.discard(self.pvar)
            else:
                raise SemantičkaGreška(f"Svijet {self.svijet.sadržaj} nije deklariran.")


def optimiziraj(formula):
    """Pretvara formulu (AST) u formulu koja od veznika ima samo kondicional i negaciju; prije te pretvorbe su još uklonjene dvostruke negacije"""

    nova = (
        formula.optim()
    )  # prije optimizacije da dobijemo samo negaciju i kondicional uklanjamo redundantne negacije
    nova = (
        nova.optim1()
    )  # kreiramo ekvivalentnu formulu koja ima samo negaciju, kondicional i box od veznika
    return (
        nova.optim()
    )  # nakon dobivanja ekvivalentne formule opet se mogu javiti redundantne negacije pa ih zato još jednom mičemo


def jednaki(f1, f2):
    klasa1 = type(f1)
    klasa2 = type(f2)

    if klasa1 != klasa2:
        return False
    return f1 == f2


# provjerava je li formula f shema aksioma A1
# NISAM TESTIRAO jer još nemamo implementiranu varijablu tipa formula
def shemaA1(f):
    optimiziraj(f)
    f.ispis()
    print()
    if not f ^ Kondicional:
        return False
    lijeva_formula = f.lijevo
    desna_formula = f.desno
    if not desna_formula ^ Kondicional:
        return False
    return lijeva_formula.ispis() == desna_formula.desna.ispis()


# ml('''
#     formula f = ($P0 -> $P1);
#     formula g = $P0;
#     formula d = ($P0 -> $P1);
#     int #b = 1;
#     if (f == f) {
#         ispiši << #b << #b;
#     }
#     int #a = #b;
#     nat #r = (3*4)+5;
#     formula c = $P0;
#     ispiši << f << #a << g << d << c;
#     #a = 1;
#     for (i = 1; i < 5; i += 2) ispiši<<i; // for (i = f; ...) javlja grešku
# ''')

rt.mem = Memorija()
fun = "__main__"
rt.lm = Memorija()

# prikaz(kod := P('''
#     koristi M { @svijet, @world, @za_warudo, @el_mundo; $pada_kisa, $ulice_su_mokre, $prolazi_cisterna };
#     unesi << "rel_dat.mir" << "val_dat.mir";
#     formula a_1 = ($pada_kisa -> $ulice_su_mokre);
#     formula nuzno_a1 = []a_1;
#     ispiši << M;
#     ispiši<<@world;
#     a_1 ? @world;
#     @world |~ $ulice_su_mokre;
#     ispiši<<@world; //zbog gornje linije bi se $ulice_su_mokre trebale maknuti iz cinjenica
#     a_1 ? @world;
#     ispiši << @world;
#     ispiši << @el_mundo;
#     $pada_kisa =| @world;
#     a_1 ? @world;
#     formula r = <>$ulice_su_mokre;
#     ispiši<<r;
#     r ? @world;
# '''))
# kod.izvrši()

# ml('''
#     koristi M { @svijet, @world, @za_warudo, @el_mundo; $pada_kisa, $ulice_su_mokre, $prolazi_cisterna };
#     M << "rel_dat.mir" << "val_dat.mir";
#     int br = 5;
#     formula a_1 = ($pada_kisa -> $ulice_su_mokre);
#     formula nuzno_a1 = []a_1;
#     // ispiši << a_1 ? @svijet << a_1 ? @world;
#     ispiši << M;
#     a_1 ? @world;
#     // ispiši << nuzno_a1 ? @el_mundo << nuzno_a1 ? @za_warudo;
# ''')

prikaz(
    kod := P(
        """
    koristi M { @svijet, @world, @za_warudo, @el_mundo; $pada_kisa, $ulice_su_mokre, $prolazi_cisterna };
    unesi << "rel_dat.mir" << "val_dat.mir";
    int #br = 5;
    formula a_1 = ($pada_kisa -> $ulice_su_mokre);
    formula nuzno_a1 = []a_1;
    // ispiši << a_1 ? @svijet << a_1 ? @world;
    ispiši << M;
    a_1 ? @world;
    ispiši << @world;
    @world |~ $ulice_su_mokre;
    a_1 ? @world;
    ispiši << @world;
    $pada_kisa =| @world;
    ispiši << @world;
    a_1 ? @world;
    formula asda = $P0;
    formula r = <>$ulice_su_mokre;
    formula ul = $ulice_su_mokre;
    ispiši << @el_mundo;
    fun _pr(int #a, formula f) {
        ispiši << @world;
        f ? @world;
    }
    ul ? @world;
    ul ? @el_mundo;
    if (r ? @world) ispiši << @za_warudo;
    formula k = _pr(#br, a_1);
    formula l = []k;
    k ? @world;
    //ispiši << @world;
    // ispiši << nuzno_a1 ? @el_mundo << nuzno_a1 ? @za_warudo;
"""
    ),
    8,
)
kod.izvrši()
