:********** 19-Nov-2015 11:28:30 ***********
: Using : C2268_rep2 VZero[-50.000]	 tStart(0) tEnd(499)
: VStart = -40.000000 	 VEnd = 50.000000 	 RevPot = -85.200000
: m0 = 0.000000 	 h0 = 1.000000 	 mPower = 2.000000 	 hPower = 1.000000
:Last Error =  :49.0232                  
: $Author : Rajnish Ranjan, Nov 2015
:*******************************************

NEURON  {
	SUFFIX Kv1_1
	USEION k READ ek WRITE ik
	RANGE gKv1_1bar, gKv1_1, ik
}

UNITS   {
	(S) = (siemens)
	(mV) = (millivolt)
	(mA) = (milliamp)
}

PARAMETER   {
	gKv1_1bar = 0.001 (S/cm2)
}

ASSIGNED    {
	v   (mV)
	ek  (mV)
	ik  (mA/cm2)
	gKv1_1  (S/cm2)
	mInf
	mTau
	hInf
	hTau
}

STATE   {
	m
	h
}

BREAKPOINT  {
	SOLVE states METHOD cnexp
	gKv1_1 = gKv1_1bar *m *m *h 
	ik = gKv1_1*(v-ek)
}

DERIVATIVE states   {
	rates()
	 m' = (mInf-m)/mTau
	h' = (hInf-h)/hTau
}

INITIAL{
	rates()
	m = mInf
	h = hInf
}

PROCEDURE rates(){
	UNITSOFF
		mInf =   1/(1+exp((v- -30.509781)/-9.612456))
		mTau =   0.309143 + (0.422573 * exp(-v/15.017209)) 
		hInf =   0.607451 +( 0.512988 / (1 + exp((v - -21.997832)/5.585790))) 
		hTau =   33.060819 + (3.448857 * exp(-v/7.848950)) 
	UNITSON
}

