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
void err_fun(double *nom_x, double *delta_x, double *out_7576548165016352808) {
   out_7576548165016352808[0] = delta_x[0] + nom_x[0];
   out_7576548165016352808[1] = delta_x[1] + nom_x[1];
   out_7576548165016352808[2] = delta_x[2] + nom_x[2];
   out_7576548165016352808[3] = delta_x[3] + nom_x[3];
   out_7576548165016352808[4] = delta_x[4] + nom_x[4];
   out_7576548165016352808[5] = delta_x[5] + nom_x[5];
   out_7576548165016352808[6] = delta_x[6] + nom_x[6];
   out_7576548165016352808[7] = delta_x[7] + nom_x[7];
   out_7576548165016352808[8] = delta_x[8] + nom_x[8];
   out_7576548165016352808[9] = delta_x[9] + nom_x[9];
   out_7576548165016352808[10] = delta_x[10] + nom_x[10];
   out_7576548165016352808[11] = delta_x[11] + nom_x[11];
   out_7576548165016352808[12] = delta_x[12] + nom_x[12];
   out_7576548165016352808[13] = delta_x[13] + nom_x[13];
   out_7576548165016352808[14] = delta_x[14] + nom_x[14];
   out_7576548165016352808[15] = delta_x[15] + nom_x[15];
   out_7576548165016352808[16] = delta_x[16] + nom_x[16];
   out_7576548165016352808[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_3269481700032691791) {
   out_3269481700032691791[0] = -nom_x[0] + true_x[0];
   out_3269481700032691791[1] = -nom_x[1] + true_x[1];
   out_3269481700032691791[2] = -nom_x[2] + true_x[2];
   out_3269481700032691791[3] = -nom_x[3] + true_x[3];
   out_3269481700032691791[4] = -nom_x[4] + true_x[4];
   out_3269481700032691791[5] = -nom_x[5] + true_x[5];
   out_3269481700032691791[6] = -nom_x[6] + true_x[6];
   out_3269481700032691791[7] = -nom_x[7] + true_x[7];
   out_3269481700032691791[8] = -nom_x[8] + true_x[8];
   out_3269481700032691791[9] = -nom_x[9] + true_x[9];
   out_3269481700032691791[10] = -nom_x[10] + true_x[10];
   out_3269481700032691791[11] = -nom_x[11] + true_x[11];
   out_3269481700032691791[12] = -nom_x[12] + true_x[12];
   out_3269481700032691791[13] = -nom_x[13] + true_x[13];
   out_3269481700032691791[14] = -nom_x[14] + true_x[14];
   out_3269481700032691791[15] = -nom_x[15] + true_x[15];
   out_3269481700032691791[16] = -nom_x[16] + true_x[16];
   out_3269481700032691791[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_3135696547169702091) {
   out_3135696547169702091[0] = 1.0;
   out_3135696547169702091[1] = 0.0;
   out_3135696547169702091[2] = 0.0;
   out_3135696547169702091[3] = 0.0;
   out_3135696547169702091[4] = 0.0;
   out_3135696547169702091[5] = 0.0;
   out_3135696547169702091[6] = 0.0;
   out_3135696547169702091[7] = 0.0;
   out_3135696547169702091[8] = 0.0;
   out_3135696547169702091[9] = 0.0;
   out_3135696547169702091[10] = 0.0;
   out_3135696547169702091[11] = 0.0;
   out_3135696547169702091[12] = 0.0;
   out_3135696547169702091[13] = 0.0;
   out_3135696547169702091[14] = 0.0;
   out_3135696547169702091[15] = 0.0;
   out_3135696547169702091[16] = 0.0;
   out_3135696547169702091[17] = 0.0;
   out_3135696547169702091[18] = 0.0;
   out_3135696547169702091[19] = 1.0;
   out_3135696547169702091[20] = 0.0;
   out_3135696547169702091[21] = 0.0;
   out_3135696547169702091[22] = 0.0;
   out_3135696547169702091[23] = 0.0;
   out_3135696547169702091[24] = 0.0;
   out_3135696547169702091[25] = 0.0;
   out_3135696547169702091[26] = 0.0;
   out_3135696547169702091[27] = 0.0;
   out_3135696547169702091[28] = 0.0;
   out_3135696547169702091[29] = 0.0;
   out_3135696547169702091[30] = 0.0;
   out_3135696547169702091[31] = 0.0;
   out_3135696547169702091[32] = 0.0;
   out_3135696547169702091[33] = 0.0;
   out_3135696547169702091[34] = 0.0;
   out_3135696547169702091[35] = 0.0;
   out_3135696547169702091[36] = 0.0;
   out_3135696547169702091[37] = 0.0;
   out_3135696547169702091[38] = 1.0;
   out_3135696547169702091[39] = 0.0;
   out_3135696547169702091[40] = 0.0;
   out_3135696547169702091[41] = 0.0;
   out_3135696547169702091[42] = 0.0;
   out_3135696547169702091[43] = 0.0;
   out_3135696547169702091[44] = 0.0;
   out_3135696547169702091[45] = 0.0;
   out_3135696547169702091[46] = 0.0;
   out_3135696547169702091[47] = 0.0;
   out_3135696547169702091[48] = 0.0;
   out_3135696547169702091[49] = 0.0;
   out_3135696547169702091[50] = 0.0;
   out_3135696547169702091[51] = 0.0;
   out_3135696547169702091[52] = 0.0;
   out_3135696547169702091[53] = 0.0;
   out_3135696547169702091[54] = 0.0;
   out_3135696547169702091[55] = 0.0;
   out_3135696547169702091[56] = 0.0;
   out_3135696547169702091[57] = 1.0;
   out_3135696547169702091[58] = 0.0;
   out_3135696547169702091[59] = 0.0;
   out_3135696547169702091[60] = 0.0;
   out_3135696547169702091[61] = 0.0;
   out_3135696547169702091[62] = 0.0;
   out_3135696547169702091[63] = 0.0;
   out_3135696547169702091[64] = 0.0;
   out_3135696547169702091[65] = 0.0;
   out_3135696547169702091[66] = 0.0;
   out_3135696547169702091[67] = 0.0;
   out_3135696547169702091[68] = 0.0;
   out_3135696547169702091[69] = 0.0;
   out_3135696547169702091[70] = 0.0;
   out_3135696547169702091[71] = 0.0;
   out_3135696547169702091[72] = 0.0;
   out_3135696547169702091[73] = 0.0;
   out_3135696547169702091[74] = 0.0;
   out_3135696547169702091[75] = 0.0;
   out_3135696547169702091[76] = 1.0;
   out_3135696547169702091[77] = 0.0;
   out_3135696547169702091[78] = 0.0;
   out_3135696547169702091[79] = 0.0;
   out_3135696547169702091[80] = 0.0;
   out_3135696547169702091[81] = 0.0;
   out_3135696547169702091[82] = 0.0;
   out_3135696547169702091[83] = 0.0;
   out_3135696547169702091[84] = 0.0;
   out_3135696547169702091[85] = 0.0;
   out_3135696547169702091[86] = 0.0;
   out_3135696547169702091[87] = 0.0;
   out_3135696547169702091[88] = 0.0;
   out_3135696547169702091[89] = 0.0;
   out_3135696547169702091[90] = 0.0;
   out_3135696547169702091[91] = 0.0;
   out_3135696547169702091[92] = 0.0;
   out_3135696547169702091[93] = 0.0;
   out_3135696547169702091[94] = 0.0;
   out_3135696547169702091[95] = 1.0;
   out_3135696547169702091[96] = 0.0;
   out_3135696547169702091[97] = 0.0;
   out_3135696547169702091[98] = 0.0;
   out_3135696547169702091[99] = 0.0;
   out_3135696547169702091[100] = 0.0;
   out_3135696547169702091[101] = 0.0;
   out_3135696547169702091[102] = 0.0;
   out_3135696547169702091[103] = 0.0;
   out_3135696547169702091[104] = 0.0;
   out_3135696547169702091[105] = 0.0;
   out_3135696547169702091[106] = 0.0;
   out_3135696547169702091[107] = 0.0;
   out_3135696547169702091[108] = 0.0;
   out_3135696547169702091[109] = 0.0;
   out_3135696547169702091[110] = 0.0;
   out_3135696547169702091[111] = 0.0;
   out_3135696547169702091[112] = 0.0;
   out_3135696547169702091[113] = 0.0;
   out_3135696547169702091[114] = 1.0;
   out_3135696547169702091[115] = 0.0;
   out_3135696547169702091[116] = 0.0;
   out_3135696547169702091[117] = 0.0;
   out_3135696547169702091[118] = 0.0;
   out_3135696547169702091[119] = 0.0;
   out_3135696547169702091[120] = 0.0;
   out_3135696547169702091[121] = 0.0;
   out_3135696547169702091[122] = 0.0;
   out_3135696547169702091[123] = 0.0;
   out_3135696547169702091[124] = 0.0;
   out_3135696547169702091[125] = 0.0;
   out_3135696547169702091[126] = 0.0;
   out_3135696547169702091[127] = 0.0;
   out_3135696547169702091[128] = 0.0;
   out_3135696547169702091[129] = 0.0;
   out_3135696547169702091[130] = 0.0;
   out_3135696547169702091[131] = 0.0;
   out_3135696547169702091[132] = 0.0;
   out_3135696547169702091[133] = 1.0;
   out_3135696547169702091[134] = 0.0;
   out_3135696547169702091[135] = 0.0;
   out_3135696547169702091[136] = 0.0;
   out_3135696547169702091[137] = 0.0;
   out_3135696547169702091[138] = 0.0;
   out_3135696547169702091[139] = 0.0;
   out_3135696547169702091[140] = 0.0;
   out_3135696547169702091[141] = 0.0;
   out_3135696547169702091[142] = 0.0;
   out_3135696547169702091[143] = 0.0;
   out_3135696547169702091[144] = 0.0;
   out_3135696547169702091[145] = 0.0;
   out_3135696547169702091[146] = 0.0;
   out_3135696547169702091[147] = 0.0;
   out_3135696547169702091[148] = 0.0;
   out_3135696547169702091[149] = 0.0;
   out_3135696547169702091[150] = 0.0;
   out_3135696547169702091[151] = 0.0;
   out_3135696547169702091[152] = 1.0;
   out_3135696547169702091[153] = 0.0;
   out_3135696547169702091[154] = 0.0;
   out_3135696547169702091[155] = 0.0;
   out_3135696547169702091[156] = 0.0;
   out_3135696547169702091[157] = 0.0;
   out_3135696547169702091[158] = 0.0;
   out_3135696547169702091[159] = 0.0;
   out_3135696547169702091[160] = 0.0;
   out_3135696547169702091[161] = 0.0;
   out_3135696547169702091[162] = 0.0;
   out_3135696547169702091[163] = 0.0;
   out_3135696547169702091[164] = 0.0;
   out_3135696547169702091[165] = 0.0;
   out_3135696547169702091[166] = 0.0;
   out_3135696547169702091[167] = 0.0;
   out_3135696547169702091[168] = 0.0;
   out_3135696547169702091[169] = 0.0;
   out_3135696547169702091[170] = 0.0;
   out_3135696547169702091[171] = 1.0;
   out_3135696547169702091[172] = 0.0;
   out_3135696547169702091[173] = 0.0;
   out_3135696547169702091[174] = 0.0;
   out_3135696547169702091[175] = 0.0;
   out_3135696547169702091[176] = 0.0;
   out_3135696547169702091[177] = 0.0;
   out_3135696547169702091[178] = 0.0;
   out_3135696547169702091[179] = 0.0;
   out_3135696547169702091[180] = 0.0;
   out_3135696547169702091[181] = 0.0;
   out_3135696547169702091[182] = 0.0;
   out_3135696547169702091[183] = 0.0;
   out_3135696547169702091[184] = 0.0;
   out_3135696547169702091[185] = 0.0;
   out_3135696547169702091[186] = 0.0;
   out_3135696547169702091[187] = 0.0;
   out_3135696547169702091[188] = 0.0;
   out_3135696547169702091[189] = 0.0;
   out_3135696547169702091[190] = 1.0;
   out_3135696547169702091[191] = 0.0;
   out_3135696547169702091[192] = 0.0;
   out_3135696547169702091[193] = 0.0;
   out_3135696547169702091[194] = 0.0;
   out_3135696547169702091[195] = 0.0;
   out_3135696547169702091[196] = 0.0;
   out_3135696547169702091[197] = 0.0;
   out_3135696547169702091[198] = 0.0;
   out_3135696547169702091[199] = 0.0;
   out_3135696547169702091[200] = 0.0;
   out_3135696547169702091[201] = 0.0;
   out_3135696547169702091[202] = 0.0;
   out_3135696547169702091[203] = 0.0;
   out_3135696547169702091[204] = 0.0;
   out_3135696547169702091[205] = 0.0;
   out_3135696547169702091[206] = 0.0;
   out_3135696547169702091[207] = 0.0;
   out_3135696547169702091[208] = 0.0;
   out_3135696547169702091[209] = 1.0;
   out_3135696547169702091[210] = 0.0;
   out_3135696547169702091[211] = 0.0;
   out_3135696547169702091[212] = 0.0;
   out_3135696547169702091[213] = 0.0;
   out_3135696547169702091[214] = 0.0;
   out_3135696547169702091[215] = 0.0;
   out_3135696547169702091[216] = 0.0;
   out_3135696547169702091[217] = 0.0;
   out_3135696547169702091[218] = 0.0;
   out_3135696547169702091[219] = 0.0;
   out_3135696547169702091[220] = 0.0;
   out_3135696547169702091[221] = 0.0;
   out_3135696547169702091[222] = 0.0;
   out_3135696547169702091[223] = 0.0;
   out_3135696547169702091[224] = 0.0;
   out_3135696547169702091[225] = 0.0;
   out_3135696547169702091[226] = 0.0;
   out_3135696547169702091[227] = 0.0;
   out_3135696547169702091[228] = 1.0;
   out_3135696547169702091[229] = 0.0;
   out_3135696547169702091[230] = 0.0;
   out_3135696547169702091[231] = 0.0;
   out_3135696547169702091[232] = 0.0;
   out_3135696547169702091[233] = 0.0;
   out_3135696547169702091[234] = 0.0;
   out_3135696547169702091[235] = 0.0;
   out_3135696547169702091[236] = 0.0;
   out_3135696547169702091[237] = 0.0;
   out_3135696547169702091[238] = 0.0;
   out_3135696547169702091[239] = 0.0;
   out_3135696547169702091[240] = 0.0;
   out_3135696547169702091[241] = 0.0;
   out_3135696547169702091[242] = 0.0;
   out_3135696547169702091[243] = 0.0;
   out_3135696547169702091[244] = 0.0;
   out_3135696547169702091[245] = 0.0;
   out_3135696547169702091[246] = 0.0;
   out_3135696547169702091[247] = 1.0;
   out_3135696547169702091[248] = 0.0;
   out_3135696547169702091[249] = 0.0;
   out_3135696547169702091[250] = 0.0;
   out_3135696547169702091[251] = 0.0;
   out_3135696547169702091[252] = 0.0;
   out_3135696547169702091[253] = 0.0;
   out_3135696547169702091[254] = 0.0;
   out_3135696547169702091[255] = 0.0;
   out_3135696547169702091[256] = 0.0;
   out_3135696547169702091[257] = 0.0;
   out_3135696547169702091[258] = 0.0;
   out_3135696547169702091[259] = 0.0;
   out_3135696547169702091[260] = 0.0;
   out_3135696547169702091[261] = 0.0;
   out_3135696547169702091[262] = 0.0;
   out_3135696547169702091[263] = 0.0;
   out_3135696547169702091[264] = 0.0;
   out_3135696547169702091[265] = 0.0;
   out_3135696547169702091[266] = 1.0;
   out_3135696547169702091[267] = 0.0;
   out_3135696547169702091[268] = 0.0;
   out_3135696547169702091[269] = 0.0;
   out_3135696547169702091[270] = 0.0;
   out_3135696547169702091[271] = 0.0;
   out_3135696547169702091[272] = 0.0;
   out_3135696547169702091[273] = 0.0;
   out_3135696547169702091[274] = 0.0;
   out_3135696547169702091[275] = 0.0;
   out_3135696547169702091[276] = 0.0;
   out_3135696547169702091[277] = 0.0;
   out_3135696547169702091[278] = 0.0;
   out_3135696547169702091[279] = 0.0;
   out_3135696547169702091[280] = 0.0;
   out_3135696547169702091[281] = 0.0;
   out_3135696547169702091[282] = 0.0;
   out_3135696547169702091[283] = 0.0;
   out_3135696547169702091[284] = 0.0;
   out_3135696547169702091[285] = 1.0;
   out_3135696547169702091[286] = 0.0;
   out_3135696547169702091[287] = 0.0;
   out_3135696547169702091[288] = 0.0;
   out_3135696547169702091[289] = 0.0;
   out_3135696547169702091[290] = 0.0;
   out_3135696547169702091[291] = 0.0;
   out_3135696547169702091[292] = 0.0;
   out_3135696547169702091[293] = 0.0;
   out_3135696547169702091[294] = 0.0;
   out_3135696547169702091[295] = 0.0;
   out_3135696547169702091[296] = 0.0;
   out_3135696547169702091[297] = 0.0;
   out_3135696547169702091[298] = 0.0;
   out_3135696547169702091[299] = 0.0;
   out_3135696547169702091[300] = 0.0;
   out_3135696547169702091[301] = 0.0;
   out_3135696547169702091[302] = 0.0;
   out_3135696547169702091[303] = 0.0;
   out_3135696547169702091[304] = 1.0;
   out_3135696547169702091[305] = 0.0;
   out_3135696547169702091[306] = 0.0;
   out_3135696547169702091[307] = 0.0;
   out_3135696547169702091[308] = 0.0;
   out_3135696547169702091[309] = 0.0;
   out_3135696547169702091[310] = 0.0;
   out_3135696547169702091[311] = 0.0;
   out_3135696547169702091[312] = 0.0;
   out_3135696547169702091[313] = 0.0;
   out_3135696547169702091[314] = 0.0;
   out_3135696547169702091[315] = 0.0;
   out_3135696547169702091[316] = 0.0;
   out_3135696547169702091[317] = 0.0;
   out_3135696547169702091[318] = 0.0;
   out_3135696547169702091[319] = 0.0;
   out_3135696547169702091[320] = 0.0;
   out_3135696547169702091[321] = 0.0;
   out_3135696547169702091[322] = 0.0;
   out_3135696547169702091[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_2367158378490033196) {
   out_2367158378490033196[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_2367158378490033196[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_2367158378490033196[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_2367158378490033196[3] = dt*state[12] + state[3];
   out_2367158378490033196[4] = dt*state[13] + state[4];
   out_2367158378490033196[5] = dt*state[14] + state[5];
   out_2367158378490033196[6] = state[6];
   out_2367158378490033196[7] = state[7];
   out_2367158378490033196[8] = state[8];
   out_2367158378490033196[9] = state[9];
   out_2367158378490033196[10] = state[10];
   out_2367158378490033196[11] = state[11];
   out_2367158378490033196[12] = state[12];
   out_2367158378490033196[13] = state[13];
   out_2367158378490033196[14] = state[14];
   out_2367158378490033196[15] = state[15];
   out_2367158378490033196[16] = state[16];
   out_2367158378490033196[17] = state[17];
}
void F_fun(double *state, double dt, double *out_6441421400486242095) {
   out_6441421400486242095[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_6441421400486242095[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_6441421400486242095[2] = 0;
   out_6441421400486242095[3] = 0;
   out_6441421400486242095[4] = 0;
   out_6441421400486242095[5] = 0;
   out_6441421400486242095[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_6441421400486242095[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_6441421400486242095[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_6441421400486242095[9] = 0;
   out_6441421400486242095[10] = 0;
   out_6441421400486242095[11] = 0;
   out_6441421400486242095[12] = 0;
   out_6441421400486242095[13] = 0;
   out_6441421400486242095[14] = 0;
   out_6441421400486242095[15] = 0;
   out_6441421400486242095[16] = 0;
   out_6441421400486242095[17] = 0;
   out_6441421400486242095[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_6441421400486242095[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_6441421400486242095[20] = 0;
   out_6441421400486242095[21] = 0;
   out_6441421400486242095[22] = 0;
   out_6441421400486242095[23] = 0;
   out_6441421400486242095[24] = 0;
   out_6441421400486242095[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_6441421400486242095[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_6441421400486242095[27] = 0;
   out_6441421400486242095[28] = 0;
   out_6441421400486242095[29] = 0;
   out_6441421400486242095[30] = 0;
   out_6441421400486242095[31] = 0;
   out_6441421400486242095[32] = 0;
   out_6441421400486242095[33] = 0;
   out_6441421400486242095[34] = 0;
   out_6441421400486242095[35] = 0;
   out_6441421400486242095[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_6441421400486242095[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_6441421400486242095[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_6441421400486242095[39] = 0;
   out_6441421400486242095[40] = 0;
   out_6441421400486242095[41] = 0;
   out_6441421400486242095[42] = 0;
   out_6441421400486242095[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_6441421400486242095[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_6441421400486242095[45] = 0;
   out_6441421400486242095[46] = 0;
   out_6441421400486242095[47] = 0;
   out_6441421400486242095[48] = 0;
   out_6441421400486242095[49] = 0;
   out_6441421400486242095[50] = 0;
   out_6441421400486242095[51] = 0;
   out_6441421400486242095[52] = 0;
   out_6441421400486242095[53] = 0;
   out_6441421400486242095[54] = 0;
   out_6441421400486242095[55] = 0;
   out_6441421400486242095[56] = 0;
   out_6441421400486242095[57] = 1;
   out_6441421400486242095[58] = 0;
   out_6441421400486242095[59] = 0;
   out_6441421400486242095[60] = 0;
   out_6441421400486242095[61] = 0;
   out_6441421400486242095[62] = 0;
   out_6441421400486242095[63] = 0;
   out_6441421400486242095[64] = 0;
   out_6441421400486242095[65] = 0;
   out_6441421400486242095[66] = dt;
   out_6441421400486242095[67] = 0;
   out_6441421400486242095[68] = 0;
   out_6441421400486242095[69] = 0;
   out_6441421400486242095[70] = 0;
   out_6441421400486242095[71] = 0;
   out_6441421400486242095[72] = 0;
   out_6441421400486242095[73] = 0;
   out_6441421400486242095[74] = 0;
   out_6441421400486242095[75] = 0;
   out_6441421400486242095[76] = 1;
   out_6441421400486242095[77] = 0;
   out_6441421400486242095[78] = 0;
   out_6441421400486242095[79] = 0;
   out_6441421400486242095[80] = 0;
   out_6441421400486242095[81] = 0;
   out_6441421400486242095[82] = 0;
   out_6441421400486242095[83] = 0;
   out_6441421400486242095[84] = 0;
   out_6441421400486242095[85] = dt;
   out_6441421400486242095[86] = 0;
   out_6441421400486242095[87] = 0;
   out_6441421400486242095[88] = 0;
   out_6441421400486242095[89] = 0;
   out_6441421400486242095[90] = 0;
   out_6441421400486242095[91] = 0;
   out_6441421400486242095[92] = 0;
   out_6441421400486242095[93] = 0;
   out_6441421400486242095[94] = 0;
   out_6441421400486242095[95] = 1;
   out_6441421400486242095[96] = 0;
   out_6441421400486242095[97] = 0;
   out_6441421400486242095[98] = 0;
   out_6441421400486242095[99] = 0;
   out_6441421400486242095[100] = 0;
   out_6441421400486242095[101] = 0;
   out_6441421400486242095[102] = 0;
   out_6441421400486242095[103] = 0;
   out_6441421400486242095[104] = dt;
   out_6441421400486242095[105] = 0;
   out_6441421400486242095[106] = 0;
   out_6441421400486242095[107] = 0;
   out_6441421400486242095[108] = 0;
   out_6441421400486242095[109] = 0;
   out_6441421400486242095[110] = 0;
   out_6441421400486242095[111] = 0;
   out_6441421400486242095[112] = 0;
   out_6441421400486242095[113] = 0;
   out_6441421400486242095[114] = 1;
   out_6441421400486242095[115] = 0;
   out_6441421400486242095[116] = 0;
   out_6441421400486242095[117] = 0;
   out_6441421400486242095[118] = 0;
   out_6441421400486242095[119] = 0;
   out_6441421400486242095[120] = 0;
   out_6441421400486242095[121] = 0;
   out_6441421400486242095[122] = 0;
   out_6441421400486242095[123] = 0;
   out_6441421400486242095[124] = 0;
   out_6441421400486242095[125] = 0;
   out_6441421400486242095[126] = 0;
   out_6441421400486242095[127] = 0;
   out_6441421400486242095[128] = 0;
   out_6441421400486242095[129] = 0;
   out_6441421400486242095[130] = 0;
   out_6441421400486242095[131] = 0;
   out_6441421400486242095[132] = 0;
   out_6441421400486242095[133] = 1;
   out_6441421400486242095[134] = 0;
   out_6441421400486242095[135] = 0;
   out_6441421400486242095[136] = 0;
   out_6441421400486242095[137] = 0;
   out_6441421400486242095[138] = 0;
   out_6441421400486242095[139] = 0;
   out_6441421400486242095[140] = 0;
   out_6441421400486242095[141] = 0;
   out_6441421400486242095[142] = 0;
   out_6441421400486242095[143] = 0;
   out_6441421400486242095[144] = 0;
   out_6441421400486242095[145] = 0;
   out_6441421400486242095[146] = 0;
   out_6441421400486242095[147] = 0;
   out_6441421400486242095[148] = 0;
   out_6441421400486242095[149] = 0;
   out_6441421400486242095[150] = 0;
   out_6441421400486242095[151] = 0;
   out_6441421400486242095[152] = 1;
   out_6441421400486242095[153] = 0;
   out_6441421400486242095[154] = 0;
   out_6441421400486242095[155] = 0;
   out_6441421400486242095[156] = 0;
   out_6441421400486242095[157] = 0;
   out_6441421400486242095[158] = 0;
   out_6441421400486242095[159] = 0;
   out_6441421400486242095[160] = 0;
   out_6441421400486242095[161] = 0;
   out_6441421400486242095[162] = 0;
   out_6441421400486242095[163] = 0;
   out_6441421400486242095[164] = 0;
   out_6441421400486242095[165] = 0;
   out_6441421400486242095[166] = 0;
   out_6441421400486242095[167] = 0;
   out_6441421400486242095[168] = 0;
   out_6441421400486242095[169] = 0;
   out_6441421400486242095[170] = 0;
   out_6441421400486242095[171] = 1;
   out_6441421400486242095[172] = 0;
   out_6441421400486242095[173] = 0;
   out_6441421400486242095[174] = 0;
   out_6441421400486242095[175] = 0;
   out_6441421400486242095[176] = 0;
   out_6441421400486242095[177] = 0;
   out_6441421400486242095[178] = 0;
   out_6441421400486242095[179] = 0;
   out_6441421400486242095[180] = 0;
   out_6441421400486242095[181] = 0;
   out_6441421400486242095[182] = 0;
   out_6441421400486242095[183] = 0;
   out_6441421400486242095[184] = 0;
   out_6441421400486242095[185] = 0;
   out_6441421400486242095[186] = 0;
   out_6441421400486242095[187] = 0;
   out_6441421400486242095[188] = 0;
   out_6441421400486242095[189] = 0;
   out_6441421400486242095[190] = 1;
   out_6441421400486242095[191] = 0;
   out_6441421400486242095[192] = 0;
   out_6441421400486242095[193] = 0;
   out_6441421400486242095[194] = 0;
   out_6441421400486242095[195] = 0;
   out_6441421400486242095[196] = 0;
   out_6441421400486242095[197] = 0;
   out_6441421400486242095[198] = 0;
   out_6441421400486242095[199] = 0;
   out_6441421400486242095[200] = 0;
   out_6441421400486242095[201] = 0;
   out_6441421400486242095[202] = 0;
   out_6441421400486242095[203] = 0;
   out_6441421400486242095[204] = 0;
   out_6441421400486242095[205] = 0;
   out_6441421400486242095[206] = 0;
   out_6441421400486242095[207] = 0;
   out_6441421400486242095[208] = 0;
   out_6441421400486242095[209] = 1;
   out_6441421400486242095[210] = 0;
   out_6441421400486242095[211] = 0;
   out_6441421400486242095[212] = 0;
   out_6441421400486242095[213] = 0;
   out_6441421400486242095[214] = 0;
   out_6441421400486242095[215] = 0;
   out_6441421400486242095[216] = 0;
   out_6441421400486242095[217] = 0;
   out_6441421400486242095[218] = 0;
   out_6441421400486242095[219] = 0;
   out_6441421400486242095[220] = 0;
   out_6441421400486242095[221] = 0;
   out_6441421400486242095[222] = 0;
   out_6441421400486242095[223] = 0;
   out_6441421400486242095[224] = 0;
   out_6441421400486242095[225] = 0;
   out_6441421400486242095[226] = 0;
   out_6441421400486242095[227] = 0;
   out_6441421400486242095[228] = 1;
   out_6441421400486242095[229] = 0;
   out_6441421400486242095[230] = 0;
   out_6441421400486242095[231] = 0;
   out_6441421400486242095[232] = 0;
   out_6441421400486242095[233] = 0;
   out_6441421400486242095[234] = 0;
   out_6441421400486242095[235] = 0;
   out_6441421400486242095[236] = 0;
   out_6441421400486242095[237] = 0;
   out_6441421400486242095[238] = 0;
   out_6441421400486242095[239] = 0;
   out_6441421400486242095[240] = 0;
   out_6441421400486242095[241] = 0;
   out_6441421400486242095[242] = 0;
   out_6441421400486242095[243] = 0;
   out_6441421400486242095[244] = 0;
   out_6441421400486242095[245] = 0;
   out_6441421400486242095[246] = 0;
   out_6441421400486242095[247] = 1;
   out_6441421400486242095[248] = 0;
   out_6441421400486242095[249] = 0;
   out_6441421400486242095[250] = 0;
   out_6441421400486242095[251] = 0;
   out_6441421400486242095[252] = 0;
   out_6441421400486242095[253] = 0;
   out_6441421400486242095[254] = 0;
   out_6441421400486242095[255] = 0;
   out_6441421400486242095[256] = 0;
   out_6441421400486242095[257] = 0;
   out_6441421400486242095[258] = 0;
   out_6441421400486242095[259] = 0;
   out_6441421400486242095[260] = 0;
   out_6441421400486242095[261] = 0;
   out_6441421400486242095[262] = 0;
   out_6441421400486242095[263] = 0;
   out_6441421400486242095[264] = 0;
   out_6441421400486242095[265] = 0;
   out_6441421400486242095[266] = 1;
   out_6441421400486242095[267] = 0;
   out_6441421400486242095[268] = 0;
   out_6441421400486242095[269] = 0;
   out_6441421400486242095[270] = 0;
   out_6441421400486242095[271] = 0;
   out_6441421400486242095[272] = 0;
   out_6441421400486242095[273] = 0;
   out_6441421400486242095[274] = 0;
   out_6441421400486242095[275] = 0;
   out_6441421400486242095[276] = 0;
   out_6441421400486242095[277] = 0;
   out_6441421400486242095[278] = 0;
   out_6441421400486242095[279] = 0;
   out_6441421400486242095[280] = 0;
   out_6441421400486242095[281] = 0;
   out_6441421400486242095[282] = 0;
   out_6441421400486242095[283] = 0;
   out_6441421400486242095[284] = 0;
   out_6441421400486242095[285] = 1;
   out_6441421400486242095[286] = 0;
   out_6441421400486242095[287] = 0;
   out_6441421400486242095[288] = 0;
   out_6441421400486242095[289] = 0;
   out_6441421400486242095[290] = 0;
   out_6441421400486242095[291] = 0;
   out_6441421400486242095[292] = 0;
   out_6441421400486242095[293] = 0;
   out_6441421400486242095[294] = 0;
   out_6441421400486242095[295] = 0;
   out_6441421400486242095[296] = 0;
   out_6441421400486242095[297] = 0;
   out_6441421400486242095[298] = 0;
   out_6441421400486242095[299] = 0;
   out_6441421400486242095[300] = 0;
   out_6441421400486242095[301] = 0;
   out_6441421400486242095[302] = 0;
   out_6441421400486242095[303] = 0;
   out_6441421400486242095[304] = 1;
   out_6441421400486242095[305] = 0;
   out_6441421400486242095[306] = 0;
   out_6441421400486242095[307] = 0;
   out_6441421400486242095[308] = 0;
   out_6441421400486242095[309] = 0;
   out_6441421400486242095[310] = 0;
   out_6441421400486242095[311] = 0;
   out_6441421400486242095[312] = 0;
   out_6441421400486242095[313] = 0;
   out_6441421400486242095[314] = 0;
   out_6441421400486242095[315] = 0;
   out_6441421400486242095[316] = 0;
   out_6441421400486242095[317] = 0;
   out_6441421400486242095[318] = 0;
   out_6441421400486242095[319] = 0;
   out_6441421400486242095[320] = 0;
   out_6441421400486242095[321] = 0;
   out_6441421400486242095[322] = 0;
   out_6441421400486242095[323] = 1;
}
void h_4(double *state, double *unused, double *out_4573904491198962061) {
   out_4573904491198962061[0] = state[6] + state[9];
   out_4573904491198962061[1] = state[7] + state[10];
   out_4573904491198962061[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_6445319511998695839) {
   out_6445319511998695839[0] = 0;
   out_6445319511998695839[1] = 0;
   out_6445319511998695839[2] = 0;
   out_6445319511998695839[3] = 0;
   out_6445319511998695839[4] = 0;
   out_6445319511998695839[5] = 0;
   out_6445319511998695839[6] = 1;
   out_6445319511998695839[7] = 0;
   out_6445319511998695839[8] = 0;
   out_6445319511998695839[9] = 1;
   out_6445319511998695839[10] = 0;
   out_6445319511998695839[11] = 0;
   out_6445319511998695839[12] = 0;
   out_6445319511998695839[13] = 0;
   out_6445319511998695839[14] = 0;
   out_6445319511998695839[15] = 0;
   out_6445319511998695839[16] = 0;
   out_6445319511998695839[17] = 0;
   out_6445319511998695839[18] = 0;
   out_6445319511998695839[19] = 0;
   out_6445319511998695839[20] = 0;
   out_6445319511998695839[21] = 0;
   out_6445319511998695839[22] = 0;
   out_6445319511998695839[23] = 0;
   out_6445319511998695839[24] = 0;
   out_6445319511998695839[25] = 1;
   out_6445319511998695839[26] = 0;
   out_6445319511998695839[27] = 0;
   out_6445319511998695839[28] = 1;
   out_6445319511998695839[29] = 0;
   out_6445319511998695839[30] = 0;
   out_6445319511998695839[31] = 0;
   out_6445319511998695839[32] = 0;
   out_6445319511998695839[33] = 0;
   out_6445319511998695839[34] = 0;
   out_6445319511998695839[35] = 0;
   out_6445319511998695839[36] = 0;
   out_6445319511998695839[37] = 0;
   out_6445319511998695839[38] = 0;
   out_6445319511998695839[39] = 0;
   out_6445319511998695839[40] = 0;
   out_6445319511998695839[41] = 0;
   out_6445319511998695839[42] = 0;
   out_6445319511998695839[43] = 0;
   out_6445319511998695839[44] = 1;
   out_6445319511998695839[45] = 0;
   out_6445319511998695839[46] = 0;
   out_6445319511998695839[47] = 1;
   out_6445319511998695839[48] = 0;
   out_6445319511998695839[49] = 0;
   out_6445319511998695839[50] = 0;
   out_6445319511998695839[51] = 0;
   out_6445319511998695839[52] = 0;
   out_6445319511998695839[53] = 0;
}
void h_10(double *state, double *unused, double *out_2344085230968916776) {
   out_2344085230968916776[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_2344085230968916776[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_2344085230968916776[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_1355793170921322878) {
   out_1355793170921322878[0] = 0;
   out_1355793170921322878[1] = 9.8100000000000005*cos(state[1]);
   out_1355793170921322878[2] = 0;
   out_1355793170921322878[3] = 0;
   out_1355793170921322878[4] = -state[8];
   out_1355793170921322878[5] = state[7];
   out_1355793170921322878[6] = 0;
   out_1355793170921322878[7] = state[5];
   out_1355793170921322878[8] = -state[4];
   out_1355793170921322878[9] = 0;
   out_1355793170921322878[10] = 0;
   out_1355793170921322878[11] = 0;
   out_1355793170921322878[12] = 1;
   out_1355793170921322878[13] = 0;
   out_1355793170921322878[14] = 0;
   out_1355793170921322878[15] = 1;
   out_1355793170921322878[16] = 0;
   out_1355793170921322878[17] = 0;
   out_1355793170921322878[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_1355793170921322878[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_1355793170921322878[20] = 0;
   out_1355793170921322878[21] = state[8];
   out_1355793170921322878[22] = 0;
   out_1355793170921322878[23] = -state[6];
   out_1355793170921322878[24] = -state[5];
   out_1355793170921322878[25] = 0;
   out_1355793170921322878[26] = state[3];
   out_1355793170921322878[27] = 0;
   out_1355793170921322878[28] = 0;
   out_1355793170921322878[29] = 0;
   out_1355793170921322878[30] = 0;
   out_1355793170921322878[31] = 1;
   out_1355793170921322878[32] = 0;
   out_1355793170921322878[33] = 0;
   out_1355793170921322878[34] = 1;
   out_1355793170921322878[35] = 0;
   out_1355793170921322878[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_1355793170921322878[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_1355793170921322878[38] = 0;
   out_1355793170921322878[39] = -state[7];
   out_1355793170921322878[40] = state[6];
   out_1355793170921322878[41] = 0;
   out_1355793170921322878[42] = state[4];
   out_1355793170921322878[43] = -state[3];
   out_1355793170921322878[44] = 0;
   out_1355793170921322878[45] = 0;
   out_1355793170921322878[46] = 0;
   out_1355793170921322878[47] = 0;
   out_1355793170921322878[48] = 0;
   out_1355793170921322878[49] = 0;
   out_1355793170921322878[50] = 1;
   out_1355793170921322878[51] = 0;
   out_1355793170921322878[52] = 0;
   out_1355793170921322878[53] = 1;
}
void h_13(double *state, double *unused, double *out_2891206438167930313) {
   out_2891206438167930313[0] = state[3];
   out_2891206438167930313[1] = state[4];
   out_2891206438167930313[2] = state[5];
}
void H_13(double *state, double *unused, double *out_8789150736378522976) {
   out_8789150736378522976[0] = 0;
   out_8789150736378522976[1] = 0;
   out_8789150736378522976[2] = 0;
   out_8789150736378522976[3] = 1;
   out_8789150736378522976[4] = 0;
   out_8789150736378522976[5] = 0;
   out_8789150736378522976[6] = 0;
   out_8789150736378522976[7] = 0;
   out_8789150736378522976[8] = 0;
   out_8789150736378522976[9] = 0;
   out_8789150736378522976[10] = 0;
   out_8789150736378522976[11] = 0;
   out_8789150736378522976[12] = 0;
   out_8789150736378522976[13] = 0;
   out_8789150736378522976[14] = 0;
   out_8789150736378522976[15] = 0;
   out_8789150736378522976[16] = 0;
   out_8789150736378522976[17] = 0;
   out_8789150736378522976[18] = 0;
   out_8789150736378522976[19] = 0;
   out_8789150736378522976[20] = 0;
   out_8789150736378522976[21] = 0;
   out_8789150736378522976[22] = 1;
   out_8789150736378522976[23] = 0;
   out_8789150736378522976[24] = 0;
   out_8789150736378522976[25] = 0;
   out_8789150736378522976[26] = 0;
   out_8789150736378522976[27] = 0;
   out_8789150736378522976[28] = 0;
   out_8789150736378522976[29] = 0;
   out_8789150736378522976[30] = 0;
   out_8789150736378522976[31] = 0;
   out_8789150736378522976[32] = 0;
   out_8789150736378522976[33] = 0;
   out_8789150736378522976[34] = 0;
   out_8789150736378522976[35] = 0;
   out_8789150736378522976[36] = 0;
   out_8789150736378522976[37] = 0;
   out_8789150736378522976[38] = 0;
   out_8789150736378522976[39] = 0;
   out_8789150736378522976[40] = 0;
   out_8789150736378522976[41] = 1;
   out_8789150736378522976[42] = 0;
   out_8789150736378522976[43] = 0;
   out_8789150736378522976[44] = 0;
   out_8789150736378522976[45] = 0;
   out_8789150736378522976[46] = 0;
   out_8789150736378522976[47] = 0;
   out_8789150736378522976[48] = 0;
   out_8789150736378522976[49] = 0;
   out_8789150736378522976[50] = 0;
   out_8789150736378522976[51] = 0;
   out_8789150736378522976[52] = 0;
   out_8789150736378522976[53] = 0;
}
void h_14(double *state, double *unused, double *out_3674947514289008640) {
   out_3674947514289008640[0] = state[6];
   out_3674947514289008640[1] = state[7];
   out_3674947514289008640[2] = state[8];
}
void H_14(double *state, double *unused, double *out_8038183705371371248) {
   out_8038183705371371248[0] = 0;
   out_8038183705371371248[1] = 0;
   out_8038183705371371248[2] = 0;
   out_8038183705371371248[3] = 0;
   out_8038183705371371248[4] = 0;
   out_8038183705371371248[5] = 0;
   out_8038183705371371248[6] = 1;
   out_8038183705371371248[7] = 0;
   out_8038183705371371248[8] = 0;
   out_8038183705371371248[9] = 0;
   out_8038183705371371248[10] = 0;
   out_8038183705371371248[11] = 0;
   out_8038183705371371248[12] = 0;
   out_8038183705371371248[13] = 0;
   out_8038183705371371248[14] = 0;
   out_8038183705371371248[15] = 0;
   out_8038183705371371248[16] = 0;
   out_8038183705371371248[17] = 0;
   out_8038183705371371248[18] = 0;
   out_8038183705371371248[19] = 0;
   out_8038183705371371248[20] = 0;
   out_8038183705371371248[21] = 0;
   out_8038183705371371248[22] = 0;
   out_8038183705371371248[23] = 0;
   out_8038183705371371248[24] = 0;
   out_8038183705371371248[25] = 1;
   out_8038183705371371248[26] = 0;
   out_8038183705371371248[27] = 0;
   out_8038183705371371248[28] = 0;
   out_8038183705371371248[29] = 0;
   out_8038183705371371248[30] = 0;
   out_8038183705371371248[31] = 0;
   out_8038183705371371248[32] = 0;
   out_8038183705371371248[33] = 0;
   out_8038183705371371248[34] = 0;
   out_8038183705371371248[35] = 0;
   out_8038183705371371248[36] = 0;
   out_8038183705371371248[37] = 0;
   out_8038183705371371248[38] = 0;
   out_8038183705371371248[39] = 0;
   out_8038183705371371248[40] = 0;
   out_8038183705371371248[41] = 0;
   out_8038183705371371248[42] = 0;
   out_8038183705371371248[43] = 0;
   out_8038183705371371248[44] = 1;
   out_8038183705371371248[45] = 0;
   out_8038183705371371248[46] = 0;
   out_8038183705371371248[47] = 0;
   out_8038183705371371248[48] = 0;
   out_8038183705371371248[49] = 0;
   out_8038183705371371248[50] = 0;
   out_8038183705371371248[51] = 0;
   out_8038183705371371248[52] = 0;
   out_8038183705371371248[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_7576548165016352808) {
  err_fun(nom_x, delta_x, out_7576548165016352808);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_3269481700032691791) {
  inv_err_fun(nom_x, true_x, out_3269481700032691791);
}
void pose_H_mod_fun(double *state, double *out_3135696547169702091) {
  H_mod_fun(state, out_3135696547169702091);
}
void pose_f_fun(double *state, double dt, double *out_2367158378490033196) {
  f_fun(state,  dt, out_2367158378490033196);
}
void pose_F_fun(double *state, double dt, double *out_6441421400486242095) {
  F_fun(state,  dt, out_6441421400486242095);
}
void pose_h_4(double *state, double *unused, double *out_4573904491198962061) {
  h_4(state, unused, out_4573904491198962061);
}
void pose_H_4(double *state, double *unused, double *out_6445319511998695839) {
  H_4(state, unused, out_6445319511998695839);
}
void pose_h_10(double *state, double *unused, double *out_2344085230968916776) {
  h_10(state, unused, out_2344085230968916776);
}
void pose_H_10(double *state, double *unused, double *out_1355793170921322878) {
  H_10(state, unused, out_1355793170921322878);
}
void pose_h_13(double *state, double *unused, double *out_2891206438167930313) {
  h_13(state, unused, out_2891206438167930313);
}
void pose_H_13(double *state, double *unused, double *out_8789150736378522976) {
  H_13(state, unused, out_8789150736378522976);
}
void pose_h_14(double *state, double *unused, double *out_3674947514289008640) {
  h_14(state, unused, out_3674947514289008640);
}
void pose_H_14(double *state, double *unused, double *out_8038183705371371248) {
  H_14(state, unused, out_8038183705371371248);
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
