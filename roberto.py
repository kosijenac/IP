from vepar import *

subskript = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')
class PrekidBreak(NelokalnaKontrolaToka): """Signal koji šalje naredba break."""
class PrekidContinue(NelokalnaKontrolaToka): """Signal koji šalje naredba continue"""

class T(TipoviTokena):
    NEG, KONJ, DISJ, O_OTV, O_ZATV = '~&|()'
    KOND, BIKOND = '->', '<->'
    BOX, DIAMOND = '[]', '<>'

    class PVAR(Token):
        def optim(self): return self
        def ispis(self): return self.sadržaj.translate(subskript)
        def optim1(self): return self
    #gornji tokeni su za formule, a donji za program
    TOČKAZ, V_OTV, V_ZATV = ';{}'
    FOR, IF, ELSE, WHILE, ISPIŠI = 'for', 'if', 'else', 'while', 'ispiši'
    INT = 'int'
    JEDNAKO, JJEDNAKO, PLUS, PLUSP, PLUSJ, MINUS, MINUSM, MINUSJ, PUTA, NA = '=', '==', '+', '++', '+=', '-', '--', '-=', '*', '^'
    MANJE, MMANJE, VEĆE = '<', '<<', '>' 

    class CONTINUE(Token):
        literal = 'continue'
        def izvrši(self): raise PrekidContinue
    class BREAK(Token):
        literal = 'break'
        def izvrši(self): raise PrekidBreak
    class BROJ(Token): 
        def vrijednost(self): return int(self.sadržaj)
    class IME(Token): 
        def vrijednost(self): return rt.mem[self]

@lexer
def ml(lex):
    for znak in lex:
        if znak.isspace() : lex.zanemari()
        elif znak == '[':
            lex >> ']'
            yield lex.token(T.BOX)
        elif znak == '<':
            if lex >= '>' : yield lex.token(T.DIAMOND)
            elif lex >= '<': yield lex.token(T.MMANJE)
            elif lex >= '-':
                lex >> '>'
                yield lex.token(T.BIKOND)
            else: yield lex.token(T.MANJE)
        elif znak == 'P':
            lex.prirodni_broj('')
            yield lex.token(T.PVAR)
        elif znak.isalpha() or znak == '_':
            lex * {str.isalnum, '_'}
            yield lex.literal_ili(T.IME)
        elif znak.isdecimal():
            lex.prirodni_broj(znak)
            yield lex.token(T.BROJ)
        elif znak == '-':
            if lex >= '>': yield lex.token(T.KOND)
            elif lex >= '-': yield lex.token(T.MINUSM)
            elif lex >= '=': yield lex.token(T.MINUSJ)
            else: yield lex.token(T.MINUS)
        elif znak == '+':
            if lex >= '+': yield lex.token(T.PLUSP)
            elif lex >= '=': yield lex.token(T.PLUSJ)
            else: yield lex.token(T.PLUS)
        elif znak == '=':
            yield lex.token(T.JJEDNAKO if lex >= '=' else T.JEDNAKO)
        elif znak == '#':
            lex - '\n'
            lex.zanemari()
        else: yield lex.literal(T)

### beskontekstna gramatika
# start -> naredbe naredba
# naredbe -> '' | naredbe naredba
# naredba  -> petlja | grananje | ispis TOČKAZ | pridruživanje TOČKAZ | deklaracija TOČKAZ | BREAK TOČKAZ | CONTINUE TOČKAZ
# for_operator -> MANJE | VEĆE ##NAPOMENA: ovdje nadodati ako zelimo jos nesto u for_operatoru (možda još !=)
# promjena -> PLUSP | MINUSM | PLUSJ BROJ | MINUSJ BROJ
# for -> FOR O_OTV IME# JEDNAKO BROJ TOČKAZ IME# for_operator BROJ TOČKAZ IME# promjena O_ZATV
# blok -> V_OTV naredbe V_ZATV | naredba
# petlja -> for blok
# varijabla -> IME | BROJ
# if_operator -> JJEDNAKO | MANJE | VEĆE  ##NAPOMENA: ovdje nadodati ako zelimo jos nesto u if_operatoru (možda još !=)
# uvjet -> varijabla | varijabla if_operator varijabla 
# grananje -> IF O_OTV uvjet O_ZATV blok (ELSE blok)?
# varijable -> '' | varijable MMANJE varijabla
# ispis -> ISPIŠI varijable 
# izraz -> član | izraz (PLUS|MINUS) član
# član -> faktor | član PUTA faktor
# faktor -> baza | baza NA faktor | MINUS faktor
# baza -> BROJ | IME(aritmetičkog tipa) | O_OTV izraz O_ZATV 
# tip -> INT (ovo je odvojeno iako je pravilo trivijalno jer će biti još tipova s desne strane; vjerojatno ću još od aritmetičkih dodati nat i to će biti dovoljno)
# pridruživanje -> IME JEDNAKO izraz
# deklaracija -> tip IME JEDNAKO izraz 

