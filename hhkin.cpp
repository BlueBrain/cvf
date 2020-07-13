/*********************************************************
Model Name      : hhkin
Filename        : hhkin.mod
NMODL Version   : 6.2.0
Vectorized      : true
Threadsafe      : true
Created         : Mon Aug  3 12:16:04 2020
Backend         : C (api-compatibility)
NMODL Compiler  : 0.2 [2969adb 20-07-2020 21:53]
*********************************************************/

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <coreneuron/mechanism/mech/cfile/scoplib.h>
#include <coreneuron/nrnconf.h>
#include <coreneuron/sim/multicore.hpp>
#include <coreneuron/mechanism/register_mech.hpp>
#include <coreneuron/gpu/nrn_acc_manager.hpp>
#include <coreneuron/utils/randoms/nrnran123.h>
#include <coreneuron/nrniv/nrniv_decl.h>
#include <coreneuron/utils/ivocvect.hpp>
#include <coreneuron/utils/nrnoc_aux.hpp>
#include <coreneuron/mechanism/mech/mod2c_core_thread.hpp>
#include <coreneuron/sim/scopmath/newton_struct.h>
#include "_kinderiv.h"
#include <Eigen/LU>


namespace coreneuron {


    /** channel information */
    static const char *mechanism[] = {
        "6.2.0",
        "hhkin",
        "a0_hhkin",
        "a1_hhkin",
        "a2_hhkin",
        "a3_hhkin",
        "a4_hhkin",
        "a5_hhkin",
        "a6_hhkin",
        "a7_hhkin",
        "a8_hhkin",
        "a9_hhkin",
        "gnabar_hhkin",
        "gkbar_hhkin",
        "gl_hhkin",
        "el_hhkin",
        0,
        "gna_hhkin",
        "gk_hhkin",
        "il_hhkin",
        "am_hhkin",
        "ah_hhkin",
        "an_hhkin",
        "bm_hhkin",
        "bh_hhkin",
        "bn_hhkin",
        0,
        "m_hhkin",
        "h_hhkin",
        "n_hhkin",
        "mc_hhkin",
        "hc_hhkin",
        "nc_hhkin",
        0,
        0
    };


    /** all global variables */
    struct hhkin_Store {
        int na_type;
        int k_type;
        double m0;
        double h0;
        double n0;
        double mc0;
        double hc0;
        double nc0;
        int reset;
        int mech_type;
        int* slist1;
        int* dlist1;
        ThreadDatum* __restrict__ ext_call_thread;
    };

    /** holds object of global variable */
    hhkin_Store hhkin_global;


    /** all mechanism instance variables */
    struct hhkin_Instance  {
        const double* __restrict__ a0;
        const double* __restrict__ a1;
        const double* __restrict__ a2;
        const double* __restrict__ a3;
        const double* __restrict__ a4;
        const double* __restrict__ a5;
        const double* __restrict__ a6;
        const double* __restrict__ a7;
        const double* __restrict__ a8;
        const double* __restrict__ a9;
        const double* __restrict__ gnabar;
        const double* __restrict__ gkbar;
        const double* __restrict__ gl;
        const double* __restrict__ el;
        double* __restrict__ gna;
        double* __restrict__ gk;
        double* __restrict__ il;
        double* __restrict__ am;
        double* __restrict__ ah;
        double* __restrict__ an;
        double* __restrict__ bm;
        double* __restrict__ bh;
        double* __restrict__ bn;
        double* __restrict__ m;
        double* __restrict__ h;
        double* __restrict__ n;
        double* __restrict__ mc;
        double* __restrict__ hc;
        double* __restrict__ nc;
        double* __restrict__ Dm;
        double* __restrict__ Dh;
        double* __restrict__ Dn;
        double* __restrict__ Dmc;
        double* __restrict__ Dhc;
        double* __restrict__ Dnc;
        double* __restrict__ ena;
        double* __restrict__ ek;
        double* __restrict__ ina;
        double* __restrict__ ik;
        double* __restrict__ v_unused;
        double* __restrict__ g_unused;
        const double* __restrict__ ion_ena;
        double* __restrict__ ion_ina;
        double* __restrict__ ion_dinadv;
        const double* __restrict__ ion_ek;
        double* __restrict__ ion_ik;
        double* __restrict__ ion_dikdv;
    };


