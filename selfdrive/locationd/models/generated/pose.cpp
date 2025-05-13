#include "pose.h"

namespace {
#define DIM 18
#define EDIM 18
#define MEDIM 18
typedef void (*Hfun)(double *, double *, double *);
const static double MAHA_THRESH_4 = 7.814727903251177;
const static double MAHA_THRESH_10 = 7.814727903251177;
const static double MAHA_THRESH_13 = 7.814727903251177;
const static double MAHA_THRESH_14 = 7.814727903251177;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_5541459369101084294) {
   out_5541459369101084294[0] = delta_x[0] + nom_x[0];
   out_5541459369101084294[1] = delta_x[1] + nom_x[1];
   out_5541459369101084294[2] = delta_x[2] + nom_x[2];
   out_5541459369101084294[3] = delta_x[3] + nom_x[3];
   out_5541459369101084294[4] = delta_x[4] + nom_x[4];
   out_5541459369101084294[5] = delta_x[5] + nom_x[5];
   out_5541459369101084294[6] = delta_x[6] + nom_x[6];
   out_5541459369101084294[7] = delta_x[7] + nom_x[7];
   out_5541459369101084294[8] = delta_x[8] + nom_x[8];
   out_5541459369101084294[9] = delta_x[9] + nom_x[9];
   out_5541459369101084294[10] = delta_x[10] + nom_x[10];
   out_5541459369101084294[11] = delta_x[11] + nom_x[11];
   out_5541459369101084294[12] = delta_x[12] + nom_x[12];
   out_5541459369101084294[13] = delta_x[13] + nom_x[13];
   out_5541459369101084294[14] = delta_x[14] + nom_x[14];
   out_5541459369101084294[15] = delta_x[15] + nom_x[15];
   out_5541459369101084294[16] = delta_x[16] + nom_x[16];
   out_5541459369101084294[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_2205697697981872470) {
   out_2205697697981872470[0] = -nom_x[0] + true_x[0];
   out_2205697697981872470[1] = -nom_x[1] + true_x[1];
   out_2205697697981872470[2] = -nom_x[2] + true_x[2];
   out_2205697697981872470[3] = -nom_x[3] + true_x[3];
   out_2205697697981872470[4] = -nom_x[4] + true_x[4];
   out_2205697697981872470[5] = -nom_x[5] + true_x[5];
   out_2205697697981872470[6] = -nom_x[6] + true_x[6];
   out_2205697697981872470[7] = -nom_x[7] + true_x[7];
   out_2205697697981872470[8] = -nom_x[8] + true_x[8];
   out_2205697697981872470[9] = -nom_x[9] + true_x[9];
   out_2205697697981872470[10] = -nom_x[10] + true_x[10];
   out_2205697697981872470[11] = -nom_x[11] + true_x[11];
   out_2205697697981872470[12] = -nom_x[12] + true_x[12];
   out_2205697697981872470[13] = -nom_x[13] + true_x[13];
   out_2205697697981872470[14] = -nom_x[14] + true_x[14];
   out_2205697697981872470[15] = -nom_x[15] + true_x[15];
   out_2205697697981872470[16] = -nom_x[16] + true_x[16];
   out_2205697697981872470[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_5441704980450863752) {
   out_5441704980450863752[0] = 1.0;
   out_5441704980450863752[1] = 0.0;
   out_5441704980450863752[2] = 0.0;
   out_5441704980450863752[3] = 0.0;
   out_5441704980450863752[4] = 0.0;
   out_5441704980450863752[5] = 0.0;
   out_5441704980450863752[6] = 0.0;
   out_5441704980450863752[7] = 0.0;
   out_5441704980450863752[8] = 0.0;
   out_5441704980450863752[9] = 0.0;
   out_5441704980450863752[10] = 0.0;
   out_5441704980450863752[11] = 0.0;
   out_5441704980450863752[12] = 0.0;
   out_5441704980450863752[13] = 0.0;
   out_5441704980450863752[14] = 0.0;
   out_5441704980450863752[15] = 0.0;
   out_5441704980450863752[16] = 0.0;
   out_5441704980450863752[17] = 0.0;
   out_5441704980450863752[18] = 0.0;
   out_5441704980450863752[19] = 1.0;
   out_5441704980450863752[20] = 0.0;
   out_5441704980450863752[21] = 0.0;
   out_5441704980450863752[22] = 0.0;
   out_5441704980450863752[23] = 0.0;
   out_5441704980450863752[24] = 0.0;
   out_5441704980450863752[25] = 0.0;
   out_5441704980450863752[26] = 0.0;
   out_5441704980450863752[27] = 0.0;
   out_5441704980450863752[28] = 0.0;
   out_5441704980450863752[29] = 0.0;
   out_5441704980450863752[30] = 0.0;
   out_5441704980450863752[31] = 0.0;
   out_5441704980450863752[32] = 0.0;
   out_5441704980450863752[33] = 0.0;
   out_5441704980450863752[34] = 0.0;
   out_5441704980450863752[35] = 0.0;
   out_5441704980450863752[36] = 0.0;
   out_5441704980450863752[37] = 0.0;
   out_5441704980450863752[38] = 1.0;
   out_5441704980450863752[39] = 0.0;
   out_5441704980450863752[40] = 0.0;
   out_5441704980450863752[41] = 0.0;
   out_5441704980450863752[42] = 0.0;
   out_5441704980450863752[43] = 0.0;
   out_5441704980450863752[44] = 0.0;
   out_5441704980450863752[45] = 0.0;
   out_5441704980450863752[46] = 0.0;
   out_5441704980450863752[47] = 0.0;
   out_5441704980450863752[48] = 0.0;
   out_5441704980450863752[49] = 0.0;
   out_5441704980450863752[50] = 0.0;
   out_5441704980450863752[51] = 0.0;
   out_5441704980450863752[52] = 0.0;
   out_5441704980450863752[53] = 0.0;
   out_5441704980450863752[54] = 0.0;
   out_5441704980450863752[55] = 0.0;
   out_5441704980450863752[56] = 0.0;
   out_5441704980450863752[57] = 1.0;
   out_5441704980450863752[58] = 0.0;
   out_5441704980450863752[59] = 0.0;
   out_5441704980450863752[60] = 0.0;
   out_5441704980450863752[61] = 0.0;
   out_5441704980450863752[62] = 0.0;
   out_5441704980450863752[63] = 0.0;
   out_5441704980450863752[64] = 0.0;
   out_5441704980450863752[65] = 0.0;
   out_5441704980450863752[66] = 0.0;
   out_5441704980450863752[67] = 0.0;
   out_5441704980450863752[68] = 0.0;
   out_5441704980450863752[69] = 0.0;
   out_5441704980450863752[70] = 0.0;
   out_5441704980450863752[71] = 0.0;
   out_5441704980450863752[72] = 0.0;
   out_5441704980450863752[73] = 0.0;
   out_5441704980450863752[74] = 0.0;
   out_5441704980450863752[75] = 0.0;
   out_5441704980450863752[76] = 1.0;
   out_5441704980450863752[77] = 0.0;
   out_5441704980450863752[78] = 0.0;
   out_5441704980450863752[79] = 0.0;
   out_5441704980450863752[80] = 0.0;
   out_5441704980450863752[81] = 0.0;
   out_5441704980450863752[82] = 0.0;
   out_5441704980450863752[83] = 0.0;
   out_5441704980450863752[84] = 0.0;
   out_5441704980450863752[85] = 0.0;
   out_5441704980450863752[86] = 0.0;
   out_5441704980450863752[87] = 0.0;
   out_5441704980450863752[88] = 0.0;
   out_5441704980450863752[89] = 0.0;
   out_5441704980450863752[90] = 0.0;
   out_5441704980450863752[91] = 0.0;
   out_5441704980450863752[92] = 0.0;
   out_5441704980450863752[93] = 0.0;
   out_5441704980450863752[94] = 0.0;
   out_5441704980450863752[95] = 1.0;
   out_5441704980450863752[96] = 0.0;
   out_5441704980450863752[97] = 0.0;
   out_5441704980450863752[98] = 0.0;
   out_5441704980450863752[99] = 0.0;
   out_5441704980450863752[100] = 0.0;
   out_5441704980450863752[101] = 0.0;
   out_5441704980450863752[102] = 0.0;
   out_5441704980450863752[103] = 0.0;
   out_5441704980450863752[104] = 0.0;
   out_5441704980450863752[105] = 0.0;
   out_5441704980450863752[106] = 0.0;
   out_5441704980450863752[107] = 0.0;
   out_5441704980450863752[108] = 0.0;
   out_5441704980450863752[109] = 0.0;
   out_5441704980450863752[110] = 0.0;
   out_5441704980450863752[111] = 0.0;
   out_5441704980450863752[112] = 0.0;
   out_5441704980450863752[113] = 0.0;
   out_5441704980450863752[114] = 1.0;
   out_5441704980450863752[115] = 0.0;
   out_5441704980450863752[116] = 0.0;
   out_5441704980450863752[117] = 0.0;
   out_5441704980450863752[118] = 0.0;
   out_5441704980450863752[119] = 0.0;
   out_5441704980450863752[120] = 0.0;
   out_5441704980450863752[121] = 0.0;
   out_5441704980450863752[122] = 0.0;
   out_5441704980450863752[123] = 0.0;
   out_5441704980450863752[124] = 0.0;
   out_5441704980450863752[125] = 0.0;
   out_5441704980450863752[126] = 0.0;
   out_5441704980450863752[127] = 0.0;
   out_5441704980450863752[128] = 0.0;
   out_5441704980450863752[129] = 0.0;
   out_5441704980450863752[130] = 0.0;
   out_5441704980450863752[131] = 0.0;
   out_5441704980450863752[132] = 0.0;
   out_5441704980450863752[133] = 1.0;
   out_5441704980450863752[134] = 0.0;
   out_5441704980450863752[135] = 0.0;
   out_5441704980450863752[136] = 0.0;
   out_5441704980450863752[137] = 0.0;
   out_5441704980450863752[138] = 0.0;
   out_5441704980450863752[139] = 0.0;
   out_5441704980450863752[140] = 0.0;
   out_5441704980450863752[141] = 0.0;
   out_5441704980450863752[142] = 0.0;
   out_5441704980450863752[143] = 0.0;
   out_5441704980450863752[144] = 0.0;
   out_5441704980450863752[145] = 0.0;
   out_5441704980450863752[146] = 0.0;
   out_5441704980450863752[147] = 0.0;
   out_5441704980450863752[148] = 0.0;
   out_5441704980450863752[149] = 0.0;
   out_5441704980450863752[150] = 0.0;
   out_5441704980450863752[151] = 0.0;
   out_5441704980450863752[152] = 1.0;
   out_5441704980450863752[153] = 0.0;
   out_5441704980450863752[154] = 0.0;
   out_5441704980450863752[155] = 0.0;
   out_5441704980450863752[156] = 0.0;
   out_5441704980450863752[157] = 0.0;
   out_5441704980450863752[158] = 0.0;
   out_5441704980450863752[159] = 0.0;
   out_5441704980450863752[160] = 0.0;
   out_5441704980450863752[161] = 0.0;
   out_5441704980450863752[162] = 0.0;
   out_5441704980450863752[163] = 0.0;
   out_5441704980450863752[164] = 0.0;
   out_5441704980450863752[165] = 0.0;
   out_5441704980450863752[166] = 0.0;
   out_5441704980450863752[167] = 0.0;
   out_5441704980450863752[168] = 0.0;
   out_5441704980450863752[169] = 0.0;
   out_5441704980450863752[170] = 0.0;
   out_5441704980450863752[171] = 1.0;
   out_5441704980450863752[172] = 0.0;
   out_5441704980450863752[173] = 0.0;
   out_5441704980450863752[174] = 0.0;
   out_5441704980450863752[175] = 0.0;
   out_5441704980450863752[176] = 0.0;
   out_5441704980450863752[177] = 0.0;
   out_5441704980450863752[178] = 0.0;
   out_5441704980450863752[179] = 0.0;
   out_5441704980450863752[180] = 0.0;
   out_5441704980450863752[181] = 0.0;
   out_5441704980450863752[182] = 0.0;
   out_5441704980450863752[183] = 0.0;
   out_5441704980450863752[184] = 0.0;
   out_5441704980450863752[185] = 0.0;
   out_5441704980450863752[186] = 0.0;
   out_5441704980450863752[187] = 0.0;
   out_5441704980450863752[188] = 0.0;
   out_5441704980450863752[189] = 0.0;
   out_5441704980450863752[190] = 1.0;
   out_5441704980450863752[191] = 0.0;
   out_5441704980450863752[192] = 0.0;
   out_5441704980450863752[193] = 0.0;
   out_5441704980450863752[194] = 0.0;
   out_5441704980450863752[195] = 0.0;
   out_5441704980450863752[196] = 0.0;
   out_5441704980450863752[197] = 0.0;
   out_5441704980450863752[198] = 0.0;
   out_5441704980450863752[199] = 0.0;
   out_5441704980450863752[200] = 0.0;
   out_5441704980450863752[201] = 0.0;
   out_5441704980450863752[202] = 0.0;
   out_5441704980450863752[203] = 0.0;
   out_5441704980450863752[204] = 0.0;
   out_5441704980450863752[205] = 0.0;
   out_5441704980450863752[206] = 0.0;
   out_5441704980450863752[207] = 0.0;
   out_5441704980450863752[208] = 0.0;
   out_5441704980450863752[209] = 1.0;
   out_5441704980450863752[210] = 0.0;
   out_5441704980450863752[211] = 0.0;
   out_5441704980450863752[212] = 0.0;
   out_5441704980450863752[213] = 0.0;
   out_5441704980450863752[214] = 0.0;
   out_5441704980450863752[215] = 0.0;
   out_5441704980450863752[216] = 0.0;
   out_5441704980450863752[217] = 0.0;
   out_5441704980450863752[218] = 0.0;
   out_5441704980450863752[219] = 0.0;
   out_5441704980450863752[220] = 0.0;
   out_5441704980450863752[221] = 0.0;
   out_5441704980450863752[222] = 0.0;
   out_5441704980450863752[223] = 0.0;
   out_5441704980450863752[224] = 0.0;
   out_5441704980450863752[225] = 0.0;
   out_5441704980450863752[226] = 0.0;
   out_5441704980450863752[227] = 0.0;
   out_5441704980450863752[228] = 1.0;
   out_5441704980450863752[229] = 0.0;
   out_5441704980450863752[230] = 0.0;
   out_5441704980450863752[231] = 0.0;
   out_5441704980450863752[232] = 0.0;
   out_5441704980450863752[233] = 0.0;
   out_5441704980450863752[234] = 0.0;
   out_5441704980450863752[235] = 0.0;
   out_5441704980450863752[236] = 0.0;
   out_5441704980450863752[237] = 0.0;
   out_5441704980450863752[238] = 0.0;
   out_5441704980450863752[239] = 0.0;
   out_5441704980450863752[240] = 0.0;
   out_5441704980450863752[241] = 0.0;
   out_5441704980450863752[242] = 0.0;
   out_5441704980450863752[243] = 0.0;
   out_5441704980450863752[244] = 0.0;
   out_5441704980450863752[245] = 0.0;
   out_5441704980450863752[246] = 0.0;
   out_5441704980450863752[247] = 1.0;
   out_5441704980450863752[248] = 0.0;
   out_5441704980450863752[249] = 0.0;
   out_5441704980450863752[250] = 0.0;
   out_5441704980450863752[251] = 0.0;
   out_5441704980450863752[252] = 0.0;
   out_5441704980450863752[253] = 0.0;
   out_5441704980450863752[254] = 0.0;
   out_5441704980450863752[255] = 0.0;
   out_5441704980450863752[256] = 0.0;
   out_5441704980450863752[257] = 0.0;
   out_5441704980450863752[258] = 0.0;
   out_5441704980450863752[259] = 0.0;
   out_5441704980450863752[260] = 0.0;
   out_5441704980450863752[261] = 0.0;
   out_5441704980450863752[262] = 0.0;
   out_5441704980450863752[263] = 0.0;
   out_5441704980450863752[264] = 0.0;
   out_5441704980450863752[265] = 0.0;
   out_5441704980450863752[266] = 1.0;
   out_5441704980450863752[267] = 0.0;
   out_5441704980450863752[268] = 0.0;
   out_5441704980450863752[269] = 0.0;
   out_5441704980450863752[270] = 0.0;
   out_5441704980450863752[271] = 0.0;
   out_5441704980450863752[272] = 0.0;
   out_5441704980450863752[273] = 0.0;
   out_5441704980450863752[274] = 0.0;
   out_5441704980450863752[275] = 0.0;
   out_5441704980450863752[276] = 0.0;
   out_5441704980450863752[277] = 0.0;
   out_5441704980450863752[278] = 0.0;
   out_5441704980450863752[279] = 0.0;
   out_5441704980450863752[280] = 0.0;
   out_5441704980450863752[281] = 0.0;
   out_5441704980450863752[282] = 0.0;
   out_5441704980450863752[283] = 0.0;
   out_5441704980450863752[284] = 0.0;
   out_5441704980450863752[285] = 1.0;
   out_5441704980450863752[286] = 0.0;
   out_5441704980450863752[287] = 0.0;
   out_5441704980450863752[288] = 0.0;
   out_5441704980450863752[289] = 0.0;
   out_5441704980450863752[290] = 0.0;
   out_5441704980450863752[291] = 0.0;
   out_5441704980450863752[292] = 0.0;
   out_5441704980450863752[293] = 0.0;
   out_5441704980450863752[294] = 0.0;
   out_5441704980450863752[295] = 0.0;
   out_5441704980450863752[296] = 0.0;
   out_5441704980450863752[297] = 0.0;
   out_5441704980450863752[298] = 0.0;
   out_5441704980450863752[299] = 0.0;
   out_5441704980450863752[300] = 0.0;
   out_5441704980450863752[301] = 0.0;
   out_5441704980450863752[302] = 0.0;
   out_5441704980450863752[303] = 0.0;
   out_5441704980450863752[304] = 1.0;
   out_5441704980450863752[305] = 0.0;
   out_5441704980450863752[306] = 0.0;
   out_5441704980450863752[307] = 0.0;
   out_5441704980450863752[308] = 0.0;
   out_5441704980450863752[309] = 0.0;
   out_5441704980450863752[310] = 0.0;
   out_5441704980450863752[311] = 0.0;
   out_5441704980450863752[312] = 0.0;
   out_5441704980450863752[313] = 0.0;
   out_5441704980450863752[314] = 0.0;
   out_5441704980450863752[315] = 0.0;
   out_5441704980450863752[316] = 0.0;
   out_5441704980450863752[317] = 0.0;
   out_5441704980450863752[318] = 0.0;
   out_5441704980450863752[319] = 0.0;
   out_5441704980450863752[320] = 0.0;
   out_5441704980450863752[321] = 0.0;
   out_5441704980450863752[322] = 0.0;
   out_5441704980450863752[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_6977509595567259634) {
   out_6977509595567259634[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_6977509595567259634[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_6977509595567259634[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_6977509595567259634[3] = dt*state[12] + state[3];
   out_6977509595567259634[4] = dt*state[13] + state[4];
   out_6977509595567259634[5] = dt*state[14] + state[5];
   out_6977509595567259634[6] = state[6];
   out_6977509595567259634[7] = state[7];
   out_6977509595567259634[8] = state[8];
   out_6977509595567259634[9] = state[9];
   out_6977509595567259634[10] = state[10];
   out_6977509595567259634[11] = state[11];
   out_6977509595567259634[12] = state[12];
   out_6977509595567259634[13] = state[13];
   out_6977509595567259634[14] = state[14];
   out_6977509595567259634[15] = state[15];
   out_6977509595567259634[16] = state[16];
   out_6977509595567259634[17] = state[17];
}
void F_fun(double *state, double dt, double *out_4929240761074066778) {
   out_4929240761074066778[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4929240761074066778[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4929240761074066778[2] = 0;
   out_4929240761074066778[3] = 0;
   out_4929240761074066778[4] = 0;
   out_4929240761074066778[5] = 0;
   out_4929240761074066778[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4929240761074066778[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4929240761074066778[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4929240761074066778[9] = 0;
   out_4929240761074066778[10] = 0;
   out_4929240761074066778[11] = 0;
   out_4929240761074066778[12] = 0;
   out_4929240761074066778[13] = 0;
   out_4929240761074066778[14] = 0;
   out_4929240761074066778[15] = 0;
   out_4929240761074066778[16] = 0;
   out_4929240761074066778[17] = 0;
   out_4929240761074066778[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4929240761074066778[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4929240761074066778[20] = 0;
   out_4929240761074066778[21] = 0;
   out_4929240761074066778[22] = 0;
   out_4929240761074066778[23] = 0;
   out_4929240761074066778[24] = 0;
   out_4929240761074066778[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4929240761074066778[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4929240761074066778[27] = 0;
   out_4929240761074066778[28] = 0;
   out_4929240761074066778[29] = 0;
   out_4929240761074066778[30] = 0;
   out_4929240761074066778[31] = 0;
   out_4929240761074066778[32] = 0;
   out_4929240761074066778[33] = 0;
   out_4929240761074066778[34] = 0;
   out_4929240761074066778[35] = 0;
   out_4929240761074066778[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4929240761074066778[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4929240761074066778[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4929240761074066778[39] = 0;
   out_4929240761074066778[40] = 0;
   out_4929240761074066778[41] = 0;
   out_4929240761074066778[42] = 0;
   out_4929240761074066778[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4929240761074066778[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4929240761074066778[45] = 0;
   out_4929240761074066778[46] = 0;
   out_4929240761074066778[47] = 0;
   out_4929240761074066778[48] = 0;
   out_4929240761074066778[49] = 0;
   out_4929240761074066778[50] = 0;
   out_4929240761074066778[51] = 0;
   out_4929240761074066778[52] = 0;
   out_4929240761074066778[53] = 0;
   out_4929240761074066778[54] = 0;
   out_4929240761074066778[55] = 0;
   out_4929240761074066778[56] = 0;
   out_4929240761074066778[57] = 1;
   out_4929240761074066778[58] = 0;
   out_4929240761074066778[59] = 0;
   out_4929240761074066778[60] = 0;
   out_4929240761074066778[61] = 0;
   out_4929240761074066778[62] = 0;
   out_4929240761074066778[63] = 0;
   out_4929240761074066778[64] = 0;
   out_4929240761074066778[65] = 0;
   out_4929240761074066778[66] = dt;
   out_4929240761074066778[67] = 0;
   out_4929240761074066778[68] = 0;
   out_4929240761074066778[69] = 0;
   out_4929240761074066778[70] = 0;
   out_4929240761074066778[71] = 0;
   out_4929240761074066778[72] = 0;
   out_4929240761074066778[73] = 0;
   out_4929240761074066778[74] = 0;
   out_4929240761074066778[75] = 0;
   out_4929240761074066778[76] = 1;
   out_4929240761074066778[77] = 0;
   out_4929240761074066778[78] = 0;
   out_4929240761074066778[79] = 0;
   out_4929240761074066778[80] = 0;
   out_4929240761074066778[81] = 0;
   out_4929240761074066778[82] = 0;
   out_4929240761074066778[83] = 0;
   out_4929240761074066778[84] = 0;
   out_4929240761074066778[85] = dt;
   out_4929240761074066778[86] = 0;
   out_4929240761074066778[87] = 0;
   out_4929240761074066778[88] = 0;
   out_4929240761074066778[89] = 0;
   out_4929240761074066778[90] = 0;
   out_4929240761074066778[91] = 0;
   out_4929240761074066778[92] = 0;
   out_4929240761074066778[93] = 0;
   out_4929240761074066778[94] = 0;
   out_4929240761074066778[95] = 1;
   out_4929240761074066778[96] = 0;
   out_4929240761074066778[97] = 0;
   out_4929240761074066778[98] = 0;
   out_4929240761074066778[99] = 0;
   out_4929240761074066778[100] = 0;
   out_4929240761074066778[101] = 0;
   out_4929240761074066778[102] = 0;
   out_4929240761074066778[103] = 0;
   out_4929240761074066778[104] = dt;
   out_4929240761074066778[105] = 0;
   out_4929240761074066778[106] = 0;
   out_4929240761074066778[107] = 0;
   out_4929240761074066778[108] = 0;
   out_4929240761074066778[109] = 0;
   out_4929240761074066778[110] = 0;
   out_4929240761074066778[111] = 0;
   out_4929240761074066778[112] = 0;
   out_4929240761074066778[113] = 0;
   out_4929240761074066778[114] = 1;
   out_4929240761074066778[115] = 0;
   out_4929240761074066778[116] = 0;
   out_4929240761074066778[117] = 0;
   out_4929240761074066778[118] = 0;
   out_4929240761074066778[119] = 0;
   out_4929240761074066778[120] = 0;
   out_4929240761074066778[121] = 0;
   out_4929240761074066778[122] = 0;
   out_4929240761074066778[123] = 0;
   out_4929240761074066778[124] = 0;
   out_4929240761074066778[125] = 0;
   out_4929240761074066778[126] = 0;
   out_4929240761074066778[127] = 0;
   out_4929240761074066778[128] = 0;
   out_4929240761074066778[129] = 0;
   out_4929240761074066778[130] = 0;
   out_4929240761074066778[131] = 0;
   out_4929240761074066778[132] = 0;
   out_4929240761074066778[133] = 1;
   out_4929240761074066778[134] = 0;
   out_4929240761074066778[135] = 0;
   out_4929240761074066778[136] = 0;
   out_4929240761074066778[137] = 0;
   out_4929240761074066778[138] = 0;
   out_4929240761074066778[139] = 0;
   out_4929240761074066778[140] = 0;
   out_4929240761074066778[141] = 0;
   out_4929240761074066778[142] = 0;
   out_4929240761074066778[143] = 0;
   out_4929240761074066778[144] = 0;
   out_4929240761074066778[145] = 0;
   out_4929240761074066778[146] = 0;
   out_4929240761074066778[147] = 0;
   out_4929240761074066778[148] = 0;
   out_4929240761074066778[149] = 0;
   out_4929240761074066778[150] = 0;
   out_4929240761074066778[151] = 0;
   out_4929240761074066778[152] = 1;
   out_4929240761074066778[153] = 0;
   out_4929240761074066778[154] = 0;
   out_4929240761074066778[155] = 0;
   out_4929240761074066778[156] = 0;
   out_4929240761074066778[157] = 0;
   out_4929240761074066778[158] = 0;
   out_4929240761074066778[159] = 0;
   out_4929240761074066778[160] = 0;
   out_4929240761074066778[161] = 0;
   out_4929240761074066778[162] = 0;
   out_4929240761074066778[163] = 0;
   out_4929240761074066778[164] = 0;
   out_4929240761074066778[165] = 0;
   out_4929240761074066778[166] = 0;
   out_4929240761074066778[167] = 0;
   out_4929240761074066778[168] = 0;
   out_4929240761074066778[169] = 0;
   out_4929240761074066778[170] = 0;
   out_4929240761074066778[171] = 1;
   out_4929240761074066778[172] = 0;
   out_4929240761074066778[173] = 0;
   out_4929240761074066778[174] = 0;
   out_4929240761074066778[175] = 0;
   out_4929240761074066778[176] = 0;
   out_4929240761074066778[177] = 0;
   out_4929240761074066778[178] = 0;
   out_4929240761074066778[179] = 0;
   out_4929240761074066778[180] = 0;
   out_4929240761074066778[181] = 0;
   out_4929240761074066778[182] = 0;
   out_4929240761074066778[183] = 0;
   out_4929240761074066778[184] = 0;
   out_4929240761074066778[185] = 0;
   out_4929240761074066778[186] = 0;
   out_4929240761074066778[187] = 0;
   out_4929240761074066778[188] = 0;
   out_4929240761074066778[189] = 0;
   out_4929240761074066778[190] = 1;
   out_4929240761074066778[191] = 0;
   out_4929240761074066778[192] = 0;
   out_4929240761074066778[193] = 0;
   out_4929240761074066778[194] = 0;
   out_4929240761074066778[195] = 0;
   out_4929240761074066778[196] = 0;
   out_4929240761074066778[197] = 0;
   out_4929240761074066778[198] = 0;
   out_4929240761074066778[199] = 0;
   out_4929240761074066778[200] = 0;
   out_4929240761074066778[201] = 0;
   out_4929240761074066778[202] = 0;
   out_4929240761074066778[203] = 0;
   out_4929240761074066778[204] = 0;
   out_4929240761074066778[205] = 0;
   out_4929240761074066778[206] = 0;
   out_4929240761074066778[207] = 0;
   out_4929240761074066778[208] = 0;
   out_4929240761074066778[209] = 1;
   out_4929240761074066778[210] = 0;
   out_4929240761074066778[211] = 0;
   out_4929240761074066778[212] = 0;
   out_4929240761074066778[213] = 0;
   out_4929240761074066778[214] = 0;
   out_4929240761074066778[215] = 0;
   out_4929240761074066778[216] = 0;
   out_4929240761074066778[217] = 0;
   out_4929240761074066778[218] = 0;
   out_4929240761074066778[219] = 0;
   out_4929240761074066778[220] = 0;
   out_4929240761074066778[221] = 0;
   out_4929240761074066778[222] = 0;
   out_4929240761074066778[223] = 0;
   out_4929240761074066778[224] = 0;
   out_4929240761074066778[225] = 0;
   out_4929240761074066778[226] = 0;
   out_4929240761074066778[227] = 0;
   out_4929240761074066778[228] = 1;
   out_4929240761074066778[229] = 0;
   out_4929240761074066778[230] = 0;
   out_4929240761074066778[231] = 0;
   out_4929240761074066778[232] = 0;
   out_4929240761074066778[233] = 0;
   out_4929240761074066778[234] = 0;
   out_4929240761074066778[235] = 0;
   out_4929240761074066778[236] = 0;
   out_4929240761074066778[237] = 0;
   out_4929240761074066778[238] = 0;
   out_4929240761074066778[239] = 0;
   out_4929240761074066778[240] = 0;
   out_4929240761074066778[241] = 0;
   out_4929240761074066778[242] = 0;
   out_4929240761074066778[243] = 0;
   out_4929240761074066778[244] = 0;
   out_4929240761074066778[245] = 0;
   out_4929240761074066778[246] = 0;
   out_4929240761074066778[247] = 1;
   out_4929240761074066778[248] = 0;
   out_4929240761074066778[249] = 0;
   out_4929240761074066778[250] = 0;
   out_4929240761074066778[251] = 0;
   out_4929240761074066778[252] = 0;
   out_4929240761074066778[253] = 0;
   out_4929240761074066778[254] = 0;
   out_4929240761074066778[255] = 0;
   out_4929240761074066778[256] = 0;
   out_4929240761074066778[257] = 0;
   out_4929240761074066778[258] = 0;
   out_4929240761074066778[259] = 0;
   out_4929240761074066778[260] = 0;
   out_4929240761074066778[261] = 0;
   out_4929240761074066778[262] = 0;
   out_4929240761074066778[263] = 0;
   out_4929240761074066778[264] = 0;
   out_4929240761074066778[265] = 0;
   out_4929240761074066778[266] = 1;
   out_4929240761074066778[267] = 0;
   out_4929240761074066778[268] = 0;
   out_4929240761074066778[269] = 0;
   out_4929240761074066778[270] = 0;
   out_4929240761074066778[271] = 0;
   out_4929240761074066778[272] = 0;
   out_4929240761074066778[273] = 0;
   out_4929240761074066778[274] = 0;
   out_4929240761074066778[275] = 0;
   out_4929240761074066778[276] = 0;
   out_4929240761074066778[277] = 0;
   out_4929240761074066778[278] = 0;
   out_4929240761074066778[279] = 0;
   out_4929240761074066778[280] = 0;
   out_4929240761074066778[281] = 0;
   out_4929240761074066778[282] = 0;
   out_4929240761074066778[283] = 0;
   out_4929240761074066778[284] = 0;
   out_4929240761074066778[285] = 1;
   out_4929240761074066778[286] = 0;
   out_4929240761074066778[287] = 0;
   out_4929240761074066778[288] = 0;
   out_4929240761074066778[289] = 0;
   out_4929240761074066778[290] = 0;
   out_4929240761074066778[291] = 0;
   out_4929240761074066778[292] = 0;
   out_4929240761074066778[293] = 0;
   out_4929240761074066778[294] = 0;
   out_4929240761074066778[295] = 0;
   out_4929240761074066778[296] = 0;
   out_4929240761074066778[297] = 0;
   out_4929240761074066778[298] = 0;
   out_4929240761074066778[299] = 0;
   out_4929240761074066778[300] = 0;
   out_4929240761074066778[301] = 0;
   out_4929240761074066778[302] = 0;
   out_4929240761074066778[303] = 0;
   out_4929240761074066778[304] = 1;
   out_4929240761074066778[305] = 0;
   out_4929240761074066778[306] = 0;
   out_4929240761074066778[307] = 0;
   out_4929240761074066778[308] = 0;
   out_4929240761074066778[309] = 0;
   out_4929240761074066778[310] = 0;
   out_4929240761074066778[311] = 0;
   out_4929240761074066778[312] = 0;
   out_4929240761074066778[313] = 0;
   out_4929240761074066778[314] = 0;
   out_4929240761074066778[315] = 0;
   out_4929240761074066778[316] = 0;
   out_4929240761074066778[317] = 0;
   out_4929240761074066778[318] = 0;
   out_4929240761074066778[319] = 0;
   out_4929240761074066778[320] = 0;
   out_4929240761074066778[321] = 0;
   out_4929240761074066778[322] = 0;
   out_4929240761074066778[323] = 1;
}
void h_4(double *state, double *unused, double *out_7829171151825984237) {
   out_7829171151825984237[0] = state[6] + state[9];
   out_7829171151825984237[1] = state[7] + state[10];
   out_7829171151825984237[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_406376826301094969) {
   out_406376826301094969[0] = 0;
   out_406376826301094969[1] = 0;
   out_406376826301094969[2] = 0;
   out_406376826301094969[3] = 0;
   out_406376826301094969[4] = 0;
   out_406376826301094969[5] = 0;
   out_406376826301094969[6] = 1;
   out_406376826301094969[7] = 0;
   out_406376826301094969[8] = 0;
   out_406376826301094969[9] = 1;
   out_406376826301094969[10] = 0;
   out_406376826301094969[11] = 0;
   out_406376826301094969[12] = 0;
   out_406376826301094969[13] = 0;
   out_406376826301094969[14] = 0;
   out_406376826301094969[15] = 0;
   out_406376826301094969[16] = 0;
   out_406376826301094969[17] = 0;
   out_406376826301094969[18] = 0;
   out_406376826301094969[19] = 0;
   out_406376826301094969[20] = 0;
   out_406376826301094969[21] = 0;
   out_406376826301094969[22] = 0;
   out_406376826301094969[23] = 0;
   out_406376826301094969[24] = 0;
   out_406376826301094969[25] = 1;
   out_406376826301094969[26] = 0;
   out_406376826301094969[27] = 0;
   out_406376826301094969[28] = 1;
   out_406376826301094969[29] = 0;
   out_406376826301094969[30] = 0;
   out_406376826301094969[31] = 0;
   out_406376826301094969[32] = 0;
   out_406376826301094969[33] = 0;
   out_406376826301094969[34] = 0;
   out_406376826301094969[35] = 0;
   out_406376826301094969[36] = 0;
   out_406376826301094969[37] = 0;
   out_406376826301094969[38] = 0;
   out_406376826301094969[39] = 0;
   out_406376826301094969[40] = 0;
   out_406376826301094969[41] = 0;
   out_406376826301094969[42] = 0;
   out_406376826301094969[43] = 0;
   out_406376826301094969[44] = 1;
   out_406376826301094969[45] = 0;
   out_406376826301094969[46] = 0;
   out_406376826301094969[47] = 1;
   out_406376826301094969[48] = 0;
   out_406376826301094969[49] = 0;
   out_406376826301094969[50] = 0;
   out_406376826301094969[51] = 0;
   out_406376826301094969[52] = 0;
   out_406376826301094969[53] = 0;
}
void h_10(double *state, double *unused, double *out_7608125297515821150) {
   out_7608125297515821150[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_7608125297515821150[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_7608125297515821150[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_8432157119955175331) {
   out_8432157119955175331[0] = 0;
   out_8432157119955175331[1] = 9.8100000000000005*cos(state[1]);
   out_8432157119955175331[2] = 0;
   out_8432157119955175331[3] = 0;
   out_8432157119955175331[4] = -state[8];
   out_8432157119955175331[5] = state[7];
   out_8432157119955175331[6] = 0;
   out_8432157119955175331[7] = state[5];
   out_8432157119955175331[8] = -state[4];
   out_8432157119955175331[9] = 0;
   out_8432157119955175331[10] = 0;
   out_8432157119955175331[11] = 0;
   out_8432157119955175331[12] = 1;
   out_8432157119955175331[13] = 0;
   out_8432157119955175331[14] = 0;
   out_8432157119955175331[15] = 1;
   out_8432157119955175331[16] = 0;
   out_8432157119955175331[17] = 0;
   out_8432157119955175331[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_8432157119955175331[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_8432157119955175331[20] = 0;
   out_8432157119955175331[21] = state[8];
   out_8432157119955175331[22] = 0;
   out_8432157119955175331[23] = -state[6];
   out_8432157119955175331[24] = -state[5];
   out_8432157119955175331[25] = 0;
   out_8432157119955175331[26] = state[3];
   out_8432157119955175331[27] = 0;
   out_8432157119955175331[28] = 0;
   out_8432157119955175331[29] = 0;
   out_8432157119955175331[30] = 0;
   out_8432157119955175331[31] = 1;
   out_8432157119955175331[32] = 0;
   out_8432157119955175331[33] = 0;
   out_8432157119955175331[34] = 1;
   out_8432157119955175331[35] = 0;
   out_8432157119955175331[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_8432157119955175331[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_8432157119955175331[38] = 0;
   out_8432157119955175331[39] = -state[7];
   out_8432157119955175331[40] = state[6];
   out_8432157119955175331[41] = 0;
   out_8432157119955175331[42] = state[4];
   out_8432157119955175331[43] = -state[3];
   out_8432157119955175331[44] = 0;
   out_8432157119955175331[45] = 0;
   out_8432157119955175331[46] = 0;
   out_8432157119955175331[47] = 0;
   out_8432157119955175331[48] = 0;
   out_8432157119955175331[49] = 0;
   out_8432157119955175331[50] = 1;
   out_8432157119955175331[51] = 0;
   out_8432157119955175331[52] = 0;
   out_8432157119955175331[53] = 1;
}
void h_13(double *state, double *unused, double *out_2187629780182442219) {
   out_2187629780182442219[0] = state[3];
   out_2187629780182442219[1] = state[4];
   out_2187629780182442219[2] = state[5];
}
void H_13(double *state, double *unused, double *out_2805896999031237832) {
   out_2805896999031237832[0] = 0;
   out_2805896999031237832[1] = 0;
   out_2805896999031237832[2] = 0;
   out_2805896999031237832[3] = 1;
   out_2805896999031237832[4] = 0;
   out_2805896999031237832[5] = 0;
   out_2805896999031237832[6] = 0;
   out_2805896999031237832[7] = 0;
   out_2805896999031237832[8] = 0;
   out_2805896999031237832[9] = 0;
   out_2805896999031237832[10] = 0;
   out_2805896999031237832[11] = 0;
   out_2805896999031237832[12] = 0;
   out_2805896999031237832[13] = 0;
   out_2805896999031237832[14] = 0;
   out_2805896999031237832[15] = 0;
   out_2805896999031237832[16] = 0;
   out_2805896999031237832[17] = 0;
   out_2805896999031237832[18] = 0;
   out_2805896999031237832[19] = 0;
   out_2805896999031237832[20] = 0;
   out_2805896999031237832[21] = 0;
   out_2805896999031237832[22] = 1;
   out_2805896999031237832[23] = 0;
   out_2805896999031237832[24] = 0;
   out_2805896999031237832[25] = 0;
   out_2805896999031237832[26] = 0;
   out_2805896999031237832[27] = 0;
   out_2805896999031237832[28] = 0;
   out_2805896999031237832[29] = 0;
   out_2805896999031237832[30] = 0;
   out_2805896999031237832[31] = 0;
   out_2805896999031237832[32] = 0;
   out_2805896999031237832[33] = 0;
   out_2805896999031237832[34] = 0;
   out_2805896999031237832[35] = 0;
   out_2805896999031237832[36] = 0;
   out_2805896999031237832[37] = 0;
   out_2805896999031237832[38] = 0;
   out_2805896999031237832[39] = 0;
   out_2805896999031237832[40] = 0;
   out_2805896999031237832[41] = 1;
   out_2805896999031237832[42] = 0;
   out_2805896999031237832[43] = 0;
   out_2805896999031237832[44] = 0;
   out_2805896999031237832[45] = 0;
   out_2805896999031237832[46] = 0;
   out_2805896999031237832[47] = 0;
   out_2805896999031237832[48] = 0;
   out_2805896999031237832[49] = 0;
   out_2805896999031237832[50] = 0;
   out_2805896999031237832[51] = 0;
   out_2805896999031237832[52] = 0;
   out_2805896999031237832[53] = 0;
}
void h_14(double *state, double *unused, double *out_7403982089292470191) {
   out_7403982089292470191[0] = state[6];
   out_7403982089292470191[1] = state[7];
   out_7403982089292470191[2] = state[8];
}
void H_14(double *state, double *unused, double *out_3556864030038389560) {
   out_3556864030038389560[0] = 0;
   out_3556864030038389560[1] = 0;
   out_3556864030038389560[2] = 0;
   out_3556864030038389560[3] = 0;
   out_3556864030038389560[4] = 0;
   out_3556864030038389560[5] = 0;
   out_3556864030038389560[6] = 1;
   out_3556864030038389560[7] = 0;
   out_3556864030038389560[8] = 0;
   out_3556864030038389560[9] = 0;
   out_3556864030038389560[10] = 0;
   out_3556864030038389560[11] = 0;
   out_3556864030038389560[12] = 0;
   out_3556864030038389560[13] = 0;
   out_3556864030038389560[14] = 0;
   out_3556864030038389560[15] = 0;
   out_3556864030038389560[16] = 0;
   out_3556864030038389560[17] = 0;
   out_3556864030038389560[18] = 0;
   out_3556864030038389560[19] = 0;
   out_3556864030038389560[20] = 0;
   out_3556864030038389560[21] = 0;
   out_3556864030038389560[22] = 0;
   out_3556864030038389560[23] = 0;
   out_3556864030038389560[24] = 0;
   out_3556864030038389560[25] = 1;
   out_3556864030038389560[26] = 0;
   out_3556864030038389560[27] = 0;
   out_3556864030038389560[28] = 0;
   out_3556864030038389560[29] = 0;
   out_3556864030038389560[30] = 0;
   out_3556864030038389560[31] = 0;
   out_3556864030038389560[32] = 0;
   out_3556864030038389560[33] = 0;
   out_3556864030038389560[34] = 0;
   out_3556864030038389560[35] = 0;
   out_3556864030038389560[36] = 0;
   out_3556864030038389560[37] = 0;
   out_3556864030038389560[38] = 0;
   out_3556864030038389560[39] = 0;
   out_3556864030038389560[40] = 0;
   out_3556864030038389560[41] = 0;
   out_3556864030038389560[42] = 0;
   out_3556864030038389560[43] = 0;
   out_3556864030038389560[44] = 1;
   out_3556864030038389560[45] = 0;
   out_3556864030038389560[46] = 0;
   out_3556864030038389560[47] = 0;
   out_3556864030038389560[48] = 0;
   out_3556864030038389560[49] = 0;
   out_3556864030038389560[50] = 0;
   out_3556864030038389560[51] = 0;
   out_3556864030038389560[52] = 0;
   out_3556864030038389560[53] = 0;
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

void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_4, H_4, NULL, in_z, in_R, in_ea, MAHA_THRESH_4);
}
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_10, H_10, NULL, in_z, in_R, in_ea, MAHA_THRESH_10);
}
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_13, H_13, NULL, in_z, in_R, in_ea, MAHA_THRESH_13);
}
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_14, H_14, NULL, in_z, in_R, in_ea, MAHA_THRESH_14);
}
void pose_err_fun(double *nom_x, double *delta_x, double *out_5541459369101084294) {
  err_fun(nom_x, delta_x, out_5541459369101084294);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_2205697697981872470) {
  inv_err_fun(nom_x, true_x, out_2205697697981872470);
}
void pose_H_mod_fun(double *state, double *out_5441704980450863752) {
  H_mod_fun(state, out_5441704980450863752);
}
void pose_f_fun(double *state, double dt, double *out_6977509595567259634) {
  f_fun(state,  dt, out_6977509595567259634);
}
void pose_F_fun(double *state, double dt, double *out_4929240761074066778) {
  F_fun(state,  dt, out_4929240761074066778);
}
void pose_h_4(double *state, double *unused, double *out_7829171151825984237) {
  h_4(state, unused, out_7829171151825984237);
}
void pose_H_4(double *state, double *unused, double *out_406376826301094969) {
  H_4(state, unused, out_406376826301094969);
}
void pose_h_10(double *state, double *unused, double *out_7608125297515821150) {
  h_10(state, unused, out_7608125297515821150);
}
void pose_H_10(double *state, double *unused, double *out_8432157119955175331) {
  H_10(state, unused, out_8432157119955175331);
}
void pose_h_13(double *state, double *unused, double *out_2187629780182442219) {
  h_13(state, unused, out_2187629780182442219);
}
void pose_H_13(double *state, double *unused, double *out_2805896999031237832) {
  H_13(state, unused, out_2805896999031237832);
}
void pose_h_14(double *state, double *unused, double *out_7403982089292470191) {
  h_14(state, unused, out_7403982089292470191);
}
void pose_H_14(double *state, double *unused, double *out_3556864030038389560) {
  H_14(state, unused, out_3556864030038389560);
}
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
}

const EKF pose = {
  .name = "pose",
  .kinds = { 4, 10, 13, 14 },
  .feature_kinds = {  },
  .f_fun = pose_f_fun,
  .F_fun = pose_F_fun,
  .err_fun = pose_err_fun,
  .inv_err_fun = pose_inv_err_fun,
  .H_mod_fun = pose_H_mod_fun,
  .predict = pose_predict,
  .hs = {
    { 4, pose_h_4 },
    { 10, pose_h_10 },
    { 13, pose_h_13 },
    { 14, pose_h_14 },
  },
  .Hs = {
    { 4, pose_H_4 },
    { 10, pose_H_10 },
    { 13, pose_H_13 },
    { 14, pose_H_14 },
  },
  .updates = {
    { 4, pose_update_4 },
    { 10, pose_update_10 },
    { 13, pose_update_13 },
    { 14, pose_update_14 },
  },
  .Hes = {
  },
  .sets = {
  },
  .extra_routines = {
  },
};

ekf_lib_init(pose)