## ovo ispod kasnije će se povezati s gornjim kad se uvedu varijable formula, model itd.
# formula -> PVAR | NEG formula | DIAMOND formula | BOX formula | O_OTV formula binvez formula O_ZATV
# binvez -> KONJ | DISJ | KOND | BIKOND

class P(Parser):
    def start(p):
        naredbe = [p.naredba()]
        while not p > KRAJ: naredbe.append(p.naredba())
        return Program(naredbe)
    
    def naredba(p):
        if p > T.FOR: return p.petlja()
        elif p > T.ISPIŠI: return p.ispis()
        elif p > T.IF: return p.grananje()
        elif p > T.IME: return p.pridruživanje()
        elif p > T.INT: return p.deklaracija() #kad budemo imali vise tipova, onda cemo imati p > {T.INT, T.FORMULA...}
        elif br := p >= T.BREAK:
            p >> T.TOČKAZ
            return br
        elif cont := p >= T.CONTINUE:
            p >> T.TOČKAZ
            return cont
        else: raise SintaksnaGreška('Nepoznata naredba')
    
    def petlja(p):
        kriva_varijabla = SemantičkaGreška('Sva tri dijela for-petlje moraju imati istu varijablu')
        
        p >> T.FOR, p >> T.O_OTV
        i = p >> T.IME
        p >> T.JEDNAKO
        početak = p >> {T.BROJ, T.IME}
        p >> T.TOČKAZ

        if (p >> T.IME) != i: raise kriva_varijabla
        for_operator = p >> {T.MANJE, T.VEĆE} # ovdje se lako doda ako hocemo podrzati jos neke operatore
        granica = p >> T.BROJ
        p >> T.TOČKAZ

        if (p >> T.IME) != i: raise kriva_varijabla
        if minus_ili_plus := p >= {T.PLUSP, T.MINUSM}: promjena = nenavedeno
        elif minus_ili_plus := p >> {T.PLUSJ, T.MINUSJ}: promjena = p >> T.BROJ
        p >> T.O_ZATV

        blok = p.blok()
        return Petlja(i, početak, for_operator, granica, promjena, minus_ili_plus, blok)
    
    #blok može biti ili jedna naredba ili {naredbe*} !!!
    def blok(p):
        naredbe = []
        if p >= T.V_OTV:
            while not p >= T.V_ZATV:
                naredbe.append(p.naredba())
        else: naredbe.append(p.naredba())

        return Blok(naredbe)
    
    def ispis(p):
        p >> T.ISPIŠI
        varijable = []
        while p >= T.MMANJE: varijable.append(p >> {T.IME, T.BROJ})
        p >> T.TOČKAZ
        return Ispis(varijable)
    
    def grananje(p):
        p >> T.IF, p >> T.O_OTV
        uvjet = p.uvjet()
        p >> T.O_ZATV
        if_blok = p.blok()
        else_blok = nenavedeno
        if p >= T.ELSE: else_blok = p.blok()
        return Grananje(uvjet, if_blok, else_blok)
    
    def uvjet(p):
        lijeva_strana = p >> {T.IME, T.BROJ}
        op = p >> {T.JJEDNAKO, T.MANJE, T.VEĆE} #ovdje se dodaju if_operatori ako zelimo prosiriti
        desna_strana = p >> {T.IME, T.BROJ}
        return Uvjet(lijeva_strana, op, desna_strana)
    
    def pridruživanje(p):
        ime_varijable = p >> T.IME
        p >> T.JEDNAKO
        vrijednost = p.izraz()
        p >> T.TOČKAZ
        return Pridruživanje(ime_varijable, vrijednost)
    
    def deklaracija(p):
        tip = p >> T.INT #kad budemo imali vise tipova, onda cemo imati p > {T.INT, T.FORMULA...}
        ime = p >> T.IME
        p >> T.JEDNAKO
        vrijednost = p.izraz()
        p >> T.TOČKAZ
        return Deklaracija(tip, ime, vrijednost)

    def izraz(p):
        t = p.član()
        while op := p >= {T.PLUS, T.MINUS}: t = Op(op, t, p.član())
        return t
    
    def član(p):
        t = p.faktor()
        while op := p >= T.PUTA: t = Op(op, t, p.faktor())
        return t
    
    def faktor(p):
        if op := p >= T.MINUS: return Op(op, nenavedeno, p.faktor())
        baza = p.baza()
        if p >= T.NA: return Potencija(baza, p.faktor())
        else: return baza

    def baza(p):
        if elementarni := p >= {T.BROJ, T.IME}: 
            return elementarni #valjda tu nece bit problema kod T.IME jer to ce kasnije bit naziv za neku varijablu koja ne mora biti aritmetickog tipa
        elif p >> T.O_OTV:
            u_zagradi = p.izraz()
            p >> T.O_ZATV
            return u_zagradi

    def formula(p):
        if varijabla := p >= T.PVAR: return varijabla
        elif p > {T.BOX, T.DIAMOND, T.NEG}:
            klasa, ispod = p.unvez(), p.formula()
            return klasa(ispod)
        elif p >> T.O_OTV:
            l, klasa, d = p.formula(), p.binvez(), p.formula()
            p >> T.O_ZATV
            return klasa(l, d)
        
    def unvez(p):
        if p >= T.NEG: return Negacija
        elif p >= T.DIAMOND: return Diamond
        elif p >= T.BOX: return Box
        else: raise p.greška()
    
    def binvez(p):
        if p >= T.KONJ: return Konjunkcija
        elif p >= T.DISJ: return Disjunkcija
        elif p >= T.KOND: return Kondicional
        elif p >= T.BIKOND: return Bikondicional
        else: raise p.greška()