    /** ion write variables */
    struct IonCurVar {
        double ina;
        double ik;
        double il;

        IonCurVar() : ina(0), ik(0), il(0) {}
    };


    /** connect global (scalar) variables to hoc -- */
    static DoubScal hoc_scalar_double[] = {
        0, 0
    };


    /** connect global (array) variables to hoc -- */
    static DoubVec hoc_vector_double[] = {
        0, 0, 0
    };


    static inline int first_pointer_var_index() {
        return -1;
    }


    static inline int get_memory_layout() {
        return 0;  //soa
    }


    static inline int float_variables_size() {
        return 41;
    }


    static inline int int_variables_size() {
        return 6;
    }


    static inline int get_mech_type() {
        return hhkin_global.mech_type;
    }


    static inline Memb_list* get_memb_list(NrnThread* nt) {
        if (nt->_ml_list == NULL) {
            return NULL;
        }
        return nt->_ml_list[get_mech_type()];
    }


    static inline void* mem_alloc(size_t num, size_t size, size_t alignment = 16) {
        void* ptr;
        posix_memalign(&ptr, alignment, num*size);
        memset(ptr, 0, size);
        return ptr;
    }


    static inline void mem_free(void* ptr) {
        free(ptr);
    }


    /** initialize global variables */
    static inline void setup_global_variables()  {
        static int setup_done = 0;
        if (setup_done) {
            return;
        }
        hhkin_global.slist1 = (int*) mem_alloc(6, sizeof(int));
        hhkin_global.dlist1 = (int*) mem_alloc(6, sizeof(int));
        hhkin_global.m0 = 0.0;
        hhkin_global.h0 = 0.0;
        hhkin_global.n0 = 0.0;
        hhkin_global.mc0 = 0.0;
        hhkin_global.hc0 = 0.0;
        hhkin_global.nc0 = 0.0;

        setup_done = 1;
    }


    /** free global variables */
    static inline void free_global_variables()  {
        mem_free(hhkin_global.slist1);
        mem_free(hhkin_global.dlist1);
    }


    /** initialize mechanism instance variables */
    static inline void setup_instance(NrnThread* nt, Memb_list* ml)  {
        hhkin_Instance* inst = (hhkin_Instance*) mem_alloc(1, sizeof(hhkin_Instance));
        int pnodecount = ml->_nodecount_padded;
        Datum* indexes = ml->pdata;
        inst->a0 = ml->data+0*pnodecount;
        inst->a1 = ml->data+1*pnodecount;
        inst->a2 = ml->data+2*pnodecount;
        inst->a3 = ml->data+3*pnodecount;
        inst->a4 = ml->data+4*pnodecount;
        inst->a5 = ml->data+5*pnodecount;
        inst->a6 = ml->data+6*pnodecount;
        inst->a7 = ml->data+7*pnodecount;
        inst->a8 = ml->data+8*pnodecount;
        inst->a9 = ml->data+9*pnodecount;
        inst->gnabar = ml->data+10*pnodecount;
        inst->gkbar = ml->data+11*pnodecount;
        inst->gl = ml->data+12*pnodecount;
        inst->el = ml->data+13*pnodecount;
        inst->gna = ml->data+14*pnodecount;
        inst->gk = ml->data+15*pnodecount;
        inst->il = ml->data+16*pnodecount;
        inst->am = ml->data+17*pnodecount;
        inst->ah = ml->data+18*pnodecount;
        inst->an = ml->data+19*pnodecount;
        inst->bm = ml->data+20*pnodecount;
        inst->bh = ml->data+21*pnodecount;
        inst->bn = ml->data+22*pnodecount;
        inst->m = ml->data+23*pnodecount;
        inst->h = ml->data+24*pnodecount;
        inst->n = ml->data+25*pnodecount;
        inst->mc = ml->data+26*pnodecount;
        inst->hc = ml->data+27*pnodecount;
        inst->nc = ml->data+28*pnodecount;
        inst->Dm = ml->data+29*pnodecount;
        inst->Dh = ml->data+30*pnodecount;
        inst->Dn = ml->data+31*pnodecount;
        inst->Dmc = ml->data+32*pnodecount;
        inst->Dhc = ml->data+33*pnodecount;
        inst->Dnc = ml->data+34*pnodecount;
        inst->ena = ml->data+35*pnodecount;
        inst->ek = ml->data+36*pnodecount;
        inst->ina = ml->data+37*pnodecount;
        inst->ik = ml->data+38*pnodecount;
        inst->v_unused = ml->data+39*pnodecount;
        inst->g_unused = ml->data+40*pnodecount;
        inst->ion_ena = nt->_data;
        inst->ion_ina = nt->_data;
        inst->ion_dinadv = nt->_data;
        inst->ion_ek = nt->_data;
        inst->ion_ik = nt->_data;
        inst->ion_dikdv = nt->_data;
        ml->instance = (void*) inst;
    }


