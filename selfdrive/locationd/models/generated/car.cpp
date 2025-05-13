#include "car.h"

namespace {
#define DIM 9
#define EDIM 9
#define MEDIM 9
typedef void (*Hfun)(double *, double *, double *);

double mass;

void set_mass(double x){ mass = x;}

double rotational_inertia;

void set_rotational_inertia(double x){ rotational_inertia = x;}

double center_to_front;

void set_center_to_front(double x){ center_to_front = x;}

double center_to_rear;

void set_center_to_rear(double x){ center_to_rear = x;}

double stiffness_front;

void set_stiffness_front(double x){ stiffness_front = x;}

double stiffness_rear;

void set_stiffness_rear(double x){ stiffness_rear = x;}
const static double MAHA_THRESH_25 = 3.8414588206941227;
const static double MAHA_THRESH_24 = 5.991464547107981;
const static double MAHA_THRESH_30 = 3.8414588206941227;
const static double MAHA_THRESH_26 = 3.8414588206941227;
const static double MAHA_THRESH_27 = 3.8414588206941227;
const static double MAHA_THRESH_29 = 3.8414588206941227;
const static double MAHA_THRESH_28 = 3.8414588206941227;
const static double MAHA_THRESH_31 = 3.8414588206941227;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_5721690112960005807) {
   out_5721690112960005807[0] = delta_x[0] + nom_x[0];
   out_5721690112960005807[1] = delta_x[1] + nom_x[1];
   out_5721690112960005807[2] = delta_x[2] + nom_x[2];
   out_5721690112960005807[3] = delta_x[3] + nom_x[3];
   out_5721690112960005807[4] = delta_x[4] + nom_x[4];
   out_5721690112960005807[5] = delta_x[5] + nom_x[5];
   out_5721690112960005807[6] = delta_x[6] + nom_x[6];
   out_5721690112960005807[7] = delta_x[7] + nom_x[7];
   out_5721690112960005807[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_3354581765801783540) {
   out_3354581765801783540[0] = -nom_x[0] + true_x[0];
   out_3354581765801783540[1] = -nom_x[1] + true_x[1];
   out_3354581765801783540[2] = -nom_x[2] + true_x[2];
   out_3354581765801783540[3] = -nom_x[3] + true_x[3];
   out_3354581765801783540[4] = -nom_x[4] + true_x[4];
   out_3354581765801783540[5] = -nom_x[5] + true_x[5];
   out_3354581765801783540[6] = -nom_x[6] + true_x[6];
   out_3354581765801783540[7] = -nom_x[7] + true_x[7];
   out_3354581765801783540[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_6763287725758130608) {
   out_6763287725758130608[0] = 1.0;
   out_6763287725758130608[1] = 0.0;
   out_6763287725758130608[2] = 0.0;
   out_6763287725758130608[3] = 0.0;
   out_6763287725758130608[4] = 0.0;
   out_6763287725758130608[5] = 0.0;
   out_6763287725758130608[6] = 0.0;
   out_6763287725758130608[7] = 0.0;
   out_6763287725758130608[8] = 0.0;
   out_6763287725758130608[9] = 0.0;
   out_6763287725758130608[10] = 1.0;
   out_6763287725758130608[11] = 0.0;
   out_6763287725758130608[12] = 0.0;
   out_6763287725758130608[13] = 0.0;
   out_6763287725758130608[14] = 0.0;
   out_6763287725758130608[15] = 0.0;
   out_6763287725758130608[16] = 0.0;
   out_6763287725758130608[17] = 0.0;
   out_6763287725758130608[18] = 0.0;
   out_6763287725758130608[19] = 0.0;
   out_6763287725758130608[20] = 1.0;
   out_6763287725758130608[21] = 0.0;
   out_6763287725758130608[22] = 0.0;
   out_6763287725758130608[23] = 0.0;
   out_6763287725758130608[24] = 0.0;
   out_6763287725758130608[25] = 0.0;
   out_6763287725758130608[26] = 0.0;
   out_6763287725758130608[27] = 0.0;
   out_6763287725758130608[28] = 0.0;
   out_6763287725758130608[29] = 0.0;
   out_6763287725758130608[30] = 1.0;
   out_6763287725758130608[31] = 0.0;
   out_6763287725758130608[32] = 0.0;
   out_6763287725758130608[33] = 0.0;
   out_6763287725758130608[34] = 0.0;
   out_6763287725758130608[35] = 0.0;
   out_6763287725758130608[36] = 0.0;
   out_6763287725758130608[37] = 0.0;
   out_6763287725758130608[38] = 0.0;
   out_6763287725758130608[39] = 0.0;
   out_6763287725758130608[40] = 1.0;
   out_6763287725758130608[41] = 0.0;
   out_6763287725758130608[42] = 0.0;
   out_6763287725758130608[43] = 0.0;
   out_6763287725758130608[44] = 0.0;
   out_6763287725758130608[45] = 0.0;
   out_6763287725758130608[46] = 0.0;
   out_6763287725758130608[47] = 0.0;
   out_6763287725758130608[48] = 0.0;
   out_6763287725758130608[49] = 0.0;
   out_6763287725758130608[50] = 1.0;
   out_6763287725758130608[51] = 0.0;
   out_6763287725758130608[52] = 0.0;
   out_6763287725758130608[53] = 0.0;
   out_6763287725758130608[54] = 0.0;
   out_6763287725758130608[55] = 0.0;
   out_6763287725758130608[56] = 0.0;
   out_6763287725758130608[57] = 0.0;
   out_6763287725758130608[58] = 0.0;
   out_6763287725758130608[59] = 0.0;
   out_6763287725758130608[60] = 1.0;
   out_6763287725758130608[61] = 0.0;
   out_6763287725758130608[62] = 0.0;
   out_6763287725758130608[63] = 0.0;
   out_6763287725758130608[64] = 0.0;
   out_6763287725758130608[65] = 0.0;
   out_6763287725758130608[66] = 0.0;
   out_6763287725758130608[67] = 0.0;
   out_6763287725758130608[68] = 0.0;
   out_6763287725758130608[69] = 0.0;
   out_6763287725758130608[70] = 1.0;
   out_6763287725758130608[71] = 0.0;
   out_6763287725758130608[72] = 0.0;
   out_6763287725758130608[73] = 0.0;
   out_6763287725758130608[74] = 0.0;
   out_6763287725758130608[75] = 0.0;
   out_6763287725758130608[76] = 0.0;
   out_6763287725758130608[77] = 0.0;
   out_6763287725758130608[78] = 0.0;
   out_6763287725758130608[79] = 0.0;
   out_6763287725758130608[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_5370129116200662341) {
   out_5370129116200662341[0] = state[0];
   out_5370129116200662341[1] = state[1];
   out_5370129116200662341[2] = state[2];
   out_5370129116200662341[3] = state[3];
   out_5370129116200662341[4] = state[4];
   out_5370129116200662341[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8000000000000007*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_5370129116200662341[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_5370129116200662341[7] = state[7];
   out_5370129116200662341[8] = state[8];
}
void F_fun(double *state, double dt, double *out_4479757118695760498) {
   out_4479757118695760498[0] = 1;
   out_4479757118695760498[1] = 0;
   out_4479757118695760498[2] = 0;
   out_4479757118695760498[3] = 0;
   out_4479757118695760498[4] = 0;
   out_4479757118695760498[5] = 0;
   out_4479757118695760498[6] = 0;
   out_4479757118695760498[7] = 0;
   out_4479757118695760498[8] = 0;
   out_4479757118695760498[9] = 0;
   out_4479757118695760498[10] = 1;
   out_4479757118695760498[11] = 0;
   out_4479757118695760498[12] = 0;
   out_4479757118695760498[13] = 0;
   out_4479757118695760498[14] = 0;
   out_4479757118695760498[15] = 0;
   out_4479757118695760498[16] = 0;
   out_4479757118695760498[17] = 0;
   out_4479757118695760498[18] = 0;
   out_4479757118695760498[19] = 0;
   out_4479757118695760498[20] = 1;
   out_4479757118695760498[21] = 0;
   out_4479757118695760498[22] = 0;
   out_4479757118695760498[23] = 0;
   out_4479757118695760498[24] = 0;
   out_4479757118695760498[25] = 0;
   out_4479757118695760498[26] = 0;
   out_4479757118695760498[27] = 0;
   out_4479757118695760498[28] = 0;
   out_4479757118695760498[29] = 0;
   out_4479757118695760498[30] = 1;
   out_4479757118695760498[31] = 0;
   out_4479757118695760498[32] = 0;
   out_4479757118695760498[33] = 0;
   out_4479757118695760498[34] = 0;
   out_4479757118695760498[35] = 0;
   out_4479757118695760498[36] = 0;
   out_4479757118695760498[37] = 0;
   out_4479757118695760498[38] = 0;
   out_4479757118695760498[39] = 0;
   out_4479757118695760498[40] = 1;
   out_4479757118695760498[41] = 0;
   out_4479757118695760498[42] = 0;
   out_4479757118695760498[43] = 0;
   out_4479757118695760498[44] = 0;
   out_4479757118695760498[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_4479757118695760498[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_4479757118695760498[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_4479757118695760498[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_4479757118695760498[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_4479757118695760498[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_4479757118695760498[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_4479757118695760498[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_4479757118695760498[53] = -9.8000000000000007*dt;
   out_4479757118695760498[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_4479757118695760498[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_4479757118695760498[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_4479757118695760498[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_4479757118695760498[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_4479757118695760498[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_4479757118695760498[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_4479757118695760498[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_4479757118695760498[62] = 0;
   out_4479757118695760498[63] = 0;
   out_4479757118695760498[64] = 0;
   out_4479757118695760498[65] = 0;
   out_4479757118695760498[66] = 0;
   out_4479757118695760498[67] = 0;
   out_4479757118695760498[68] = 0;
   out_4479757118695760498[69] = 0;
   out_4479757118695760498[70] = 1;
   out_4479757118695760498[71] = 0;
   out_4479757118695760498[72] = 0;
   out_4479757118695760498[73] = 0;
   out_4479757118695760498[74] = 0;
   out_4479757118695760498[75] = 0;
   out_4479757118695760498[76] = 0;
   out_4479757118695760498[77] = 0;
   out_4479757118695760498[78] = 0;
   out_4479757118695760498[79] = 0;
   out_4479757118695760498[80] = 1;
}
void h_25(double *state, double *unused, double *out_56772556694138775) {
   out_56772556694138775[0] = state[6];
}
void H_25(double *state, double *unused, double *out_2429900500154106629) {
   out_2429900500154106629[0] = 0;
   out_2429900500154106629[1] = 0;
   out_2429900500154106629[2] = 0;
   out_2429900500154106629[3] = 0;
   out_2429900500154106629[4] = 0;
   out_2429900500154106629[5] = 0;
   out_2429900500154106629[6] = 1;
   out_2429900500154106629[7] = 0;
   out_2429900500154106629[8] = 0;
}
void h_24(double *state, double *unused, double *out_5560281843374542778) {
   out_5560281843374542778[0] = state[4];
   out_5560281843374542778[1] = state[5];
}
void H_24(double *state, double *unused, double *out_7176409827120615663) {
   out_7176409827120615663[0] = 0;
   out_7176409827120615663[1] = 0;
   out_7176409827120615663[2] = 0;
   out_7176409827120615663[3] = 0;
   out_7176409827120615663[4] = 1;
   out_7176409827120615663[5] = 0;
   out_7176409827120615663[6] = 0;
   out_7176409827120615663[7] = 0;
   out_7176409827120615663[8] = 0;
   out_7176409827120615663[9] = 0;
   out_7176409827120615663[10] = 0;
   out_7176409827120615663[11] = 0;
   out_7176409827120615663[12] = 0;
   out_7176409827120615663[13] = 0;
   out_7176409827120615663[14] = 1;
   out_7176409827120615663[15] = 0;
   out_7176409827120615663[16] = 0;
   out_7176409827120615663[17] = 0;
}
void h_30(double *state, double *unused, double *out_3580676971559883575) {
   out_3580676971559883575[0] = state[4];
}
void H_30(double *state, double *unused, double *out_88432458353141998) {
   out_88432458353141998[0] = 0;
   out_88432458353141998[1] = 0;
   out_88432458353141998[2] = 0;
   out_88432458353141998[3] = 0;
   out_88432458353141998[4] = 1;
   out_88432458353141998[5] = 0;
   out_88432458353141998[6] = 0;
   out_88432458353141998[7] = 0;
   out_88432458353141998[8] = 0;
}
void h_26(double *state, double *unused, double *out_6617463023004216260) {
   out_6617463023004216260[0] = state[7];
}
void H_26(double *state, double *unused, double *out_874625469606693972) {
   out_874625469606693972[0] = 0;
   out_874625469606693972[1] = 0;
   out_874625469606693972[2] = 0;
   out_874625469606693972[3] = 0;
   out_874625469606693972[4] = 0;
   out_874625469606693972[5] = 0;
   out_874625469606693972[6] = 0;
   out_874625469606693972[7] = 1;
   out_874625469606693972[8] = 0;
}
void h_27(double *state, double *unused, double *out_1000282409595801210) {
   out_1000282409595801210[0] = state[3];
}
void H_27(double *state, double *unused, double *out_2086330853447282913) {
   out_2086330853447282913[0] = 0;
   out_2086330853447282913[1] = 0;
   out_2086330853447282913[2] = 0;
   out_2086330853447282913[3] = 1;
   out_2086330853447282913[4] = 0;
   out_2086330853447282913[5] = 0;
   out_2086330853447282913[6] = 0;
   out_2086330853447282913[7] = 0;
   out_2086330853447282913[8] = 0;
}
void h_29(double *state, double *unused, double *out_2637167118658221140) {
   out_2637167118658221140[0] = state[1];
}
void H_29(double *state, double *unused, double *out_598663802667534182) {
   out_598663802667534182[0] = 0;
   out_598663802667534182[1] = 1;
   out_598663802667534182[2] = 0;
   out_598663802667534182[3] = 0;
   out_598663802667534182[4] = 0;
   out_598663802667534182[5] = 0;
   out_598663802667534182[6] = 0;
   out_598663802667534182[7] = 0;
   out_598663802667534182[8] = 0;
}
void h_28(double *state, double *unused, double *out_4037068461040133895) {
   out_4037068461040133895[0] = state[0];
}
void H_28(double *state, double *unused, double *out_4483735214401996392) {
   out_4483735214401996392[0] = 1;
   out_4483735214401996392[1] = 0;
   out_4483735214401996392[2] = 0;
   out_4483735214401996392[3] = 0;
   out_4483735214401996392[4] = 0;
   out_4483735214401996392[5] = 0;
   out_4483735214401996392[6] = 0;
   out_4483735214401996392[7] = 0;
   out_4483735214401996392[8] = 0;
}
void h_31(double *state, double *unused, double *out_1458603086992241470) {
   out_1458603086992241470[0] = state[8];
}
void H_31(double *state, double *unused, double *out_248417367373342496) {
   out_248417367373342496[0] = 0;
   out_248417367373342496[1] = 0;
   out_248417367373342496[2] = 0;
   out_248417367373342496[3] = 0;
   out_248417367373342496[4] = 0;
   out_248417367373342496[5] = 0;
   out_248417367373342496[6] = 0;
   out_248417367373342496[7] = 0;
   out_248417367373342496[8] = 1;
}
#include <eigen3/Eigen/Dense>
#include <iostream>

typedef Eigen::Matrix<double, DIM, DIM, Eigen::RowMajor> DDM;
typedef Eigen::Matrix<double, EDIM, EDIM, Eigen::RowMajor> EEM;
typedef Eigen::Matrix<double, DIM, EDIM, Eigen::RowMajor> DEM;

void predict(double *in_x, double *in_P, double *in_Q, double dt) {
  typedef Eigen::Matrix<double, MEDIM, MEDIM, Eigen::RowMajor> RRM;

  double nx[DIM] = {0};
  double in_F[EDIM*EDIM] = {0};

  // functions from sympy
  f_fun(in_x, dt, nx);
  F_fun(in_x, dt, in_F);


  EEM F(in_F);
  EEM P(in_P);
  EEM Q(in_Q);

  RRM F_main = F.topLeftCorner(MEDIM, MEDIM);
  P.topLeftCorner(MEDIM, MEDIM) = (F_main * P.topLeftCorner(MEDIM, MEDIM)) * F_main.transpose();
  P.topRightCorner(MEDIM, EDIM - MEDIM) = F_main * P.topRightCorner(MEDIM, EDIM - MEDIM);
  P.bottomLeftCorner(EDIM - MEDIM, MEDIM) = P.bottomLeftCorner(EDIM - MEDIM, MEDIM) * F_main.transpose();

  P = P + dt*Q;

  // copy out state
  memcpy(in_x, nx, DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
}

// note: extra_args dim only correct when null space projecting
// otherwise 1
template <int ZDIM, int EADIM, bool MAHA_TEST>
void update(double *in_x, double *in_P, Hfun h_fun, Hfun H_fun, Hfun Hea_fun, double *in_z, double *in_R, double *in_ea, double MAHA_THRESHOLD) {
  typedef Eigen::Matrix<double, ZDIM, ZDIM, Eigen::RowMajor> ZZM;
  typedef Eigen::Matrix<double, ZDIM, DIM, Eigen::RowMajor> ZDM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, EDIM, Eigen::RowMajor> XEM;
  //typedef Eigen::Matrix<double, EDIM, ZDIM, Eigen::RowMajor> EZM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, 1> X1M;
  typedef Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> XXM;

  double in_hx[ZDIM] = {0};
  double in_H[ZDIM * DIM] = {0};
  double in_H_mod[EDIM * DIM] = {0};
  double delta_x[EDIM] = {0};
  double x_new[DIM] = {0};


  // state x, P
  Eigen::Matrix<double, ZDIM, 1> z(in_z);
  EEM P(in_P);
  ZZM pre_R(in_R);

  // functions from sympy
  h_fun(in_x, in_ea, in_hx);
  H_fun(in_x, in_ea, in_H);
  ZDM pre_H(in_H);

  // get y (y = z - hx)
  Eigen::Matrix<double, ZDIM, 1> pre_y(in_hx); pre_y = z - pre_y;
  X1M y; XXM H; XXM R;
  if (Hea_fun){
    typedef Eigen::Matrix<double, ZDIM, EADIM, Eigen::RowMajor> ZAM;
    double in_Hea[ZDIM * EADIM] = {0};
    Hea_fun(in_x, in_ea, in_Hea);
    ZAM Hea(in_Hea);
    XXM A = Hea.transpose().fullPivLu().kernel();


    y = A.transpose() * pre_y;
    H = A.transpose() * pre_H;
    R = A.transpose() * pre_R * A;
  } else {
    y = pre_y;
    H = pre_H;
    R = pre_R;
  }
  // get modified H
  H_mod_fun(in_x, in_H_mod);
  DEM H_mod(in_H_mod);
  XEM H_err = H * H_mod;

  // Do mahalobis distance test
  if (MAHA_TEST){
    XXM a = (H_err * P * H_err.transpose() + R).inverse();
    double maha_dist = y.transpose() * a * y;
    if (maha_dist > MAHA_THRESHOLD){
      R = 1.0e16 * R;
    }
  }

  // Outlier resilient weighting
  double weight = 1;//(1.5)/(1 + y.squaredNorm()/R.sum());

  // kalman gains and I_KH
  XXM S = ((H_err * P) * H_err.transpose()) + R/weight;
  XEM KT = S.fullPivLu().solve(H_err * P.transpose());
  //EZM K = KT.transpose(); TODO: WHY DOES THIS NOT COMPILE?
  //EZM K = S.fullPivLu().solve(H_err * P.transpose()).transpose();
  //std::cout << "Here is the matrix rot:\n" << K << std::endl;
  EEM I_KH = Eigen::Matrix<double, EDIM, EDIM>::Identity() - (KT.transpose() * H_err);

  // update state by injecting dx
  Eigen::Matrix<double, EDIM, 1> dx(delta_x);
  dx  = (KT.transpose() * y);
  memcpy(delta_x, dx.data(), EDIM * sizeof(double));
  err_fun(in_x, delta_x, x_new);
  Eigen::Matrix<double, DIM, 1> x(x_new);

  // update cov
  P = ((I_KH * P) * I_KH.transpose()) + ((KT.transpose() * R) * KT);

  // copy out state
  memcpy(in_x, x.data(), DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
  memcpy(in_z, y.data(), y.rows() * sizeof(double));
}




}
extern "C" {

void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_25, H_25, NULL, in_z, in_R, in_ea, MAHA_THRESH_25);
}
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<2, 3, 0>(in_x, in_P, h_24, H_24, NULL, in_z, in_R, in_ea, MAHA_THRESH_24);
}
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_30, H_30, NULL, in_z, in_R, in_ea, MAHA_THRESH_30);
}
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_26, H_26, NULL, in_z, in_R, in_ea, MAHA_THRESH_26);
}
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_27, H_27, NULL, in_z, in_R, in_ea, MAHA_THRESH_27);
}
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_29, H_29, NULL, in_z, in_R, in_ea, MAHA_THRESH_29);
}
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_28, H_28, NULL, in_z, in_R, in_ea, MAHA_THRESH_28);
}
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_31, H_31, NULL, in_z, in_R, in_ea, MAHA_THRESH_31);
}
void car_err_fun(double *nom_x, double *delta_x, double *out_5721690112960005807) {
  err_fun(nom_x, delta_x, out_5721690112960005807);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_3354581765801783540) {
  inv_err_fun(nom_x, true_x, out_3354581765801783540);
}
void car_H_mod_fun(double *state, double *out_6763287725758130608) {
  H_mod_fun(state, out_6763287725758130608);
}
void car_f_fun(double *state, double dt, double *out_5370129116200662341) {
  f_fun(state,  dt, out_5370129116200662341);
}
void car_F_fun(double *state, double dt, double *out_4479757118695760498) {
  F_fun(state,  dt, out_4479757118695760498);
}
void car_h_25(double *state, double *unused, double *out_56772556694138775) {
  h_25(state, unused, out_56772556694138775);
}
void car_H_25(double *state, double *unused, double *out_2429900500154106629) {
  H_25(state, unused, out_2429900500154106629);
}
void car_h_24(double *state, double *unused, double *out_5560281843374542778) {
  h_24(state, unused, out_5560281843374542778);
}
void car_H_24(double *state, double *unused, double *out_7176409827120615663) {
  H_24(state, unused, out_7176409827120615663);
}
void car_h_30(double *state, double *unused, double *out_3580676971559883575) {
  h_30(state, unused, out_3580676971559883575);
}
void car_H_30(double *state, double *unused, double *out_88432458353141998) {
  H_30(state, unused, out_88432458353141998);
}
void car_h_26(double *state, double *unused, double *out_6617463023004216260) {
  h_26(state, unused, out_6617463023004216260);
}
void car_H_26(double *state, double *unused, double *out_874625469606693972) {
  H_26(state, unused, out_874625469606693972);
}
void car_h_27(double *state, double *unused, double *out_1000282409595801210) {
  h_27(state, unused, out_1000282409595801210);
}
void car_H_27(double *state, double *unused, double *out_2086330853447282913) {
  H_27(state, unused, out_2086330853447282913);
}
void car_h_29(double *state, double *unused, double *out_2637167118658221140) {
  h_29(state, unused, out_2637167118658221140);
}
void car_H_29(double *state, double *unused, double *out_598663802667534182) {
  H_29(state, unused, out_598663802667534182);
}
void car_h_28(double *state, double *unused, double *out_4037068461040133895) {
  h_28(state, unused, out_4037068461040133895);
}
void car_H_28(double *state, double *unused, double *out_4483735214401996392) {
  H_28(state, unused, out_4483735214401996392);
}
void car_h_31(double *state, double *unused, double *out_1458603086992241470) {
  h_31(state, unused, out_1458603086992241470);
}
void car_H_31(double *state, double *unused, double *out_248417367373342496) {
  H_31(state, unused, out_248417367373342496);
}
void car_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
void car_set_mass(double x) {
  set_mass(x);
}
void car_set_rotational_inertia(double x) {
  set_rotational_inertia(x);
}
void car_set_center_to_front(double x) {
  set_center_to_front(x);
}
void car_set_center_to_rear(double x) {
  set_center_to_rear(x);
}
void car_set_stiffness_front(double x) {
  set_stiffness_front(x);
}
void car_set_stiffness_rear(double x) {
  set_stiffness_rear(x);
}
}

const EKF car = {
  .name = "car",
  .kinds = { 25, 24, 30, 26, 27, 29, 28, 31 },
  .feature_kinds = {  },
  .f_fun = car_f_fun,
  .F_fun = car_F_fun,
  .err_fun = car_err_fun,
  .inv_err_fun = car_inv_err_fun,
  .H_mod_fun = car_H_mod_fun,
  .predict = car_predict,
  .hs = {
    { 25, car_h_25 },
    { 24, car_h_24 },
    { 30, car_h_30 },
    { 26, car_h_26 },
    { 27, car_h_27 },
    { 29, car_h_29 },
    { 28, car_h_28 },
    { 31, car_h_31 },
  },
  .Hs = {
    { 25, car_H_25 },
    { 24, car_H_24 },
    { 30, car_H_30 },
    { 26, car_H_26 },
    { 27, car_H_27 },
    { 29, car_H_29 },
    { 28, car_H_28 },
    { 31, car_H_31 },
  },
  .updates = {
    { 25, car_update_25 },
    { 24, car_update_24 },
    { 30, car_update_30 },
    { 26, car_update_26 },
    { 27, car_update_27 },
    { 29, car_update_29 },
    { 28, car_update_28 },
    { 31, car_update_31 },
  },
  .Hes = {
  },
  .sets = {
    { "mass", car_set_mass },
    { "rotational_inertia", car_set_rotational_inertia },
    { "center_to_front", car_set_center_to_front },
    { "center_to_rear", car_set_center_to_rear },
    { "stiffness_front", car_set_stiffness_front },
    { "stiffness_rear", car_set_stiffness_rear },
  },
  .extra_routines = {
  },
};

ekf_lib_init(car)