class Program(AST):
    naredbe: 'barem jedna naredba'

    def izvrši(program):
        rt.mem = Memorija()
        try:
            for naredba in program.naredbe: naredba.izvrši()
        except PrekidBreak: raise SemantičkaGreška('Nedozvoljen break izvan petlje')
        except PrekidContinue: raise SemantičkaGreška('Nedozvoljen continue izvan petlje')

class Petlja(AST):
    varijabla: 'IME'
    početak: 'BROJ | varijabla'
    operator: '(<|>)' #mogli bi bit još podržani <= ili >=, ali nije da time dobivamo na ekspresivnosti jezika; eventualno dodati !=
    granica: 'BROJ'
    promjena: 'BROJ?'
    predznak: '(+|-)'
    blok: 'naredba*'

    def izvrši(petlja):
        kv = petlja.varijabla
        rt.mem[kv] = petlja.početak.vrijednost()
        while rt.mem[kv] < petlja.granica.vrijednost() if petlja.operator ^ T.MANJE else rt.mem[kv] > petlja.granica.vrijednost():
            try:
                petlja.blok.izvrši()
            except PrekidBreak: break
            except PrekidContinue: #nazalost dupliciram kod radi ispravnog rada continue, kasnije mozemo popraviti
                prom = petlja.promjena
                if petlja.predznak ^ T.MINUSJ or petlja.predznak ^ T.MINUSM:
                    rt.mem[kv] -= prom.vrijednost() if prom else 1
                else: rt.mem[kv] += prom.vrijednost() if prom else 1
                continue
            prom = petlja.promjena
            if petlja.predznak ^ T.MINUSJ or petlja.predznak ^ T.MINUSM:
                rt.mem[kv] -= prom.vrijednost() if prom else 1
            else: rt.mem[kv] += prom.vrijednost() if prom else 1

class Blok(AST):
    naredbe: 'naredba*'
    
    def izvrši(blok):
        for naredba in blok.naredbe:
            naredba.izvrši()

class Ispis(AST):
    varijable: 'IME*'

    def izvrši(ispis):
        for varijabla in ispis.varijable:
            print(varijabla.vrijednost(), end = ' ')

class Uvjet(AST):
    lijeva: '(IME|BROJ)'
    operator: '(==|<|>)'
    desna: '(IME|BROJ)'

    def ispunjen(uvjet):
        if uvjet.operator ^ T.JJEDNAKO:
            return uvjet.lijeva.vrijednost() == uvjet.desna.vrijednost()
        elif uvjet.operator ^ T.VEĆE:
            return uvjet.lijeva.vrijednost() > uvjet.desna.vrijednost()
        elif uvjet.operator ^ T.MANJE:
            return uvjet.lijeva.vrijednost() < uvjet.desna.vrijednost()
        else: raise SintaksnaGreška('Nepodržan operator u if-uvjetu')