    /** cleanup mechanism instance variables */
    static inline void cleanup_instance(Memb_list* ml)  {
        hhkin_Instance* inst = (hhkin_Instance*) ml->instance;
        mem_free((void*)inst);
    }


    static void nrn_alloc_hhkin(double* data, Datum* indexes, int type)  {
        // do nothing
    }


    inline double vtrap_hhkin(int id, int pnodecount, hhkin_Instance* inst, IonCurVar& ionvar, double* data, const Datum* indexes, ThreadDatum* thread, NrnThread* nt, double v, double x, double y);
    inline int rates_hhkin(int id, int pnodecount, hhkin_Instance* inst, IonCurVar& ionvar, double* data, const Datum* indexes, ThreadDatum* thread, NrnThread* nt, double v, double arg_v);


    inline int rates_hhkin(int id, int pnodecount, hhkin_Instance* inst, IonCurVar& ionvar, double* data, const Datum* indexes, ThreadDatum* thread, NrnThread* nt, double v, double arg_v) {
        int ret_rates = 0;
        inst->am[id] = 0.1 * vtrap_hhkin(id, pnodecount, inst, ionvar, data, indexes, thread, nt, v,  -(arg_v + 40.0), 10.0);
        inst->bm[id] = 4.0 * exp( -(arg_v + 65.0) / 18.0);
        inst->ah[id] = 0.07000000000000001 * exp( -(arg_v + 65.0) / 20.0);
        inst->bh[id] = 1.0 / (exp( -(arg_v + 35.0) / 10.0) + 1.0);
        inst->an[id] = 0.01 * vtrap_hhkin(id, pnodecount, inst, ionvar, data, indexes, thread, nt, v,  -(arg_v + 55.0), 10.0);
        inst->bn[id] = 0.125 * exp( -(arg_v + 65.0) / 80.0);
        return ret_rates;
    }


    inline double vtrap_hhkin(int id, int pnodecount, hhkin_Instance* inst, IonCurVar& ionvar, double* data, const Datum* indexes, ThreadDatum* thread, NrnThread* nt, double v, double x, double y) {
        double ret_vtrap = 0.0;
        if (fabs(x / y) < 1e-06) {
            ret_vtrap = y * (1.0 - x / y / 2.0);
        } else {
            ret_vtrap = x / (exp(x / y) - 1.0);
        }
        return ret_vtrap;
    }


    /** initialize channel */
    void nrn_init_hhkin(NrnThread* nt, Memb_list* ml, int type) {
        int nodecount = ml->nodecount;
        int pnodecount = ml->_nodecount_padded;
        const int* __restrict__ node_index = ml->nodeindices;
        double* __restrict__ data = ml->data;
        const double* __restrict__ voltage = nt->_actual_v;
        Datum* __restrict__ indexes = ml->pdata;
        ThreadDatum* __restrict__ thread = ml->_thread;

        setup_instance(nt, ml);
        hhkin_Instance* __restrict__ inst = (hhkin_Instance*) ml->instance;

        if (_nrn_skip_initmodel == 0) {
            int start = 0;
            int end = nodecount;
            #pragma ivdep
            for (int id = start; id < end; id++) {
                int node_id = node_index[id];
                double v = voltage[node_id];
                IonCurVar ionvar;
                inst->m[id] = hhkin_global.m0;
                inst->h[id] = hhkin_global.h0;
                inst->n[id] = hhkin_global.n0;
                inst->mc[id] = hhkin_global.mc0;
                inst->hc[id] = hhkin_global.hc0;
                inst->nc[id] = hhkin_global.nc0;
                rates_hhkin(id, pnodecount, inst, ionvar, data, indexes, thread, nt, v, v);
                inst->m[id] = inst->am[id] / (inst->am[id] + inst->bm[id]);
                inst->h[id] = inst->ah[id] / (inst->ah[id] + inst->bh[id]);
                inst->n[id] = inst->an[id] / (inst->an[id] + inst->bn[id]);
                inst->mc[id] = inst->bm[id] / (inst->am[id] + inst->bm[id]);
                inst->hc[id] = inst->bh[id] / (inst->ah[id] + inst->bh[id]);
                inst->nc[id] = inst->bn[id] / (inst->an[id] + inst->bn[id]);
            }
        }
    }


