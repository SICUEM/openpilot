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
void err_fun(double *nom_x, double *delta_x, double *out_391600701176490780) {
   out_391600701176490780[0] = delta_x[0] + nom_x[0];
   out_391600701176490780[1] = delta_x[1] + nom_x[1];
   out_391600701176490780[2] = delta_x[2] + nom_x[2];
   out_391600701176490780[3] = delta_x[3] + nom_x[3];
   out_391600701176490780[4] = delta_x[4] + nom_x[4];
   out_391600701176490780[5] = delta_x[5] + nom_x[5];
   out_391600701176490780[6] = delta_x[6] + nom_x[6];
   out_391600701176490780[7] = delta_x[7] + nom_x[7];
   out_391600701176490780[8] = delta_x[8] + nom_x[8];
   out_391600701176490780[9] = delta_x[9] + nom_x[9];
   out_391600701176490780[10] = delta_x[10] + nom_x[10];
   out_391600701176490780[11] = delta_x[11] + nom_x[11];
   out_391600701176490780[12] = delta_x[12] + nom_x[12];
   out_391600701176490780[13] = delta_x[13] + nom_x[13];
   out_391600701176490780[14] = delta_x[14] + nom_x[14];
   out_391600701176490780[15] = delta_x[15] + nom_x[15];
   out_391600701176490780[16] = delta_x[16] + nom_x[16];
   out_391600701176490780[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_3374625416350243041) {
   out_3374625416350243041[0] = -nom_x[0] + true_x[0];
   out_3374625416350243041[1] = -nom_x[1] + true_x[1];
   out_3374625416350243041[2] = -nom_x[2] + true_x[2];
   out_3374625416350243041[3] = -nom_x[3] + true_x[3];
   out_3374625416350243041[4] = -nom_x[4] + true_x[4];
   out_3374625416350243041[5] = -nom_x[5] + true_x[5];
   out_3374625416350243041[6] = -nom_x[6] + true_x[6];
   out_3374625416350243041[7] = -nom_x[7] + true_x[7];
   out_3374625416350243041[8] = -nom_x[8] + true_x[8];
   out_3374625416350243041[9] = -nom_x[9] + true_x[9];
   out_3374625416350243041[10] = -nom_x[10] + true_x[10];
   out_3374625416350243041[11] = -nom_x[11] + true_x[11];
   out_3374625416350243041[12] = -nom_x[12] + true_x[12];
   out_3374625416350243041[13] = -nom_x[13] + true_x[13];
   out_3374625416350243041[14] = -nom_x[14] + true_x[14];
   out_3374625416350243041[15] = -nom_x[15] + true_x[15];
   out_3374625416350243041[16] = -nom_x[16] + true_x[16];
   out_3374625416350243041[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_2220345416541066761) {
   out_2220345416541066761[0] = 1.0;
   out_2220345416541066761[1] = 0.0;
   out_2220345416541066761[2] = 0.0;
   out_2220345416541066761[3] = 0.0;
   out_2220345416541066761[4] = 0.0;
   out_2220345416541066761[5] = 0.0;
   out_2220345416541066761[6] = 0.0;
   out_2220345416541066761[7] = 0.0;
   out_2220345416541066761[8] = 0.0;
   out_2220345416541066761[9] = 0.0;
   out_2220345416541066761[10] = 0.0;
   out_2220345416541066761[11] = 0.0;
   out_2220345416541066761[12] = 0.0;
   out_2220345416541066761[13] = 0.0;
   out_2220345416541066761[14] = 0.0;
   out_2220345416541066761[15] = 0.0;
   out_2220345416541066761[16] = 0.0;
   out_2220345416541066761[17] = 0.0;
   out_2220345416541066761[18] = 0.0;
   out_2220345416541066761[19] = 1.0;
   out_2220345416541066761[20] = 0.0;
   out_2220345416541066761[21] = 0.0;
   out_2220345416541066761[22] = 0.0;
   out_2220345416541066761[23] = 0.0;
   out_2220345416541066761[24] = 0.0;
   out_2220345416541066761[25] = 0.0;
   out_2220345416541066761[26] = 0.0;
   out_2220345416541066761[27] = 0.0;
   out_2220345416541066761[28] = 0.0;
   out_2220345416541066761[29] = 0.0;
   out_2220345416541066761[30] = 0.0;
   out_2220345416541066761[31] = 0.0;
   out_2220345416541066761[32] = 0.0;
   out_2220345416541066761[33] = 0.0;
   out_2220345416541066761[34] = 0.0;
   out_2220345416541066761[35] = 0.0;
   out_2220345416541066761[36] = 0.0;
   out_2220345416541066761[37] = 0.0;
   out_2220345416541066761[38] = 1.0;
   out_2220345416541066761[39] = 0.0;
   out_2220345416541066761[40] = 0.0;
   out_2220345416541066761[41] = 0.0;
   out_2220345416541066761[42] = 0.0;
   out_2220345416541066761[43] = 0.0;
   out_2220345416541066761[44] = 0.0;
   out_2220345416541066761[45] = 0.0;
   out_2220345416541066761[46] = 0.0;
   out_2220345416541066761[47] = 0.0;
   out_2220345416541066761[48] = 0.0;
   out_2220345416541066761[49] = 0.0;
   out_2220345416541066761[50] = 0.0;
   out_2220345416541066761[51] = 0.0;
   out_2220345416541066761[52] = 0.0;
   out_2220345416541066761[53] = 0.0;
   out_2220345416541066761[54] = 0.0;
   out_2220345416541066761[55] = 0.0;
   out_2220345416541066761[56] = 0.0;
   out_2220345416541066761[57] = 1.0;
   out_2220345416541066761[58] = 0.0;
   out_2220345416541066761[59] = 0.0;
   out_2220345416541066761[60] = 0.0;
   out_2220345416541066761[61] = 0.0;
   out_2220345416541066761[62] = 0.0;
   out_2220345416541066761[63] = 0.0;
   out_2220345416541066761[64] = 0.0;
   out_2220345416541066761[65] = 0.0;
   out_2220345416541066761[66] = 0.0;
   out_2220345416541066761[67] = 0.0;
   out_2220345416541066761[68] = 0.0;
   out_2220345416541066761[69] = 0.0;
   out_2220345416541066761[70] = 0.0;
   out_2220345416541066761[71] = 0.0;
   out_2220345416541066761[72] = 0.0;
   out_2220345416541066761[73] = 0.0;
   out_2220345416541066761[74] = 0.0;
   out_2220345416541066761[75] = 0.0;
   out_2220345416541066761[76] = 1.0;
   out_2220345416541066761[77] = 0.0;
   out_2220345416541066761[78] = 0.0;
   out_2220345416541066761[79] = 0.0;
   out_2220345416541066761[80] = 0.0;
   out_2220345416541066761[81] = 0.0;
   out_2220345416541066761[82] = 0.0;
   out_2220345416541066761[83] = 0.0;
   out_2220345416541066761[84] = 0.0;
   out_2220345416541066761[85] = 0.0;
   out_2220345416541066761[86] = 0.0;
   out_2220345416541066761[87] = 0.0;
   out_2220345416541066761[88] = 0.0;
   out_2220345416541066761[89] = 0.0;
   out_2220345416541066761[90] = 0.0;
   out_2220345416541066761[91] = 0.0;
   out_2220345416541066761[92] = 0.0;
   out_2220345416541066761[93] = 0.0;
   out_2220345416541066761[94] = 0.0;
   out_2220345416541066761[95] = 1.0;
   out_2220345416541066761[96] = 0.0;
   out_2220345416541066761[97] = 0.0;
   out_2220345416541066761[98] = 0.0;
   out_2220345416541066761[99] = 0.0;
   out_2220345416541066761[100] = 0.0;
   out_2220345416541066761[101] = 0.0;
   out_2220345416541066761[102] = 0.0;
   out_2220345416541066761[103] = 0.0;
   out_2220345416541066761[104] = 0.0;
   out_2220345416541066761[105] = 0.0;
   out_2220345416541066761[106] = 0.0;
   out_2220345416541066761[107] = 0.0;
   out_2220345416541066761[108] = 0.0;
   out_2220345416541066761[109] = 0.0;
   out_2220345416541066761[110] = 0.0;
   out_2220345416541066761[111] = 0.0;
   out_2220345416541066761[112] = 0.0;
   out_2220345416541066761[113] = 0.0;
   out_2220345416541066761[114] = 1.0;
   out_2220345416541066761[115] = 0.0;
   out_2220345416541066761[116] = 0.0;
   out_2220345416541066761[117] = 0.0;
   out_2220345416541066761[118] = 0.0;
   out_2220345416541066761[119] = 0.0;
   out_2220345416541066761[120] = 0.0;
   out_2220345416541066761[121] = 0.0;
   out_2220345416541066761[122] = 0.0;
   out_2220345416541066761[123] = 0.0;
   out_2220345416541066761[124] = 0.0;
   out_2220345416541066761[125] = 0.0;
   out_2220345416541066761[126] = 0.0;
   out_2220345416541066761[127] = 0.0;
   out_2220345416541066761[128] = 0.0;
   out_2220345416541066761[129] = 0.0;
   out_2220345416541066761[130] = 0.0;
   out_2220345416541066761[131] = 0.0;
   out_2220345416541066761[132] = 0.0;
   out_2220345416541066761[133] = 1.0;
   out_2220345416541066761[134] = 0.0;
   out_2220345416541066761[135] = 0.0;
   out_2220345416541066761[136] = 0.0;
   out_2220345416541066761[137] = 0.0;
   out_2220345416541066761[138] = 0.0;
   out_2220345416541066761[139] = 0.0;
   out_2220345416541066761[140] = 0.0;
   out_2220345416541066761[141] = 0.0;
   out_2220345416541066761[142] = 0.0;
   out_2220345416541066761[143] = 0.0;
   out_2220345416541066761[144] = 0.0;
   out_2220345416541066761[145] = 0.0;
   out_2220345416541066761[146] = 0.0;
   out_2220345416541066761[147] = 0.0;
   out_2220345416541066761[148] = 0.0;
   out_2220345416541066761[149] = 0.0;
   out_2220345416541066761[150] = 0.0;
   out_2220345416541066761[151] = 0.0;
   out_2220345416541066761[152] = 1.0;
   out_2220345416541066761[153] = 0.0;
   out_2220345416541066761[154] = 0.0;
   out_2220345416541066761[155] = 0.0;
   out_2220345416541066761[156] = 0.0;
   out_2220345416541066761[157] = 0.0;
   out_2220345416541066761[158] = 0.0;
   out_2220345416541066761[159] = 0.0;
   out_2220345416541066761[160] = 0.0;
   out_2220345416541066761[161] = 0.0;
   out_2220345416541066761[162] = 0.0;
   out_2220345416541066761[163] = 0.0;
   out_2220345416541066761[164] = 0.0;
   out_2220345416541066761[165] = 0.0;
   out_2220345416541066761[166] = 0.0;
   out_2220345416541066761[167] = 0.0;
   out_2220345416541066761[168] = 0.0;
   out_2220345416541066761[169] = 0.0;
   out_2220345416541066761[170] = 0.0;
   out_2220345416541066761[171] = 1.0;
   out_2220345416541066761[172] = 0.0;
   out_2220345416541066761[173] = 0.0;
   out_2220345416541066761[174] = 0.0;
   out_2220345416541066761[175] = 0.0;
   out_2220345416541066761[176] = 0.0;
   out_2220345416541066761[177] = 0.0;
   out_2220345416541066761[178] = 0.0;
   out_2220345416541066761[179] = 0.0;
   out_2220345416541066761[180] = 0.0;
   out_2220345416541066761[181] = 0.0;
   out_2220345416541066761[182] = 0.0;
   out_2220345416541066761[183] = 0.0;
   out_2220345416541066761[184] = 0.0;
   out_2220345416541066761[185] = 0.0;
   out_2220345416541066761[186] = 0.0;
   out_2220345416541066761[187] = 0.0;
   out_2220345416541066761[188] = 0.0;
   out_2220345416541066761[189] = 0.0;
   out_2220345416541066761[190] = 1.0;
   out_2220345416541066761[191] = 0.0;
   out_2220345416541066761[192] = 0.0;
   out_2220345416541066761[193] = 0.0;
   out_2220345416541066761[194] = 0.0;
   out_2220345416541066761[195] = 0.0;
   out_2220345416541066761[196] = 0.0;
   out_2220345416541066761[197] = 0.0;
   out_2220345416541066761[198] = 0.0;
   out_2220345416541066761[199] = 0.0;
   out_2220345416541066761[200] = 0.0;
   out_2220345416541066761[201] = 0.0;
   out_2220345416541066761[202] = 0.0;
   out_2220345416541066761[203] = 0.0;
   out_2220345416541066761[204] = 0.0;
   out_2220345416541066761[205] = 0.0;
   out_2220345416541066761[206] = 0.0;
   out_2220345416541066761[207] = 0.0;
   out_2220345416541066761[208] = 0.0;
   out_2220345416541066761[209] = 1.0;
   out_2220345416541066761[210] = 0.0;
   out_2220345416541066761[211] = 0.0;
   out_2220345416541066761[212] = 0.0;
   out_2220345416541066761[213] = 0.0;
   out_2220345416541066761[214] = 0.0;
   out_2220345416541066761[215] = 0.0;
   out_2220345416541066761[216] = 0.0;
   out_2220345416541066761[217] = 0.0;
   out_2220345416541066761[218] = 0.0;
   out_2220345416541066761[219] = 0.0;
   out_2220345416541066761[220] = 0.0;
   out_2220345416541066761[221] = 0.0;
   out_2220345416541066761[222] = 0.0;
   out_2220345416541066761[223] = 0.0;
   out_2220345416541066761[224] = 0.0;
   out_2220345416541066761[225] = 0.0;
   out_2220345416541066761[226] = 0.0;
   out_2220345416541066761[227] = 0.0;
   out_2220345416541066761[228] = 1.0;
   out_2220345416541066761[229] = 0.0;
   out_2220345416541066761[230] = 0.0;
   out_2220345416541066761[231] = 0.0;
   out_2220345416541066761[232] = 0.0;
   out_2220345416541066761[233] = 0.0;
   out_2220345416541066761[234] = 0.0;
   out_2220345416541066761[235] = 0.0;
   out_2220345416541066761[236] = 0.0;
   out_2220345416541066761[237] = 0.0;
   out_2220345416541066761[238] = 0.0;
   out_2220345416541066761[239] = 0.0;
   out_2220345416541066761[240] = 0.0;
   out_2220345416541066761[241] = 0.0;
   out_2220345416541066761[242] = 0.0;
   out_2220345416541066761[243] = 0.0;
   out_2220345416541066761[244] = 0.0;
   out_2220345416541066761[245] = 0.0;
   out_2220345416541066761[246] = 0.0;
   out_2220345416541066761[247] = 1.0;
   out_2220345416541066761[248] = 0.0;
   out_2220345416541066761[249] = 0.0;
   out_2220345416541066761[250] = 0.0;
   out_2220345416541066761[251] = 0.0;
   out_2220345416541066761[252] = 0.0;
   out_2220345416541066761[253] = 0.0;
   out_2220345416541066761[254] = 0.0;
   out_2220345416541066761[255] = 0.0;
   out_2220345416541066761[256] = 0.0;
   out_2220345416541066761[257] = 0.0;
   out_2220345416541066761[258] = 0.0;
   out_2220345416541066761[259] = 0.0;
   out_2220345416541066761[260] = 0.0;
   out_2220345416541066761[261] = 0.0;
   out_2220345416541066761[262] = 0.0;
   out_2220345416541066761[263] = 0.0;
   out_2220345416541066761[264] = 0.0;
   out_2220345416541066761[265] = 0.0;
   out_2220345416541066761[266] = 1.0;
   out_2220345416541066761[267] = 0.0;
   out_2220345416541066761[268] = 0.0;
   out_2220345416541066761[269] = 0.0;
   out_2220345416541066761[270] = 0.0;
   out_2220345416541066761[271] = 0.0;
   out_2220345416541066761[272] = 0.0;
   out_2220345416541066761[273] = 0.0;
   out_2220345416541066761[274] = 0.0;
   out_2220345416541066761[275] = 0.0;
   out_2220345416541066761[276] = 0.0;
   out_2220345416541066761[277] = 0.0;
   out_2220345416541066761[278] = 0.0;
   out_2220345416541066761[279] = 0.0;
   out_2220345416541066761[280] = 0.0;
   out_2220345416541066761[281] = 0.0;
   out_2220345416541066761[282] = 0.0;
   out_2220345416541066761[283] = 0.0;
   out_2220345416541066761[284] = 0.0;
   out_2220345416541066761[285] = 1.0;
   out_2220345416541066761[286] = 0.0;
   out_2220345416541066761[287] = 0.0;
   out_2220345416541066761[288] = 0.0;
   out_2220345416541066761[289] = 0.0;
   out_2220345416541066761[290] = 0.0;
   out_2220345416541066761[291] = 0.0;
   out_2220345416541066761[292] = 0.0;
   out_2220345416541066761[293] = 0.0;
   out_2220345416541066761[294] = 0.0;
   out_2220345416541066761[295] = 0.0;
   out_2220345416541066761[296] = 0.0;
   out_2220345416541066761[297] = 0.0;
   out_2220345416541066761[298] = 0.0;
   out_2220345416541066761[299] = 0.0;
   out_2220345416541066761[300] = 0.0;
   out_2220345416541066761[301] = 0.0;
   out_2220345416541066761[302] = 0.0;
   out_2220345416541066761[303] = 0.0;
   out_2220345416541066761[304] = 1.0;
   out_2220345416541066761[305] = 0.0;
   out_2220345416541066761[306] = 0.0;
   out_2220345416541066761[307] = 0.0;
   out_2220345416541066761[308] = 0.0;
   out_2220345416541066761[309] = 0.0;
   out_2220345416541066761[310] = 0.0;
   out_2220345416541066761[311] = 0.0;
   out_2220345416541066761[312] = 0.0;
   out_2220345416541066761[313] = 0.0;
   out_2220345416541066761[314] = 0.0;
   out_2220345416541066761[315] = 0.0;
   out_2220345416541066761[316] = 0.0;
   out_2220345416541066761[317] = 0.0;
   out_2220345416541066761[318] = 0.0;
   out_2220345416541066761[319] = 0.0;
   out_2220345416541066761[320] = 0.0;
   out_2220345416541066761[321] = 0.0;
   out_2220345416541066761[322] = 0.0;
   out_2220345416541066761[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_4446512712900270623) {
   out_4446512712900270623[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_4446512712900270623[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_4446512712900270623[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_4446512712900270623[3] = dt*state[12] + state[3];
   out_4446512712900270623[4] = dt*state[13] + state[4];
   out_4446512712900270623[5] = dt*state[14] + state[5];
   out_4446512712900270623[6] = state[6];
   out_4446512712900270623[7] = state[7];
   out_4446512712900270623[8] = state[8];
   out_4446512712900270623[9] = state[9];
   out_4446512712900270623[10] = state[10];
   out_4446512712900270623[11] = state[11];
   out_4446512712900270623[12] = state[12];
   out_4446512712900270623[13] = state[13];
   out_4446512712900270623[14] = state[14];
   out_4446512712900270623[15] = state[15];
   out_4446512712900270623[16] = state[16];
   out_4446512712900270623[17] = state[17];
}
void F_fun(double *state, double dt, double *out_1222015542029334518) {
   out_1222015542029334518[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1222015542029334518[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1222015542029334518[2] = 0;
   out_1222015542029334518[3] = 0;
   out_1222015542029334518[4] = 0;
   out_1222015542029334518[5] = 0;
   out_1222015542029334518[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1222015542029334518[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1222015542029334518[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1222015542029334518[9] = 0;
   out_1222015542029334518[10] = 0;
   out_1222015542029334518[11] = 0;
   out_1222015542029334518[12] = 0;
   out_1222015542029334518[13] = 0;
   out_1222015542029334518[14] = 0;
   out_1222015542029334518[15] = 0;
   out_1222015542029334518[16] = 0;
   out_1222015542029334518[17] = 0;
   out_1222015542029334518[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1222015542029334518[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1222015542029334518[20] = 0;
   out_1222015542029334518[21] = 0;
   out_1222015542029334518[22] = 0;
   out_1222015542029334518[23] = 0;
   out_1222015542029334518[24] = 0;
   out_1222015542029334518[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1222015542029334518[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1222015542029334518[27] = 0;
   out_1222015542029334518[28] = 0;
   out_1222015542029334518[29] = 0;
   out_1222015542029334518[30] = 0;
   out_1222015542029334518[31] = 0;
   out_1222015542029334518[32] = 0;
   out_1222015542029334518[33] = 0;
   out_1222015542029334518[34] = 0;
   out_1222015542029334518[35] = 0;
   out_1222015542029334518[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1222015542029334518[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1222015542029334518[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1222015542029334518[39] = 0;
   out_1222015542029334518[40] = 0;
   out_1222015542029334518[41] = 0;
   out_1222015542029334518[42] = 0;
   out_1222015542029334518[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1222015542029334518[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1222015542029334518[45] = 0;
   out_1222015542029334518[46] = 0;
   out_1222015542029334518[47] = 0;
   out_1222015542029334518[48] = 0;
   out_1222015542029334518[49] = 0;
   out_1222015542029334518[50] = 0;
   out_1222015542029334518[51] = 0;
   out_1222015542029334518[52] = 0;
   out_1222015542029334518[53] = 0;
   out_1222015542029334518[54] = 0;
   out_1222015542029334518[55] = 0;
   out_1222015542029334518[56] = 0;
   out_1222015542029334518[57] = 1;
   out_1222015542029334518[58] = 0;
   out_1222015542029334518[59] = 0;
   out_1222015542029334518[60] = 0;
   out_1222015542029334518[61] = 0;
   out_1222015542029334518[62] = 0;
   out_1222015542029334518[63] = 0;
   out_1222015542029334518[64] = 0;
   out_1222015542029334518[65] = 0;
   out_1222015542029334518[66] = dt;
   out_1222015542029334518[67] = 0;
   out_1222015542029334518[68] = 0;
   out_1222015542029334518[69] = 0;
   out_1222015542029334518[70] = 0;
   out_1222015542029334518[71] = 0;
   out_1222015542029334518[72] = 0;
   out_1222015542029334518[73] = 0;
   out_1222015542029334518[74] = 0;
   out_1222015542029334518[75] = 0;
   out_1222015542029334518[76] = 1;
   out_1222015542029334518[77] = 0;
   out_1222015542029334518[78] = 0;
   out_1222015542029334518[79] = 0;
   out_1222015542029334518[80] = 0;
   out_1222015542029334518[81] = 0;
   out_1222015542029334518[82] = 0;
   out_1222015542029334518[83] = 0;
   out_1222015542029334518[84] = 0;
   out_1222015542029334518[85] = dt;
   out_1222015542029334518[86] = 0;
   out_1222015542029334518[87] = 0;
   out_1222015542029334518[88] = 0;
   out_1222015542029334518[89] = 0;
   out_1222015542029334518[90] = 0;
   out_1222015542029334518[91] = 0;
   out_1222015542029334518[92] = 0;
   out_1222015542029334518[93] = 0;
   out_1222015542029334518[94] = 0;
   out_1222015542029334518[95] = 1;
   out_1222015542029334518[96] = 0;
   out_1222015542029334518[97] = 0;
   out_1222015542029334518[98] = 0;
   out_1222015542029334518[99] = 0;
   out_1222015542029334518[100] = 0;
   out_1222015542029334518[101] = 0;
   out_1222015542029334518[102] = 0;
   out_1222015542029334518[103] = 0;
   out_1222015542029334518[104] = dt;
   out_1222015542029334518[105] = 0;
   out_1222015542029334518[106] = 0;
   out_1222015542029334518[107] = 0;
   out_1222015542029334518[108] = 0;
   out_1222015542029334518[109] = 0;
   out_1222015542029334518[110] = 0;
   out_1222015542029334518[111] = 0;
   out_1222015542029334518[112] = 0;
   out_1222015542029334518[113] = 0;
   out_1222015542029334518[114] = 1;
   out_1222015542029334518[115] = 0;
   out_1222015542029334518[116] = 0;
   out_1222015542029334518[117] = 0;
   out_1222015542029334518[118] = 0;
   out_1222015542029334518[119] = 0;
   out_1222015542029334518[120] = 0;
   out_1222015542029334518[121] = 0;
   out_1222015542029334518[122] = 0;
   out_1222015542029334518[123] = 0;
   out_1222015542029334518[124] = 0;
   out_1222015542029334518[125] = 0;
   out_1222015542029334518[126] = 0;
   out_1222015542029334518[127] = 0;
   out_1222015542029334518[128] = 0;
   out_1222015542029334518[129] = 0;
   out_1222015542029334518[130] = 0;
   out_1222015542029334518[131] = 0;
   out_1222015542029334518[132] = 0;
   out_1222015542029334518[133] = 1;
   out_1222015542029334518[134] = 0;
   out_1222015542029334518[135] = 0;
   out_1222015542029334518[136] = 0;
   out_1222015542029334518[137] = 0;
   out_1222015542029334518[138] = 0;
   out_1222015542029334518[139] = 0;
   out_1222015542029334518[140] = 0;
   out_1222015542029334518[141] = 0;
   out_1222015542029334518[142] = 0;
   out_1222015542029334518[143] = 0;
   out_1222015542029334518[144] = 0;
   out_1222015542029334518[145] = 0;
   out_1222015542029334518[146] = 0;
   out_1222015542029334518[147] = 0;
   out_1222015542029334518[148] = 0;
   out_1222015542029334518[149] = 0;
   out_1222015542029334518[150] = 0;
   out_1222015542029334518[151] = 0;
   out_1222015542029334518[152] = 1;
   out_1222015542029334518[153] = 0;
   out_1222015542029334518[154] = 0;
   out_1222015542029334518[155] = 0;
   out_1222015542029334518[156] = 0;
   out_1222015542029334518[157] = 0;
   out_1222015542029334518[158] = 0;
   out_1222015542029334518[159] = 0;
   out_1222015542029334518[160] = 0;
   out_1222015542029334518[161] = 0;
   out_1222015542029334518[162] = 0;
   out_1222015542029334518[163] = 0;
   out_1222015542029334518[164] = 0;
   out_1222015542029334518[165] = 0;
   out_1222015542029334518[166] = 0;
   out_1222015542029334518[167] = 0;
   out_1222015542029334518[168] = 0;
   out_1222015542029334518[169] = 0;
   out_1222015542029334518[170] = 0;
   out_1222015542029334518[171] = 1;
   out_1222015542029334518[172] = 0;
   out_1222015542029334518[173] = 0;
   out_1222015542029334518[174] = 0;
   out_1222015542029334518[175] = 0;
   out_1222015542029334518[176] = 0;
   out_1222015542029334518[177] = 0;
   out_1222015542029334518[178] = 0;
   out_1222015542029334518[179] = 0;
   out_1222015542029334518[180] = 0;
   out_1222015542029334518[181] = 0;
   out_1222015542029334518[182] = 0;
   out_1222015542029334518[183] = 0;
   out_1222015542029334518[184] = 0;
   out_1222015542029334518[185] = 0;
   out_1222015542029334518[186] = 0;
   out_1222015542029334518[187] = 0;
   out_1222015542029334518[188] = 0;
   out_1222015542029334518[189] = 0;
   out_1222015542029334518[190] = 1;
   out_1222015542029334518[191] = 0;
   out_1222015542029334518[192] = 0;
   out_1222015542029334518[193] = 0;
   out_1222015542029334518[194] = 0;
   out_1222015542029334518[195] = 0;
   out_1222015542029334518[196] = 0;
   out_1222015542029334518[197] = 0;
   out_1222015542029334518[198] = 0;
   out_1222015542029334518[199] = 0;
   out_1222015542029334518[200] = 0;
   out_1222015542029334518[201] = 0;
   out_1222015542029334518[202] = 0;
   out_1222015542029334518[203] = 0;
   out_1222015542029334518[204] = 0;
   out_1222015542029334518[205] = 0;
   out_1222015542029334518[206] = 0;
   out_1222015542029334518[207] = 0;
   out_1222015542029334518[208] = 0;
   out_1222015542029334518[209] = 1;
   out_1222015542029334518[210] = 0;
   out_1222015542029334518[211] = 0;
   out_1222015542029334518[212] = 0;
   out_1222015542029334518[213] = 0;
   out_1222015542029334518[214] = 0;
   out_1222015542029334518[215] = 0;
   out_1222015542029334518[216] = 0;
   out_1222015542029334518[217] = 0;
   out_1222015542029334518[218] = 0;
   out_1222015542029334518[219] = 0;
   out_1222015542029334518[220] = 0;
   out_1222015542029334518[221] = 0;
   out_1222015542029334518[222] = 0;
   out_1222015542029334518[223] = 0;
   out_1222015542029334518[224] = 0;
   out_1222015542029334518[225] = 0;
   out_1222015542029334518[226] = 0;
   out_1222015542029334518[227] = 0;
   out_1222015542029334518[228] = 1;
   out_1222015542029334518[229] = 0;
   out_1222015542029334518[230] = 0;
   out_1222015542029334518[231] = 0;
   out_1222015542029334518[232] = 0;
   out_1222015542029334518[233] = 0;
   out_1222015542029334518[234] = 0;
   out_1222015542029334518[235] = 0;
   out_1222015542029334518[236] = 0;
   out_1222015542029334518[237] = 0;
   out_1222015542029334518[238] = 0;
   out_1222015542029334518[239] = 0;
   out_1222015542029334518[240] = 0;
   out_1222015542029334518[241] = 0;
   out_1222015542029334518[242] = 0;
   out_1222015542029334518[243] = 0;
   out_1222015542029334518[244] = 0;
   out_1222015542029334518[245] = 0;
   out_1222015542029334518[246] = 0;
   out_1222015542029334518[247] = 1;
   out_1222015542029334518[248] = 0;
   out_1222015542029334518[249] = 0;
   out_1222015542029334518[250] = 0;
   out_1222015542029334518[251] = 0;
   out_1222015542029334518[252] = 0;
   out_1222015542029334518[253] = 0;
   out_1222015542029334518[254] = 0;
   out_1222015542029334518[255] = 0;
   out_1222015542029334518[256] = 0;
   out_1222015542029334518[257] = 0;
   out_1222015542029334518[258] = 0;
   out_1222015542029334518[259] = 0;
   out_1222015542029334518[260] = 0;
   out_1222015542029334518[261] = 0;
   out_1222015542029334518[262] = 0;
   out_1222015542029334518[263] = 0;
   out_1222015542029334518[264] = 0;
   out_1222015542029334518[265] = 0;
   out_1222015542029334518[266] = 1;
   out_1222015542029334518[267] = 0;
   out_1222015542029334518[268] = 0;
   out_1222015542029334518[269] = 0;
   out_1222015542029334518[270] = 0;
   out_1222015542029334518[271] = 0;
   out_1222015542029334518[272] = 0;
   out_1222015542029334518[273] = 0;
   out_1222015542029334518[274] = 0;
   out_1222015542029334518[275] = 0;
   out_1222015542029334518[276] = 0;
   out_1222015542029334518[277] = 0;
   out_1222015542029334518[278] = 0;
   out_1222015542029334518[279] = 0;
   out_1222015542029334518[280] = 0;
   out_1222015542029334518[281] = 0;
   out_1222015542029334518[282] = 0;
   out_1222015542029334518[283] = 0;
   out_1222015542029334518[284] = 0;
   out_1222015542029334518[285] = 1;
   out_1222015542029334518[286] = 0;
   out_1222015542029334518[287] = 0;
   out_1222015542029334518[288] = 0;
   out_1222015542029334518[289] = 0;
   out_1222015542029334518[290] = 0;
   out_1222015542029334518[291] = 0;
   out_1222015542029334518[292] = 0;
   out_1222015542029334518[293] = 0;
   out_1222015542029334518[294] = 0;
   out_1222015542029334518[295] = 0;
   out_1222015542029334518[296] = 0;
   out_1222015542029334518[297] = 0;
   out_1222015542029334518[298] = 0;
   out_1222015542029334518[299] = 0;
   out_1222015542029334518[300] = 0;
   out_1222015542029334518[301] = 0;
   out_1222015542029334518[302] = 0;
   out_1222015542029334518[303] = 0;
   out_1222015542029334518[304] = 1;
   out_1222015542029334518[305] = 0;
   out_1222015542029334518[306] = 0;
   out_1222015542029334518[307] = 0;
   out_1222015542029334518[308] = 0;
   out_1222015542029334518[309] = 0;
   out_1222015542029334518[310] = 0;
   out_1222015542029334518[311] = 0;
   out_1222015542029334518[312] = 0;
   out_1222015542029334518[313] = 0;
   out_1222015542029334518[314] = 0;
   out_1222015542029334518[315] = 0;
   out_1222015542029334518[316] = 0;
   out_1222015542029334518[317] = 0;
   out_1222015542029334518[318] = 0;
   out_1222015542029334518[319] = 0;
   out_1222015542029334518[320] = 0;
   out_1222015542029334518[321] = 0;
   out_1222015542029334518[322] = 0;
   out_1222015542029334518[323] = 1;
}
void h_4(double *state, double *unused, double *out_8397249766321913444) {
   out_8397249766321913444[0] = state[6] + state[9];
   out_8397249766321913444[1] = state[7] + state[10];
   out_8397249766321913444[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_1053876662249882492) {
   out_1053876662249882492[0] = 0;
   out_1053876662249882492[1] = 0;
   out_1053876662249882492[2] = 0;
   out_1053876662249882492[3] = 0;
   out_1053876662249882492[4] = 0;
   out_1053876662249882492[5] = 0;
   out_1053876662249882492[6] = 1;
   out_1053876662249882492[7] = 0;
   out_1053876662249882492[8] = 0;
   out_1053876662249882492[9] = 1;
   out_1053876662249882492[10] = 0;
   out_1053876662249882492[11] = 0;
   out_1053876662249882492[12] = 0;
   out_1053876662249882492[13] = 0;
   out_1053876662249882492[14] = 0;
   out_1053876662249882492[15] = 0;
   out_1053876662249882492[16] = 0;
   out_1053876662249882492[17] = 0;
   out_1053876662249882492[18] = 0;
   out_1053876662249882492[19] = 0;
   out_1053876662249882492[20] = 0;
   out_1053876662249882492[21] = 0;
   out_1053876662249882492[22] = 0;
   out_1053876662249882492[23] = 0;
   out_1053876662249882492[24] = 0;
   out_1053876662249882492[25] = 1;
   out_1053876662249882492[26] = 0;
   out_1053876662249882492[27] = 0;
   out_1053876662249882492[28] = 1;
   out_1053876662249882492[29] = 0;
   out_1053876662249882492[30] = 0;
   out_1053876662249882492[31] = 0;
   out_1053876662249882492[32] = 0;
   out_1053876662249882492[33] = 0;
   out_1053876662249882492[34] = 0;
   out_1053876662249882492[35] = 0;
   out_1053876662249882492[36] = 0;
   out_1053876662249882492[37] = 0;
   out_1053876662249882492[38] = 0;
   out_1053876662249882492[39] = 0;
   out_1053876662249882492[40] = 0;
   out_1053876662249882492[41] = 0;
   out_1053876662249882492[42] = 0;
   out_1053876662249882492[43] = 0;
   out_1053876662249882492[44] = 1;
   out_1053876662249882492[45] = 0;
   out_1053876662249882492[46] = 0;
   out_1053876662249882492[47] = 1;
   out_1053876662249882492[48] = 0;
   out_1053876662249882492[49] = 0;
   out_1053876662249882492[50] = 0;
   out_1053876662249882492[51] = 0;
   out_1053876662249882492[52] = 0;
   out_1053876662249882492[53] = 0;
}
void h_10(double *state, double *unused, double *out_6226215451753727033) {
   out_6226215451753727033[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_6226215451753727033[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_6226215451753727033[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_6912769925911205854) {
   out_6912769925911205854[0] = 0;
   out_6912769925911205854[1] = 9.8100000000000005*cos(state[1]);
   out_6912769925911205854[2] = 0;
   out_6912769925911205854[3] = 0;
   out_6912769925911205854[4] = -state[8];
   out_6912769925911205854[5] = state[7];
   out_6912769925911205854[6] = 0;
   out_6912769925911205854[7] = state[5];
   out_6912769925911205854[8] = -state[4];
   out_6912769925911205854[9] = 0;
   out_6912769925911205854[10] = 0;
   out_6912769925911205854[11] = 0;
   out_6912769925911205854[12] = 1;
   out_6912769925911205854[13] = 0;
   out_6912769925911205854[14] = 0;
   out_6912769925911205854[15] = 1;
   out_6912769925911205854[16] = 0;
   out_6912769925911205854[17] = 0;
   out_6912769925911205854[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_6912769925911205854[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_6912769925911205854[20] = 0;
   out_6912769925911205854[21] = state[8];
   out_6912769925911205854[22] = 0;
   out_6912769925911205854[23] = -state[6];
   out_6912769925911205854[24] = -state[5];
   out_6912769925911205854[25] = 0;
   out_6912769925911205854[26] = state[3];
   out_6912769925911205854[27] = 0;
   out_6912769925911205854[28] = 0;
   out_6912769925911205854[29] = 0;
   out_6912769925911205854[30] = 0;
   out_6912769925911205854[31] = 1;
   out_6912769925911205854[32] = 0;
   out_6912769925911205854[33] = 0;
   out_6912769925911205854[34] = 1;
   out_6912769925911205854[35] = 0;
   out_6912769925911205854[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_6912769925911205854[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_6912769925911205854[38] = 0;
   out_6912769925911205854[39] = -state[7];
   out_6912769925911205854[40] = state[6];
   out_6912769925911205854[41] = 0;
   out_6912769925911205854[42] = state[4];
   out_6912769925911205854[43] = -state[3];
   out_6912769925911205854[44] = 0;
   out_6912769925911205854[45] = 0;
   out_6912769925911205854[46] = 0;
   out_6912769925911205854[47] = 0;
   out_6912769925911205854[48] = 0;
   out_6912769925911205854[49] = 0;
   out_6912769925911205854[50] = 1;
   out_6912769925911205854[51] = 0;
   out_6912769925911205854[52] = 0;
   out_6912769925911205854[53] = 1;
}
void h_13(double *state, double *unused, double *out_2707568773903906963) {
   out_2707568773903906963[0] = state[3];
   out_2707568773903906963[1] = state[4];
   out_2707568773903906963[2] = state[5];
}
void H_13(double *state, double *unused, double *out_6556754546066818437) {
   out_6556754546066818437[0] = 0;
   out_6556754546066818437[1] = 0;
   out_6556754546066818437[2] = 0;
   out_6556754546066818437[3] = 1;
   out_6556754546066818437[4] = 0;
   out_6556754546066818437[5] = 0;
   out_6556754546066818437[6] = 0;
   out_6556754546066818437[7] = 0;
   out_6556754546066818437[8] = 0;
   out_6556754546066818437[9] = 0;
   out_6556754546066818437[10] = 0;
   out_6556754546066818437[11] = 0;
   out_6556754546066818437[12] = 0;
   out_6556754546066818437[13] = 0;
   out_6556754546066818437[14] = 0;
   out_6556754546066818437[15] = 0;
   out_6556754546066818437[16] = 0;
   out_6556754546066818437[17] = 0;
   out_6556754546066818437[18] = 0;
   out_6556754546066818437[19] = 0;
   out_6556754546066818437[20] = 0;
   out_6556754546066818437[21] = 0;
   out_6556754546066818437[22] = 1;
   out_6556754546066818437[23] = 0;
   out_6556754546066818437[24] = 0;
   out_6556754546066818437[25] = 0;
   out_6556754546066818437[26] = 0;
   out_6556754546066818437[27] = 0;
   out_6556754546066818437[28] = 0;
   out_6556754546066818437[29] = 0;
   out_6556754546066818437[30] = 0;
   out_6556754546066818437[31] = 0;
   out_6556754546066818437[32] = 0;
   out_6556754546066818437[33] = 0;
   out_6556754546066818437[34] = 0;
   out_6556754546066818437[35] = 0;
   out_6556754546066818437[36] = 0;
   out_6556754546066818437[37] = 0;
   out_6556754546066818437[38] = 0;
   out_6556754546066818437[39] = 0;
   out_6556754546066818437[40] = 0;
   out_6556754546066818437[41] = 1;
   out_6556754546066818437[42] = 0;
   out_6556754546066818437[43] = 0;
   out_6556754546066818437[44] = 0;
   out_6556754546066818437[45] = 0;
   out_6556754546066818437[46] = 0;
   out_6556754546066818437[47] = 0;
   out_6556754546066818437[48] = 0;
   out_6556754546066818437[49] = 0;
   out_6556754546066818437[50] = 0;
   out_6556754546066818437[51] = 0;
   out_6556754546066818437[52] = 0;
   out_6556754546066818437[53] = 0;
}
void h_14(double *state, double *unused, double *out_1470448093605001330) {
   out_1470448093605001330[0] = state[6];
   out_1470448093605001330[1] = state[7];
   out_1470448093605001330[2] = state[8];
}
void H_14(double *state, double *unused, double *out_2909364194089602037) {
   out_2909364194089602037[0] = 0;
   out_2909364194089602037[1] = 0;
   out_2909364194089602037[2] = 0;
   out_2909364194089602037[3] = 0;
   out_2909364194089602037[4] = 0;
   out_2909364194089602037[5] = 0;
   out_2909364194089602037[6] = 1;
   out_2909364194089602037[7] = 0;
   out_2909364194089602037[8] = 0;
   out_2909364194089602037[9] = 0;
   out_2909364194089602037[10] = 0;
   out_2909364194089602037[11] = 0;
   out_2909364194089602037[12] = 0;
   out_2909364194089602037[13] = 0;
   out_2909364194089602037[14] = 0;
   out_2909364194089602037[15] = 0;
   out_2909364194089602037[16] = 0;
   out_2909364194089602037[17] = 0;
   out_2909364194089602037[18] = 0;
   out_2909364194089602037[19] = 0;
   out_2909364194089602037[20] = 0;
   out_2909364194089602037[21] = 0;
   out_2909364194089602037[22] = 0;
   out_2909364194089602037[23] = 0;
   out_2909364194089602037[24] = 0;
   out_2909364194089602037[25] = 1;
   out_2909364194089602037[26] = 0;
   out_2909364194089602037[27] = 0;
   out_2909364194089602037[28] = 0;
   out_2909364194089602037[29] = 0;
   out_2909364194089602037[30] = 0;
   out_2909364194089602037[31] = 0;
   out_2909364194089602037[32] = 0;
   out_2909364194089602037[33] = 0;
   out_2909364194089602037[34] = 0;
   out_2909364194089602037[35] = 0;
   out_2909364194089602037[36] = 0;
   out_2909364194089602037[37] = 0;
   out_2909364194089602037[38] = 0;
   out_2909364194089602037[39] = 0;
   out_2909364194089602037[40] = 0;
   out_2909364194089602037[41] = 0;
   out_2909364194089602037[42] = 0;
   out_2909364194089602037[43] = 0;
   out_2909364194089602037[44] = 1;
   out_2909364194089602037[45] = 0;
   out_2909364194089602037[46] = 0;
   out_2909364194089602037[47] = 0;
   out_2909364194089602037[48] = 0;
   out_2909364194089602037[49] = 0;
   out_2909364194089602037[50] = 0;
   out_2909364194089602037[51] = 0;
   out_2909364194089602037[52] = 0;
   out_2909364194089602037[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_391600701176490780) {
  err_fun(nom_x, delta_x, out_391600701176490780);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_3374625416350243041) {
  inv_err_fun(nom_x, true_x, out_3374625416350243041);
}
void pose_H_mod_fun(double *state, double *out_2220345416541066761) {
  H_mod_fun(state, out_2220345416541066761);
}
void pose_f_fun(double *state, double dt, double *out_4446512712900270623) {
  f_fun(state,  dt, out_4446512712900270623);
}
void pose_F_fun(double *state, double dt, double *out_1222015542029334518) {
  F_fun(state,  dt, out_1222015542029334518);
}
void pose_h_4(double *state, double *unused, double *out_8397249766321913444) {
  h_4(state, unused, out_8397249766321913444);
}
void pose_H_4(double *state, double *unused, double *out_1053876662249882492) {
  H_4(state, unused, out_1053876662249882492);
}
void pose_h_10(double *state, double *unused, double *out_6226215451753727033) {
  h_10(state, unused, out_6226215451753727033);
}
void pose_H_10(double *state, double *unused, double *out_6912769925911205854) {
  H_10(state, unused, out_6912769925911205854);
}
void pose_h_13(double *state, double *unused, double *out_2707568773903906963) {
  h_13(state, unused, out_2707568773903906963);
}
void pose_H_13(double *state, double *unused, double *out_6556754546066818437) {
  H_13(state, unused, out_6556754546066818437);
}
void pose_h_14(double *state, double *unused, double *out_1470448093605001330) {
  h_14(state, unused, out_1470448093605001330);
}
void pose_H_14(double *state, double *unused, double *out_2909364194089602037) {
  H_14(state, unused, out_2909364194089602037);
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
