#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_5541459369101084294);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_2205697697981872470);
void pose_H_mod_fun(double *state, double *out_5441704980450863752);
void pose_f_fun(double *state, double dt, double *out_6977509595567259634);
void pose_F_fun(double *state, double dt, double *out_4929240761074066778);
void pose_h_4(double *state, double *unused, double *out_7829171151825984237);
void pose_H_4(double *state, double *unused, double *out_406376826301094969);
void pose_h_10(double *state, double *unused, double *out_7608125297515821150);
void pose_H_10(double *state, double *unused, double *out_8432157119955175331);
void pose_h_13(double *state, double *unused, double *out_2187629780182442219);
void pose_H_13(double *state, double *unused, double *out_2805896999031237832);
void pose_h_14(double *state, double *unused, double *out_7403982089292470191);
void pose_H_14(double *state, double *unused, double *out_3556864030038389560);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}