    static inline double nrn_current(int id, int pnodecount, hhkin_Instance* inst, IonCurVar& ionvar, double* data, const Datum* indexes, ThreadDatum* thread, NrnThread* nt, double v) {
        double current = 0.0;
        inst->gna[id] = inst->gnabar[id] * inst->m[id] * inst->m[id] * inst->m[id] * inst->h[id];
        ionvar.ina = inst->gna[id] * (v - inst->ion_ena[indexes[0*pnodecount+id]]);
        inst->gk[id] = inst->gkbar[id] * inst->n[id] * inst->n[id] * inst->n[id] * inst->n[id];
        ionvar.ik = inst->gk[id] * (v - inst->ion_ek[indexes[3*pnodecount+id]]);
        ionvar.il = inst->gl[id] * (v - inst->el[id]);
        current += ionvar.il;
        current += ionvar.ina;
        current += ionvar.ik;
        return current;
    }


    /** update current */
    void nrn_cur_hhkin(NrnThread* nt, Memb_list* ml, int type) {
        int nodecount = ml->nodecount;
        int pnodecount = ml->_nodecount_padded;
        const int* __restrict__ node_index = ml->nodeindices;
        double* __restrict__ data = ml->data;
        const double* __restrict__ voltage = nt->_actual_v;
        double* __restrict__  vec_rhs = nt->_actual_rhs;
        double* __restrict__  vec_d = nt->_actual_d;
        Datum* __restrict__ indexes = ml->pdata;
        ThreadDatum* __restrict__ thread = ml->_thread;
        hhkin_Instance* __restrict__ inst = (hhkin_Instance*) ml->instance;

        int start = 0;
        int end = nodecount;
        #pragma ivdep
        for (int id = start; id < end; id++) {
            int node_id = node_index[id];
            double v = voltage[node_id];
            IonCurVar ionvar;
            double g = nrn_current(id, pnodecount, inst, ionvar, data, indexes, thread, nt, v+0.001);
            double dina = ionvar.ina;
            double dik = ionvar.ik;
            double rhs = nrn_current(id, pnodecount, inst, ionvar, data, indexes, thread, nt, v);
            g = (g-rhs)/0.001;
            inst->ion_dinadv[indexes[2*pnodecount+id]] += (dina-ionvar.ina)/0.001;
            inst->ion_dikdv[indexes[5*pnodecount+id]] += (dik-ionvar.ik)/0.001;
            inst->ion_ina[indexes[1*pnodecount+id]] += ionvar.ina;
            inst->ion_ik[indexes[4*pnodecount+id]] += ionvar.ik;
            vec_rhs[node_id] -= rhs;
            vec_d[node_id] += g;
        }
    }


