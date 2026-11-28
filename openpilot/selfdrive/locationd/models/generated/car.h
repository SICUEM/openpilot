#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_err_fun(double *nom_x, double *delta_x, double *out_1232205435626782406);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_7152097647721288473);
void car_H_mod_fun(double *state, double *out_3575593915700917900);
void car_f_fun(double *state, double dt, double *out_3904257278707298762);
void car_F_fun(double *state, double dt, double *out_5680123238953389985);
void car_h_25(double *state, double *unused, double *out_868987620285352657);
void car_H_25(double *state, double *unused, double *out_5677961932096396479);
void car_h_24(double *state, double *unused, double *out_2095005001207080869);
void car_H_24(double *state, double *unused, double *out_3540716955543959912);
void car_h_30(double *state, double *unused, double *out_1144181682569858546);
void car_H_30(double *state, double *unused, double *out_5548622984953156409);
void car_h_26(double *state, double *unused, double *out_6505163490741475796);
void car_H_26(double *state, double *unused, double *out_1936458613222340255);
void car_h_27(double *state, double *unused, double *out_5870660887946198302);
void car_H_27(double *state, double *unused, double *out_3373859673152731498);
void car_h_29(double *state, double *unused, double *out_8818386878301683263);
void car_H_29(double *state, double *unused, double *out_1660496946283180465);
void car_h_28(double *state, double *unused, double *out_3111308284060642463);
void car_H_28(double *state, double *unused, double *out_3624127217848506716);
void car_h_31(double *state, double *unused, double *out_2768461907968669693);
void car_H_31(double *state, double *unused, double *out_5708607893973356907);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}