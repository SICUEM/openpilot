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
void err_fun(double *nom_x, double *delta_x, double *out_6817535191504783905) {
   out_6817535191504783905[0] = delta_x[0] + nom_x[0];
   out_6817535191504783905[1] = delta_x[1] + nom_x[1];
   out_6817535191504783905[2] = delta_x[2] + nom_x[2];
   out_6817535191504783905[3] = delta_x[3] + nom_x[3];
   out_6817535191504783905[4] = delta_x[4] + nom_x[4];
   out_6817535191504783905[5] = delta_x[5] + nom_x[5];
   out_6817535191504783905[6] = delta_x[6] + nom_x[6];
   out_6817535191504783905[7] = delta_x[7] + nom_x[7];
   out_6817535191504783905[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_8482289000311789677) {
   out_8482289000311789677[0] = -nom_x[0] + true_x[0];
   out_8482289000311789677[1] = -nom_x[1] + true_x[1];
   out_8482289000311789677[2] = -nom_x[2] + true_x[2];
   out_8482289000311789677[3] = -nom_x[3] + true_x[3];
   out_8482289000311789677[4] = -nom_x[4] + true_x[4];
   out_8482289000311789677[5] = -nom_x[5] + true_x[5];
   out_8482289000311789677[6] = -nom_x[6] + true_x[6];
   out_8482289000311789677[7] = -nom_x[7] + true_x[7];
   out_8482289000311789677[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_382395767526373517) {
   out_382395767526373517[0] = 1.0;
   out_382395767526373517[1] = 0.0;
   out_382395767526373517[2] = 0.0;
   out_382395767526373517[3] = 0.0;
   out_382395767526373517[4] = 0.0;
   out_382395767526373517[5] = 0.0;
   out_382395767526373517[6] = 0.0;
   out_382395767526373517[7] = 0.0;
   out_382395767526373517[8] = 0.0;
   out_382395767526373517[9] = 0.0;
   out_382395767526373517[10] = 1.0;
   out_382395767526373517[11] = 0.0;
   out_382395767526373517[12] = 0.0;
   out_382395767526373517[13] = 0.0;
   out_382395767526373517[14] = 0.0;
   out_382395767526373517[15] = 0.0;
   out_382395767526373517[16] = 0.0;
   out_382395767526373517[17] = 0.0;
   out_382395767526373517[18] = 0.0;
   out_382395767526373517[19] = 0.0;
   out_382395767526373517[20] = 1.0;
   out_382395767526373517[21] = 0.0;
   out_382395767526373517[22] = 0.0;
   out_382395767526373517[23] = 0.0;
   out_382395767526373517[24] = 0.0;
   out_382395767526373517[25] = 0.0;
   out_382395767526373517[26] = 0.0;
   out_382395767526373517[27] = 0.0;
   out_382395767526373517[28] = 0.0;
   out_382395767526373517[29] = 0.0;
   out_382395767526373517[30] = 1.0;
   out_382395767526373517[31] = 0.0;
   out_382395767526373517[32] = 0.0;
   out_382395767526373517[33] = 0.0;
   out_382395767526373517[34] = 0.0;
   out_382395767526373517[35] = 0.0;
   out_382395767526373517[36] = 0.0;
   out_382395767526373517[37] = 0.0;
   out_382395767526373517[38] = 0.0;
   out_382395767526373517[39] = 0.0;
   out_382395767526373517[40] = 1.0;
   out_382395767526373517[41] = 0.0;
   out_382395767526373517[42] = 0.0;
   out_382395767526373517[43] = 0.0;
   out_382395767526373517[44] = 0.0;
   out_382395767526373517[45] = 0.0;
   out_382395767526373517[46] = 0.0;
   out_382395767526373517[47] = 0.0;
   out_382395767526373517[48] = 0.0;
   out_382395767526373517[49] = 0.0;
   out_382395767526373517[50] = 1.0;
   out_382395767526373517[51] = 0.0;
   out_382395767526373517[52] = 0.0;
   out_382395767526373517[53] = 0.0;
   out_382395767526373517[54] = 0.0;
   out_382395767526373517[55] = 0.0;
   out_382395767526373517[56] = 0.0;
   out_382395767526373517[57] = 0.0;
   out_382395767526373517[58] = 0.0;
   out_382395767526373517[59] = 0.0;
   out_382395767526373517[60] = 1.0;
   out_382395767526373517[61] = 0.0;
   out_382395767526373517[62] = 0.0;
   out_382395767526373517[63] = 0.0;
   out_382395767526373517[64] = 0.0;
   out_382395767526373517[65] = 0.0;
   out_382395767526373517[66] = 0.0;
   out_382395767526373517[67] = 0.0;
   out_382395767526373517[68] = 0.0;
   out_382395767526373517[69] = 0.0;
   out_382395767526373517[70] = 1.0;
   out_382395767526373517[71] = 0.0;
   out_382395767526373517[72] = 0.0;
   out_382395767526373517[73] = 0.0;
   out_382395767526373517[74] = 0.0;
   out_382395767526373517[75] = 0.0;
   out_382395767526373517[76] = 0.0;
   out_382395767526373517[77] = 0.0;
   out_382395767526373517[78] = 0.0;
   out_382395767526373517[79] = 0.0;
   out_382395767526373517[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_576475409094456213) {
   out_576475409094456213[0] = state[0];
   out_576475409094456213[1] = state[1];
   out_576475409094456213[2] = state[2];
   out_576475409094456213[3] = state[3];
   out_576475409094456213[4] = state[4];
   out_576475409094456213[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8000000000000007*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_576475409094456213[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_576475409094456213[7] = state[7];
   out_576475409094456213[8] = state[8];
}
void F_fun(double *state, double dt, double *out_5760595064791533026) {
   out_5760595064791533026[0] = 1;
   out_5760595064791533026[1] = 0;
   out_5760595064791533026[2] = 0;
   out_5760595064791533026[3] = 0;
   out_5760595064791533026[4] = 0;
   out_5760595064791533026[5] = 0;
   out_5760595064791533026[6] = 0;
   out_5760595064791533026[7] = 0;
   out_5760595064791533026[8] = 0;
   out_5760595064791533026[9] = 0;
   out_5760595064791533026[10] = 1;
   out_5760595064791533026[11] = 0;
   out_5760595064791533026[12] = 0;
   out_5760595064791533026[13] = 0;
   out_5760595064791533026[14] = 0;
   out_5760595064791533026[15] = 0;
   out_5760595064791533026[16] = 0;
   out_5760595064791533026[17] = 0;
   out_5760595064791533026[18] = 0;
   out_5760595064791533026[19] = 0;
   out_5760595064791533026[20] = 1;
   out_5760595064791533026[21] = 0;
   out_5760595064791533026[22] = 0;
   out_5760595064791533026[23] = 0;
   out_5760595064791533026[24] = 0;
   out_5760595064791533026[25] = 0;
   out_5760595064791533026[26] = 0;
   out_5760595064791533026[27] = 0;
   out_5760595064791533026[28] = 0;
   out_5760595064791533026[29] = 0;
   out_5760595064791533026[30] = 1;
   out_5760595064791533026[31] = 0;
   out_5760595064791533026[32] = 0;
   out_5760595064791533026[33] = 0;
   out_5760595064791533026[34] = 0;
   out_5760595064791533026[35] = 0;
   out_5760595064791533026[36] = 0;
   out_5760595064791533026[37] = 0;
   out_5760595064791533026[38] = 0;
   out_5760595064791533026[39] = 0;
   out_5760595064791533026[40] = 1;
   out_5760595064791533026[41] = 0;
   out_5760595064791533026[42] = 0;
   out_5760595064791533026[43] = 0;
   out_5760595064791533026[44] = 0;
   out_5760595064791533026[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_5760595064791533026[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_5760595064791533026[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_5760595064791533026[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_5760595064791533026[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_5760595064791533026[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_5760595064791533026[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_5760595064791533026[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_5760595064791533026[53] = -9.8000000000000007*dt;
   out_5760595064791533026[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_5760595064791533026[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_5760595064791533026[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5760595064791533026[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5760595064791533026[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_5760595064791533026[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_5760595064791533026[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_5760595064791533026[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5760595064791533026[62] = 0;
   out_5760595064791533026[63] = 0;
   out_5760595064791533026[64] = 0;
   out_5760595064791533026[65] = 0;
   out_5760595064791533026[66] = 0;
   out_5760595064791533026[67] = 0;
   out_5760595064791533026[68] = 0;
   out_5760595064791533026[69] = 0;
   out_5760595064791533026[70] = 1;
   out_5760595064791533026[71] = 0;
   out_5760595064791533026[72] = 0;
   out_5760595064791533026[73] = 0;
   out_5760595064791533026[74] = 0;
   out_5760595064791533026[75] = 0;
   out_5760595064791533026[76] = 0;
   out_5760595064791533026[77] = 0;
   out_5760595064791533026[78] = 0;
   out_5760595064791533026[79] = 0;
   out_5760595064791533026[80] = 1;
}
void h_25(double *state, double *unused, double *out_4256397903143255088) {
   out_4256397903143255088[0] = state[6];
}
void H_25(double *state, double *unused, double *out_3140584882463118160) {
   out_3140584882463118160[0] = 0;
   out_3140584882463118160[1] = 0;
   out_3140584882463118160[2] = 0;
   out_3140584882463118160[3] = 0;
   out_3140584882463118160[4] = 0;
   out_3140584882463118160[5] = 0;
   out_3140584882463118160[6] = 1;
   out_3140584882463118160[7] = 0;
   out_3140584882463118160[8] = 0;
}
void h_24(double *state, double *unused, double *out_3359041550823305585) {
   out_3359041550823305585[0] = state[4];
   out_3359041550823305585[1] = state[5];
}
void H_24(double *state, double *unused, double *out_841738268934649738) {
   out_841738268934649738[0] = 0;
   out_841738268934649738[1] = 0;
   out_841738268934649738[2] = 0;
   out_841738268934649738[3] = 0;
   out_841738268934649738[4] = 1;
   out_841738268934649738[5] = 0;
   out_841738268934649738[6] = 0;
   out_841738268934649738[7] = 0;
   out_841738268934649738[8] = 0;
   out_841738268934649738[9] = 0;
   out_841738268934649738[10] = 0;
   out_841738268934649738[11] = 0;
   out_841738268934649738[12] = 0;
   out_841738268934649738[13] = 0;
   out_841738268934649738[14] = 1;
   out_841738268934649738[15] = 0;
   out_841738268934649738[16] = 0;
   out_841738268934649738[17] = 0;
}
void h_30(double *state, double *unused, double *out_6309073519812247343) {
   out_6309073519812247343[0] = state[4];
}
void H_30(double *state, double *unused, double *out_5658917840970366787) {
   out_5658917840970366787[0] = 0;
   out_5658917840970366787[1] = 0;
   out_5658917840970366787[2] = 0;
   out_5658917840970366787[3] = 0;
   out_5658917840970366787[4] = 1;
   out_5658917840970366787[5] = 0;
   out_5658917840970366787[6] = 0;
   out_5658917840970366787[7] = 0;
   out_5658917840970366787[8] = 0;
}
void h_26(double *state, double *unused, double *out_1570927470305433413) {
   out_1570927470305433413[0] = state[7];
}
void H_26(double *state, double *unused, double *out_600918436410938064) {
   out_600918436410938064[0] = 0;
   out_600918436410938064[1] = 0;
   out_600918436410938064[2] = 0;
   out_600918436410938064[3] = 0;
   out_600918436410938064[4] = 0;
   out_600918436410938064[5] = 0;
   out_600918436410938064[6] = 0;
   out_600918436410938064[7] = 1;
   out_600918436410938064[8] = 0;
}
void h_27(double *state, double *unused, double *out_4859713787819732605) {
   out_4859713787819732605[0] = state[3];
}
void H_27(double *state, double *unused, double *out_7882511912154310004) {
   out_7882511912154310004[0] = 0;
   out_7882511912154310004[1] = 0;
   out_7882511912154310004[2] = 0;
   out_7882511912154310004[3] = 1;
   out_7882511912154310004[4] = 0;
   out_7882511912154310004[5] = 0;
   out_7882511912154310004[6] = 0;
   out_7882511912154310004[7] = 0;
   out_7882511912154310004[8] = 0;
}
void h_29(double *state, double *unused, double *out_1911121438530618331) {
   out_1911121438530618331[0] = state[1];
}
void H_29(double *state, double *unused, double *out_6169149185284758971) {
   out_6169149185284758971[0] = 0;
   out_6169149185284758971[1] = 1;
   out_6169149185284758971[2] = 0;
   out_6169149185284758971[3] = 0;
   out_6169149185284758971[4] = 0;
   out_6169149185284758971[5] = 0;
   out_6169149185284758971[6] = 0;
   out_6169149185284758971[7] = 0;
   out_6169149185284758971[8] = 0;
}
void h_28(double *state, double *unused, double *out_8585357018228973366) {
   out_8585357018228973366[0] = state[0];
}
void H_28(double *state, double *unused, double *out_1086750168215228397) {
   out_1086750168215228397[0] = 1;
   out_1086750168215228397[1] = 0;
   out_1086750168215228397[2] = 0;
   out_1086750168215228397[3] = 0;
   out_1086750168215228397[4] = 0;
   out_1086750168215228397[5] = 0;
   out_1086750168215228397[6] = 0;
   out_1086750168215228397[7] = 0;
   out_1086750168215228397[8] = 0;
}
void h_31(double *state, double *unused, double *out_1308671912787770127) {
   out_1308671912787770127[0] = state[8];
}
void H_31(double *state, double *unused, double *out_3171230844340078588) {
   out_3171230844340078588[0] = 0;
   out_3171230844340078588[1] = 0;
   out_3171230844340078588[2] = 0;
   out_3171230844340078588[3] = 0;
   out_3171230844340078588[4] = 0;
   out_3171230844340078588[5] = 0;
   out_3171230844340078588[6] = 0;
   out_3171230844340078588[7] = 0;
   out_3171230844340078588[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_6817535191504783905) {
  err_fun(nom_x, delta_x, out_6817535191504783905);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8482289000311789677) {
  inv_err_fun(nom_x, true_x, out_8482289000311789677);
}
void car_H_mod_fun(double *state, double *out_382395767526373517) {
  H_mod_fun(state, out_382395767526373517);
}
void car_f_fun(double *state, double dt, double *out_576475409094456213) {
  f_fun(state,  dt, out_576475409094456213);
}
void car_F_fun(double *state, double dt, double *out_5760595064791533026) {
  F_fun(state,  dt, out_5760595064791533026);
}
void car_h_25(double *state, double *unused, double *out_4256397903143255088) {
  h_25(state, unused, out_4256397903143255088);
}
void car_H_25(double *state, double *unused, double *out_3140584882463118160) {
  H_25(state, unused, out_3140584882463118160);
}
void car_h_24(double *state, double *unused, double *out_3359041550823305585) {
  h_24(state, unused, out_3359041550823305585);
}
void car_H_24(double *state, double *unused, double *out_841738268934649738) {
  H_24(state, unused, out_841738268934649738);
}
void car_h_30(double *state, double *unused, double *out_6309073519812247343) {
  h_30(state, unused, out_6309073519812247343);
}
void car_H_30(double *state, double *unused, double *out_5658917840970366787) {
  H_30(state, unused, out_5658917840970366787);
}
void car_h_26(double *state, double *unused, double *out_1570927470305433413) {
  h_26(state, unused, out_1570927470305433413);
}
void car_H_26(double *state, double *unused, double *out_600918436410938064) {
  H_26(state, unused, out_600918436410938064);
}
void car_h_27(double *state, double *unused, double *out_4859713787819732605) {
  h_27(state, unused, out_4859713787819732605);
}
void car_H_27(double *state, double *unused, double *out_7882511912154310004) {
  H_27(state, unused, out_7882511912154310004);
}
void car_h_29(double *state, double *unused, double *out_1911121438530618331) {
  h_29(state, unused, out_1911121438530618331);
}
void car_H_29(double *state, double *unused, double *out_6169149185284758971) {
  H_29(state, unused, out_6169149185284758971);
}
void car_h_28(double *state, double *unused, double *out_8585357018228973366) {
  h_28(state, unused, out_8585357018228973366);
}
void car_H_28(double *state, double *unused, double *out_1086750168215228397) {
  H_28(state, unused, out_1086750168215228397);
}
void car_h_31(double *state, double *unused, double *out_1308671912787770127) {
  h_31(state, unused, out_1308671912787770127);
}
void car_H_31(double *state, double *unused, double *out_3171230844340078588) {
  H_31(state, unused, out_3171230844340078588);
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