    /** update state */
    void nrn_state_hhkin(NrnThread* nt, Memb_list* ml, int type) {
        int nodecount = ml->nodecount;
        int pnodecount = ml->_nodecount_padded;
        const int* __restrict__ node_index = ml->nodeindices;
        double* __restrict__ data = ml->data;
        const double* __restrict__ voltage = nt->_actual_v;
        Datum* __restrict__ indexes = ml->pdata;
        ThreadDatum* __restrict__ thread = ml->_thread;
        hhkin_Instance* __restrict__ inst = (hhkin_Instance*) ml->instance;

        int start = 0;
        int end = nodecount;
        #pragma ivdep
        for (int id = start; id < end; id++) {
            int node_id = node_index[id];
            double v = voltage[node_id];
            IonCurVar ionvar;
            
            Eigen::Matrix<double, 6, 1> X, F;
            Eigen::Matrix<double, 6, 6> Jm;
            double* J = Jm.data();
            double old_m, old_h, old_n, old_mc, old_hc, old_nc;
            rates_hhkin(id, pnodecount, inst, ionvar, data, indexes, thread, nt, v, v);
            old_m = inst->m[id];
            old_h = inst->h[id];
            old_n = inst->n[id];
            old_mc = inst->mc[id];
            old_hc = inst->hc[id];
            old_nc = inst->nc[id];
            X[0] = inst->m[id];
            X[1] = inst->h[id];
            X[2] = inst->n[id];
            X[3] = inst->mc[id];
            X[4] = inst->hc[id];
            X[5] = inst->nc[id];
            F[0] =  -old_m;
            F[1] =  -old_h;
            F[2] =  -old_n;
            F[3] =  -old_mc;
            F[4] =  -old_hc;
            F[5] =  -old_nc;
            J[0] =  -inst->bm[id] * nt->_dt - 1.0;
            J[6] = 0.0;
            J[12] = 0.0;
            J[18] = inst->am[id] * nt->_dt;
            J[24] = 0.0;
            J[30] = 0.0;
            J[1] = 0.0;
            J[7] =  -inst->bh[id] * nt->_dt - 1.0;
            J[13] = 0.0;
            J[19] = 0.0;
            J[25] = inst->ah[id] * nt->_dt;
            J[31] = 0.0;
            J[2] = 0.0;
            J[8] = 0.0;
            J[14] =  -inst->bn[id] * nt->_dt - 1.0;
            J[20] = 0.0;
            J[26] = 0.0;
            J[32] = inst->an[id] * nt->_dt;
            J[3] = inst->bm[id] * nt->_dt;
            J[9] = 0.0;
            J[15] = 0.0;
            J[21] =  -inst->am[id] * nt->_dt - 1.0;
            J[27] = 0.0;
            J[33] = 0.0;
            J[4] = 0.0;
            J[10] = inst->bh[id] * nt->_dt;
            J[16] = 0.0;
            J[22] = 0.0;
            J[28] =  -inst->ah[id] * nt->_dt - 1.0;
            J[34] = 0.0;
            J[5] = 0.0;
            J[11] = 0.0;
            J[17] = inst->bn[id] * nt->_dt;
            J[23] = 0.0;
            J[29] = 0.0;
            J[35] =  -inst->an[id] * nt->_dt - 1.0;

            X = Eigen::PartialPivLU<Eigen::Ref<Eigen::Matrix<double, 6, 6>>>(Jm).solve(F);
            inst->m[id] = X[0];
            inst->h[id] = X[1];
            inst->n[id] = X[2];
            inst->mc[id] = X[3];
            inst->hc[id] = X[4];
            inst->nc[id] = X[5];

        }
    }


    /** register channel with the simulator */
    void _hhkin_reg()  {

        int mech_type = nrn_get_mechtype("hhkin");
        hhkin_global.mech_type = mech_type;
        if (mech_type == -1) {
            return;
        }

        _nrn_layout_reg(mech_type, get_memory_layout());
        register_mech(mechanism, nrn_alloc_hhkin, nrn_cur_hhkin, NULL, nrn_state_hhkin, nrn_init_hhkin, first_pointer_var_index(), 1);
        hhkin_global.na_type = nrn_get_mechtype("na_ion");
        hhkin_global.k_type = nrn_get_mechtype("k_ion");

        setup_global_variables();
        hoc_register_prop_size(mech_type, float_variables_size(), int_variables_size());
        hoc_register_dparam_semantics(mech_type, 0, "na_ion");
        hoc_register_dparam_semantics(mech_type, 1, "na_ion");
        hoc_register_dparam_semantics(mech_type, 2, "na_ion");
        hoc_register_dparam_semantics(mech_type, 3, "k_ion");
        hoc_register_dparam_semantics(mech_type, 4, "k_ion");
        hoc_register_dparam_semantics(mech_type, 5, "k_ion");
        hoc_register_var(hoc_scalar_double, hoc_vector_double, NULL);
    }
}
