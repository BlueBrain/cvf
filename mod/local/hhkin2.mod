TITLE hh.mod   squid sodium, potassium, and leak channels

COMMENT
This is the original Hodgkin-Huxley treatment for the set of sodium,
potassium, and leakage channels found in the squid giant axon membrane.
("A quantitative description of membrane current and its application
conduction and excitation in nerve" J.Physiol. (Lond.) 117:500-544 (1952).)
Membrane voltage is in absolute mV and has been reversed in polarity
from the original HH convention and shifted to reflect a resting potential
of -65 mV.
Remember to set celsius=6.3 (or whatever) in your HOC file.
See squid.hoc for an example of a simulation using this model.
SW Jaslove  6 March, 1992
ENDCOMMENT

UNITS {
    (mA) = (milliamp)
    (mV) = (millivolt)
    (S) = (siemens)
}

? interface
NEURON {
    SUFFIX hhkin2
    USEION na READ ena WRITE ina
    USEION k READ ek WRITE ik
    NONSPECIFIC_CURRENT il
    RANGE a0,a1,a2,a3,a4,a5,a6,a7,a8,a9
    RANGE gnabar, gkbar, gl, el, gna, gk
    :GLOBAL minf, hinf, ninf, mtau, htau, ntau
    RANGE am, ah, an, bm, bh, bn
    THREADSAFE : assigned GLOBALs will be per thread
}

PARAMETER {
    a0 a1 a2 a3 a4 a5 a6 a7 a8 a9
    gnabar = .12 (S/cm2)    <0,1e9>
    gkbar = .036 (S/cm2)    <0,1e9>
    gl = .0003 (S/cm2)	<0,1e9>
    el = -54.3 (mV)
}

STATE {
    m h n mc hc nc
}

ASSIGNED {
    v (mV)
    celsius (degC)
    ena (mV)
    ek (mV)

    gna (S/cm2)
    gk (S/cm2)
    ina (mA/cm2)
    ik (mA/cm2)
    il (mA/cm2)
    am ah an bm bh bn
}

? currents
BREAKPOINT {
    SOLVE states METHOD sparse
    gna = gnabar*m*m*m*h
    ina = gna*(v - ena)
    gk = gkbar*n*n*n*n
    ik = gk*(v - ek)
    il = gl*(v - el)
}

INITIAL {
    rates(v)
    m = am/(am + bm)
    h = ah/(ah + bh)
    n = an/(an + bn)
    mc = bm/(am + bm)
    hc = bh/(ah + bh)
    nc = bn/(an + bn)
}

? states
KINETIC states {
    rates(v)
    ~ mc <-> m (am, bm)
    ~ hc <-> h (ah, bh)
    ~ nc <-> n (an, bn)
}
:LOCAL q10


? rates
PROCEDURE rates(v(mV)) {  :Computes rate and other constants at current v.
    :Call once from HOC to initialize inf at resting v.
    :TABLE minf, mtau, hinf, htau, ninf, ntau DEPEND celsius FROM -100 TO 100 WITH 200
    UNITSOFF
    :"m" sodium activation system
    am = .1 * vtrap(-(v+40),10)
    bm =  4 * exp(-(v+65)/18)

    :"h" sodium inactivation system
    ah = .07 * exp(-(v+65)/20)
    bh = 1 / (exp(-(v+35)/10) + 1)
    :"n" potassium activation system
    an = .01*vtrap(-(v+55),10)
    bn = .125*exp(-(v+65)/80)
}

FUNCTION vtrap(x,y) {  :Traps for 0 in denominator of rate eqns.
    if (fabs(x/y) < 1e-6) {
    vtrap = y*(1 - x/y/2)
    }else{
    vtrap = x/(exp(x/y) - 1)
    }
}

UNITSON


