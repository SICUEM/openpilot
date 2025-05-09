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
void car_err_fun(double *nom_x, double *delta_x, double *out_8098960440858578624);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_3154293137930176178);
void car_H_mod_fun(double *state, double *out_5347005049005332191);
void car_f_fun(double *state, double dt, double *out_2438289479253098054);
void car_F_fun(double *state, double dt, double *out_4105542810922329074);
void car_h_25(double *state, double *unused, double *out_7208494296227778663);
void car_H_25(double *state, double *unused, double *out_749903317601042425);
void car_h_24(double *state, double *unused, double *out_538191516548567430);
void car_H_24(double *state, double *unused, double *out_2808022281201280711);
void car_h_30(double *state, double *unused, double *out_1655617128665242523);
void car_H_30(double *state, double *unused, double *out_6166787023890574330);
void car_h_26(double *state, double *unused, double *out_1381168922779090162);
void car_H_26(double *state, double *unused, double *out_2554622652159758176);
void car_h_27(double *state, double *unused, double *out_6236576509820927308);
void car_H_27(double *state, double *unused, double *out_3992023712090149419);
void car_h_29(double *state, double *unused, double *out_2599126981566904958);
void car_H_29(double *state, double *unused, double *out_2278660985220598386);
void car_h_28(double *state, double *unused, double *out_9173381512444291623);
void car_H_28(double *state, double *unused, double *out_2803738031848932188);
void car_h_31(double *state, double *unused, double *out_620666369751483500);
void car_H_31(double *state, double *unused, double *out_6326771932910774828);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}