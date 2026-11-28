#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_391600701176490780);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_3374625416350243041);
void pose_H_mod_fun(double *state, double *out_2220345416541066761);
void pose_f_fun(double *state, double dt, double *out_4446512712900270623);
void pose_F_fun(double *state, double dt, double *out_1222015542029334518);
void pose_h_4(double *state, double *unused, double *out_8397249766321913444);
void pose_H_4(double *state, double *unused, double *out_1053876662249882492);
void pose_h_10(double *state, double *unused, double *out_6226215451753727033);
void pose_H_10(double *state, double *unused, double *out_6912769925911205854);
void pose_h_13(double *state, double *unused, double *out_2707568773903906963);
void pose_H_13(double *state, double *unused, double *out_6556754546066818437);
void pose_h_14(double *state, double *unused, double *out_1470448093605001330);
void pose_H_14(double *state, double *unused, double *out_2909364194089602037);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}