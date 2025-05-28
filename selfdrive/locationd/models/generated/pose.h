#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_7576548165016352808);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_3269481700032691791);
void pose_H_mod_fun(double *state, double *out_3135696547169702091);
void pose_f_fun(double *state, double dt, double *out_2367158378490033196);
void pose_F_fun(double *state, double dt, double *out_6441421400486242095);
void pose_h_4(double *state, double *unused, double *out_4573904491198962061);
void pose_H_4(double *state, double *unused, double *out_6445319511998695839);
void pose_h_10(double *state, double *unused, double *out_2344085230968916776);
void pose_H_10(double *state, double *unused, double *out_1355793170921322878);
void pose_h_13(double *state, double *unused, double *out_2891206438167930313);
void pose_H_13(double *state, double *unused, double *out_8789150736378522976);
void pose_h_14(double *state, double *unused, double *out_3674947514289008640);
void pose_H_14(double *state, double *unused, double *out_8038183705371371248);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}