class Grananje(AST):
    uvjet: 'log'
    onda: 'naredba'
    inače: 'naredba'

    def izvrši(grananje):
        if grananje.uvjet.ispunjen(): grananje.onda.izvrši()
        elif grananje.inače: grananje.inače.izvrši()

class Pridruživanje(AST):
    varijabla: 'IME'
    vrij: '(varijabla | BROJ)'

    def izvrši(pridruživanje):
        if pridruživanje.varijabla in rt.mem:
            rt.mem[pridruživanje.varijabla] = pridruživanje.vrij.vrijednost()
        else: return rt.mem[pridruživanje.varijabla] #jer ovo vraca bas ono upozorenje koje nam treba

class Deklaracija(AST):
    tip: 'neki od podrzanih tipova'
    ime: 'IME'
    vrij: 'varijabla | BROJ'

    def izvrši(deklaracija):
        if deklaracija.ime in rt.mem:
            raise deklaracija.ime.redeklaracija()
        else: rt.mem[deklaracija.ime] = deklaracija.vrij.vrijednost()

class Op(AST):
    op: 'T'
    lijevo: 'izraz?'
    desno: 'izraz'

    def vrijednost(self):
        if self.lijevo is nenavedeno: l = 0  
        else: l = self.lijevo.vrijednost()
        o, d = self.op, self.desno.vrijednost()
        if o ^ T.PLUS: return l + d
        elif o ^ T.MINUS: return l - d
        elif o ^ T.PUTA: return l * d

class Potencija(AST):
    baza: 'elementarni | izraz'
    eksponent: 'faktor'

    def vrijednost(self):
        return self.baza.vrijednost() ** self.eksponent.vrijednost()

class Unarna(AST):
    ispod: 'formula'

    def optim(self):
        klasa = type(self)
        ispod_opt = self.ispod.optim()
        if ispod_opt ^ Negacija and self ^ Negacija: return ispod_opt.ispod
        else: return klasa(ispod_opt) 
    
    def optim1(self):
        klasa = type(self)
        if isinstance(self, Diamond):
            ispod_opt = self.ispod.optim1()
            nova_klasa = Negacija(ispod_opt)
            nova_klasa = Box(nova_klasa)
            return Negacija(nova_klasa)
        else: return self

    def ispis(self): 
        return self.veznik + self.ispod.ispis()

class Negacija(Unarna):
    veznik = '¬'
    
class Diamond(Unarna):
    veznik = '◆'

class Box(Unarna):
    veznik = '■'

class Binarna(AST):
    lijevo: 'formula'
    desno: 'formula'

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
        else: return self

    def ispis(self): return '(' + self.lijevo.ispis() + self.veznik + self.desno.ispis() + ')'

class Disjunkcija(Binarna):
    veznik = '∨'

class Konjunkcija(Binarna):
    veznik = '∧'

class Kondicional(Binarna):
    veznik = '→'

class Bikondicional(Binarna):
    veznik = '↔'

def optimiziraj(formula):
    """Pretvara formulu (AST) u formulu koja od veznika ima samo kondicional i negaciju; prije te pretvorbe su još uklonjene dvostruke negacije"""

    nova = formula.optim() #prije optimizacije da dobijemo samo negaciju i kondicional uklanjamo redundantne negacije
    nova = nova.optim1() #kreiramo ekvivalentnu formulu koja ima samo negaciju, kondicional i box od veznika
    return nova.optim() #nakon dobivanja ekvivalentne formule opet se mogu javiti redundantne negacije pa ih zato još jednom mičemo

def jednaki(f1, f2):
    klasa1 = type(f1)
    klasa2 = type(f2)

    if klasa1 != klasa2:
        return False
    elif f1 ^ T.PVAR:
        return f1.ispis() == f2.ispis()
    elif isinstance(f1, Binarna): return jednaki(f1.lijevo, f2.lijevo) and jednaki(f1.desno, f2.desno)
    else: return jednaki(f1.ispod, f2.ispod)
    
### ispod je samo testiranje

prikaz(kôd := P('''
    # ovo je komentar
    int a = 3 + 5;
    int b = 0;
    b = 3;
    for ( i = a ; i < 13 ; i++ ) {
        if (i == 10) {
            ispiši << a;
            continue;
        } else {
            ispiši << i;
        }
    }
'''), 8)
kôd.izvrši()

# optimizator za aritmeticke izraze
# while petlja -> vjerojatno onda AST Petlja preimenovat u FOR i onda zaseban AST za while
# omogucit vise logickih uvjeta u if-u
# uvest novi cjelobrojni tip nat i omogucit eksplicitno/implicitno castanje