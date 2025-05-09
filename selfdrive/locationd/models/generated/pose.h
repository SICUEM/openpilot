#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_8846465336200542325);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_904878762552493072);
void pose_H_mod_fun(double *state, double *out_8522983127573850096);
void pose_f_fun(double *state, double dt, double *out_611896847437543302);
void pose_F_fun(double *state, double dt, double *out_3104916241349686315);
void pose_h_4(double *state, double *unused, double *out_6638106921781301540);
void pose_H_4(double *state, double *unused, double *out_7325035645690951992);
void pose_h_10(double *state, double *unused, double *out_7245991018613219639);
void pose_H_10(double *state, double *unused, double *out_3241674189223813251);
void pose_h_13(double *state, double *unused, double *out_3910102813404433436);
void pose_H_13(double *state, double *unused, double *out_4112761820358619191);
void pose_h_14(double *state, double *unused, double *out_4449773984855147180);
void pose_H_14(double *state, double *unused, double *out_8038919995723227328);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}