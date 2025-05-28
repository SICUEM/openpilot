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
void car_err_fun(double *nom_x, double *delta_x, double *out_6817535191504783905);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8482289000311789677);
void car_H_mod_fun(double *state, double *out_382395767526373517);
void car_f_fun(double *state, double dt, double *out_576475409094456213);
void car_F_fun(double *state, double dt, double *out_5760595064791533026);
void car_h_25(double *state, double *unused, double *out_4256397903143255088);
void car_H_25(double *state, double *unused, double *out_3140584882463118160);
void car_h_24(double *state, double *unused, double *out_3359041550823305585);
void car_H_24(double *state, double *unused, double *out_841738268934649738);
void car_h_30(double *state, double *unused, double *out_6309073519812247343);
void car_H_30(double *state, double *unused, double *out_5658917840970366787);
void car_h_26(double *state, double *unused, double *out_1570927470305433413);
void car_H_26(double *state, double *unused, double *out_600918436410938064);
void car_h_27(double *state, double *unused, double *out_4859713787819732605);
void car_H_27(double *state, double *unused, double *out_7882511912154310004);
void car_h_29(double *state, double *unused, double *out_1911121438530618331);
void car_H_29(double *state, double *unused, double *out_6169149185284758971);
void car_h_28(double *state, double *unused, double *out_8585357018228973366);
void car_H_28(double *state, double *unused, double *out_1086750168215228397);
void car_h_31(double *state, double *unused, double *out_1308671912787770127);
void car_H_31(double *state, double *unused, double *out_3171230844340078588);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}