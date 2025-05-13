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
void car_err_fun(double *nom_x, double *delta_x, double *out_5721690112960005807);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_3354581765801783540);
void car_H_mod_fun(double *state, double *out_6763287725758130608);
void car_f_fun(double *state, double dt, double *out_5370129116200662341);
void car_F_fun(double *state, double dt, double *out_4479757118695760498);
void car_h_25(double *state, double *unused, double *out_56772556694138775);
void car_H_25(double *state, double *unused, double *out_2429900500154106629);
void car_h_24(double *state, double *unused, double *out_5560281843374542778);
void car_H_24(double *state, double *unused, double *out_7176409827120615663);
void car_h_30(double *state, double *unused, double *out_3580676971559883575);
void car_H_30(double *state, double *unused, double *out_88432458353141998);
void car_h_26(double *state, double *unused, double *out_6617463023004216260);
void car_H_26(double *state, double *unused, double *out_874625469606693972);
void car_h_27(double *state, double *unused, double *out_1000282409595801210);
void car_H_27(double *state, double *unused, double *out_2086330853447282913);
void car_h_29(double *state, double *unused, double *out_2637167118658221140);
void car_H_29(double *state, double *unused, double *out_598663802667534182);
void car_h_28(double *state, double *unused, double *out_4037068461040133895);
void car_H_28(double *state, double *unused, double *out_4483735214401996392);
void car_h_31(double *state, double *unused, double *out_1458603086992241470);
void car_H_31(double *state, double *unused, double *out_248417367373342496);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}