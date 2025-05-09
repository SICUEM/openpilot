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
void err_fun(double *nom_x, double *delta_x, double *out_8846465336200542325) {
   out_8846465336200542325[0] = delta_x[0] + nom_x[0];
   out_8846465336200542325[1] = delta_x[1] + nom_x[1];
   out_8846465336200542325[2] = delta_x[2] + nom_x[2];
   out_8846465336200542325[3] = delta_x[3] + nom_x[3];
   out_8846465336200542325[4] = delta_x[4] + nom_x[4];
   out_8846465336200542325[5] = delta_x[5] + nom_x[5];
   out_8846465336200542325[6] = delta_x[6] + nom_x[6];
   out_8846465336200542325[7] = delta_x[7] + nom_x[7];
   out_8846465336200542325[8] = delta_x[8] + nom_x[8];
   out_8846465336200542325[9] = delta_x[9] + nom_x[9];
   out_8846465336200542325[10] = delta_x[10] + nom_x[10];
   out_8846465336200542325[11] = delta_x[11] + nom_x[11];
   out_8846465336200542325[12] = delta_x[12] + nom_x[12];
   out_8846465336200542325[13] = delta_x[13] + nom_x[13];
   out_8846465336200542325[14] = delta_x[14] + nom_x[14];
   out_8846465336200542325[15] = delta_x[15] + nom_x[15];
   out_8846465336200542325[16] = delta_x[16] + nom_x[16];
   out_8846465336200542325[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_904878762552493072) {
   out_904878762552493072[0] = -nom_x[0] + true_x[0];
   out_904878762552493072[1] = -nom_x[1] + true_x[1];
   out_904878762552493072[2] = -nom_x[2] + true_x[2];
   out_904878762552493072[3] = -nom_x[3] + true_x[3];
   out_904878762552493072[4] = -nom_x[4] + true_x[4];
   out_904878762552493072[5] = -nom_x[5] + true_x[5];
   out_904878762552493072[6] = -nom_x[6] + true_x[6];
   out_904878762552493072[7] = -nom_x[7] + true_x[7];
   out_904878762552493072[8] = -nom_x[8] + true_x[8];
   out_904878762552493072[9] = -nom_x[9] + true_x[9];
   out_904878762552493072[10] = -nom_x[10] + true_x[10];
   out_904878762552493072[11] = -nom_x[11] + true_x[11];
   out_904878762552493072[12] = -nom_x[12] + true_x[12];
   out_904878762552493072[13] = -nom_x[13] + true_x[13];
   out_904878762552493072[14] = -nom_x[14] + true_x[14];
   out_904878762552493072[15] = -nom_x[15] + true_x[15];
   out_904878762552493072[16] = -nom_x[16] + true_x[16];
   out_904878762552493072[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_8522983127573850096) {
   out_8522983127573850096[0] = 1.0;
   out_8522983127573850096[1] = 0.0;
   out_8522983127573850096[2] = 0.0;
   out_8522983127573850096[3] = 0.0;
   out_8522983127573850096[4] = 0.0;
   out_8522983127573850096[5] = 0.0;
   out_8522983127573850096[6] = 0.0;
   out_8522983127573850096[7] = 0.0;
   out_8522983127573850096[8] = 0.0;
   out_8522983127573850096[9] = 0.0;
   out_8522983127573850096[10] = 0.0;
   out_8522983127573850096[11] = 0.0;
   out_8522983127573850096[12] = 0.0;
   out_8522983127573850096[13] = 0.0;
   out_8522983127573850096[14] = 0.0;
   out_8522983127573850096[15] = 0.0;
   out_8522983127573850096[16] = 0.0;
   out_8522983127573850096[17] = 0.0;
   out_8522983127573850096[18] = 0.0;
   out_8522983127573850096[19] = 1.0;
   out_8522983127573850096[20] = 0.0;
   out_8522983127573850096[21] = 0.0;
   out_8522983127573850096[22] = 0.0;
   out_8522983127573850096[23] = 0.0;
   out_8522983127573850096[24] = 0.0;
   out_8522983127573850096[25] = 0.0;
   out_8522983127573850096[26] = 0.0;
   out_8522983127573850096[27] = 0.0;
   out_8522983127573850096[28] = 0.0;
   out_8522983127573850096[29] = 0.0;
   out_8522983127573850096[30] = 0.0;
   out_8522983127573850096[31] = 0.0;
   out_8522983127573850096[32] = 0.0;
   out_8522983127573850096[33] = 0.0;
   out_8522983127573850096[34] = 0.0;
   out_8522983127573850096[35] = 0.0;
   out_8522983127573850096[36] = 0.0;
   out_8522983127573850096[37] = 0.0;
   out_8522983127573850096[38] = 1.0;
   out_8522983127573850096[39] = 0.0;
   out_8522983127573850096[40] = 0.0;
   out_8522983127573850096[41] = 0.0;
   out_8522983127573850096[42] = 0.0;
   out_8522983127573850096[43] = 0.0;
   out_8522983127573850096[44] = 0.0;
   out_8522983127573850096[45] = 0.0;
   out_8522983127573850096[46] = 0.0;
   out_8522983127573850096[47] = 0.0;
   out_8522983127573850096[48] = 0.0;
   out_8522983127573850096[49] = 0.0;
   out_8522983127573850096[50] = 0.0;
   out_8522983127573850096[51] = 0.0;
   out_8522983127573850096[52] = 0.0;
   out_8522983127573850096[53] = 0.0;
   out_8522983127573850096[54] = 0.0;
   out_8522983127573850096[55] = 0.0;
   out_8522983127573850096[56] = 0.0;
   out_8522983127573850096[57] = 1.0;
   out_8522983127573850096[58] = 0.0;
   out_8522983127573850096[59] = 0.0;
   out_8522983127573850096[60] = 0.0;
   out_8522983127573850096[61] = 0.0;
   out_8522983127573850096[62] = 0.0;
   out_8522983127573850096[63] = 0.0;
   out_8522983127573850096[64] = 0.0;
   out_8522983127573850096[65] = 0.0;
   out_8522983127573850096[66] = 0.0;
   out_8522983127573850096[67] = 0.0;
   out_8522983127573850096[68] = 0.0;
   out_8522983127573850096[69] = 0.0;
   out_8522983127573850096[70] = 0.0;
   out_8522983127573850096[71] = 0.0;
   out_8522983127573850096[72] = 0.0;
   out_8522983127573850096[73] = 0.0;
   out_8522983127573850096[74] = 0.0;
   out_8522983127573850096[75] = 0.0;
   out_8522983127573850096[76] = 1.0;
   out_8522983127573850096[77] = 0.0;
   out_8522983127573850096[78] = 0.0;
   out_8522983127573850096[79] = 0.0;
   out_8522983127573850096[80] = 0.0;
   out_8522983127573850096[81] = 0.0;
   out_8522983127573850096[82] = 0.0;
   out_8522983127573850096[83] = 0.0;
   out_8522983127573850096[84] = 0.0;
   out_8522983127573850096[85] = 0.0;
   out_8522983127573850096[86] = 0.0;
   out_8522983127573850096[87] = 0.0;
   out_8522983127573850096[88] = 0.0;
   out_8522983127573850096[89] = 0.0;
   out_8522983127573850096[90] = 0.0;
   out_8522983127573850096[91] = 0.0;
   out_8522983127573850096[92] = 0.0;
   out_8522983127573850096[93] = 0.0;
   out_8522983127573850096[94] = 0.0;
   out_8522983127573850096[95] = 1.0;
   out_8522983127573850096[96] = 0.0;
   out_8522983127573850096[97] = 0.0;
   out_8522983127573850096[98] = 0.0;
   out_8522983127573850096[99] = 0.0;
   out_8522983127573850096[100] = 0.0;
   out_8522983127573850096[101] = 0.0;
   out_8522983127573850096[102] = 0.0;
   out_8522983127573850096[103] = 0.0;
   out_8522983127573850096[104] = 0.0;
   out_8522983127573850096[105] = 0.0;
   out_8522983127573850096[106] = 0.0;
   out_8522983127573850096[107] = 0.0;
   out_8522983127573850096[108] = 0.0;
   out_8522983127573850096[109] = 0.0;
   out_8522983127573850096[110] = 0.0;
   out_8522983127573850096[111] = 0.0;
   out_8522983127573850096[112] = 0.0;
   out_8522983127573850096[113] = 0.0;
   out_8522983127573850096[114] = 1.0;
   out_8522983127573850096[115] = 0.0;
   out_8522983127573850096[116] = 0.0;
   out_8522983127573850096[117] = 0.0;
   out_8522983127573850096[118] = 0.0;
   out_8522983127573850096[119] = 0.0;
   out_8522983127573850096[120] = 0.0;
   out_8522983127573850096[121] = 0.0;
   out_8522983127573850096[122] = 0.0;
   out_8522983127573850096[123] = 0.0;
   out_8522983127573850096[124] = 0.0;
   out_8522983127573850096[125] = 0.0;
   out_8522983127573850096[126] = 0.0;
   out_8522983127573850096[127] = 0.0;
   out_8522983127573850096[128] = 0.0;
   out_8522983127573850096[129] = 0.0;
   out_8522983127573850096[130] = 0.0;
   out_8522983127573850096[131] = 0.0;
   out_8522983127573850096[132] = 0.0;
   out_8522983127573850096[133] = 1.0;
   out_8522983127573850096[134] = 0.0;
   out_8522983127573850096[135] = 0.0;
   out_8522983127573850096[136] = 0.0;
   out_8522983127573850096[137] = 0.0;
   out_8522983127573850096[138] = 0.0;
   out_8522983127573850096[139] = 0.0;
   out_8522983127573850096[140] = 0.0;
   out_8522983127573850096[141] = 0.0;
   out_8522983127573850096[142] = 0.0;
   out_8522983127573850096[143] = 0.0;
   out_8522983127573850096[144] = 0.0;
   out_8522983127573850096[145] = 0.0;
   out_8522983127573850096[146] = 0.0;
   out_8522983127573850096[147] = 0.0;
   out_8522983127573850096[148] = 0.0;
   out_8522983127573850096[149] = 0.0;
   out_8522983127573850096[150] = 0.0;
   out_8522983127573850096[151] = 0.0;
   out_8522983127573850096[152] = 1.0;
   out_8522983127573850096[153] = 0.0;
   out_8522983127573850096[154] = 0.0;
   out_8522983127573850096[155] = 0.0;
   out_8522983127573850096[156] = 0.0;
   out_8522983127573850096[157] = 0.0;
   out_8522983127573850096[158] = 0.0;
   out_8522983127573850096[159] = 0.0;
   out_8522983127573850096[160] = 0.0;
   out_8522983127573850096[161] = 0.0;
   out_8522983127573850096[162] = 0.0;
   out_8522983127573850096[163] = 0.0;
   out_8522983127573850096[164] = 0.0;
   out_8522983127573850096[165] = 0.0;
   out_8522983127573850096[166] = 0.0;
   out_8522983127573850096[167] = 0.0;
   out_8522983127573850096[168] = 0.0;
   out_8522983127573850096[169] = 0.0;
   out_8522983127573850096[170] = 0.0;
   out_8522983127573850096[171] = 1.0;
   out_8522983127573850096[172] = 0.0;
   out_8522983127573850096[173] = 0.0;
   out_8522983127573850096[174] = 0.0;
   out_8522983127573850096[175] = 0.0;
   out_8522983127573850096[176] = 0.0;
   out_8522983127573850096[177] = 0.0;
   out_8522983127573850096[178] = 0.0;
   out_8522983127573850096[179] = 0.0;
   out_8522983127573850096[180] = 0.0;
   out_8522983127573850096[181] = 0.0;
   out_8522983127573850096[182] = 0.0;
   out_8522983127573850096[183] = 0.0;
   out_8522983127573850096[184] = 0.0;
   out_8522983127573850096[185] = 0.0;
   out_8522983127573850096[186] = 0.0;
   out_8522983127573850096[187] = 0.0;
   out_8522983127573850096[188] = 0.0;
   out_8522983127573850096[189] = 0.0;
   out_8522983127573850096[190] = 1.0;
   out_8522983127573850096[191] = 0.0;
   out_8522983127573850096[192] = 0.0;
   out_8522983127573850096[193] = 0.0;
   out_8522983127573850096[194] = 0.0;
   out_8522983127573850096[195] = 0.0;
   out_8522983127573850096[196] = 0.0;
   out_8522983127573850096[197] = 0.0;
   out_8522983127573850096[198] = 0.0;
   out_8522983127573850096[199] = 0.0;
   out_8522983127573850096[200] = 0.0;
   out_8522983127573850096[201] = 0.0;
   out_8522983127573850096[202] = 0.0;
   out_8522983127573850096[203] = 0.0;
   out_8522983127573850096[204] = 0.0;
   out_8522983127573850096[205] = 0.0;
   out_8522983127573850096[206] = 0.0;
   out_8522983127573850096[207] = 0.0;
   out_8522983127573850096[208] = 0.0;
   out_8522983127573850096[209] = 1.0;
   out_8522983127573850096[210] = 0.0;
   out_8522983127573850096[211] = 0.0;
   out_8522983127573850096[212] = 0.0;
   out_8522983127573850096[213] = 0.0;
   out_8522983127573850096[214] = 0.0;
   out_8522983127573850096[215] = 0.0;
   out_8522983127573850096[216] = 0.0;
   out_8522983127573850096[217] = 0.0;
   out_8522983127573850096[218] = 0.0;
   out_8522983127573850096[219] = 0.0;
   out_8522983127573850096[220] = 0.0;
   out_8522983127573850096[221] = 0.0;
   out_8522983127573850096[222] = 0.0;
   out_8522983127573850096[223] = 0.0;
   out_8522983127573850096[224] = 0.0;
   out_8522983127573850096[225] = 0.0;
   out_8522983127573850096[226] = 0.0;
   out_8522983127573850096[227] = 0.0;
   out_8522983127573850096[228] = 1.0;
   out_8522983127573850096[229] = 0.0;
   out_8522983127573850096[230] = 0.0;
   out_8522983127573850096[231] = 0.0;
   out_8522983127573850096[232] = 0.0;
   out_8522983127573850096[233] = 0.0;
   out_8522983127573850096[234] = 0.0;
   out_8522983127573850096[235] = 0.0;
   out_8522983127573850096[236] = 0.0;
   out_8522983127573850096[237] = 0.0;
   out_8522983127573850096[238] = 0.0;
   out_8522983127573850096[239] = 0.0;
   out_8522983127573850096[240] = 0.0;
   out_8522983127573850096[241] = 0.0;
   out_8522983127573850096[242] = 0.0;
   out_8522983127573850096[243] = 0.0;
   out_8522983127573850096[244] = 0.0;
   out_8522983127573850096[245] = 0.0;
   out_8522983127573850096[246] = 0.0;
   out_8522983127573850096[247] = 1.0;
   out_8522983127573850096[248] = 0.0;
   out_8522983127573850096[249] = 0.0;
   out_8522983127573850096[250] = 0.0;
   out_8522983127573850096[251] = 0.0;
   out_8522983127573850096[252] = 0.0;
   out_8522983127573850096[253] = 0.0;
   out_8522983127573850096[254] = 0.0;
   out_8522983127573850096[255] = 0.0;
   out_8522983127573850096[256] = 0.0;
   out_8522983127573850096[257] = 0.0;
   out_8522983127573850096[258] = 0.0;
   out_8522983127573850096[259] = 0.0;
   out_8522983127573850096[260] = 0.0;
   out_8522983127573850096[261] = 0.0;
   out_8522983127573850096[262] = 0.0;
   out_8522983127573850096[263] = 0.0;
   out_8522983127573850096[264] = 0.0;
   out_8522983127573850096[265] = 0.0;
   out_8522983127573850096[266] = 1.0;
   out_8522983127573850096[267] = 0.0;
   out_8522983127573850096[268] = 0.0;
   out_8522983127573850096[269] = 0.0;
   out_8522983127573850096[270] = 0.0;
   out_8522983127573850096[271] = 0.0;
   out_8522983127573850096[272] = 0.0;
   out_8522983127573850096[273] = 0.0;
   out_8522983127573850096[274] = 0.0;
   out_8522983127573850096[275] = 0.0;
   out_8522983127573850096[276] = 0.0;
   out_8522983127573850096[277] = 0.0;
   out_8522983127573850096[278] = 0.0;
   out_8522983127573850096[279] = 0.0;
   out_8522983127573850096[280] = 0.0;
   out_8522983127573850096[281] = 0.0;
   out_8522983127573850096[282] = 0.0;
   out_8522983127573850096[283] = 0.0;
   out_8522983127573850096[284] = 0.0;
   out_8522983127573850096[285] = 1.0;
   out_8522983127573850096[286] = 0.0;
   out_8522983127573850096[287] = 0.0;
   out_8522983127573850096[288] = 0.0;
   out_8522983127573850096[289] = 0.0;
   out_8522983127573850096[290] = 0.0;
   out_8522983127573850096[291] = 0.0;
   out_8522983127573850096[292] = 0.0;
   out_8522983127573850096[293] = 0.0;
   out_8522983127573850096[294] = 0.0;
   out_8522983127573850096[295] = 0.0;
   out_8522983127573850096[296] = 0.0;
   out_8522983127573850096[297] = 0.0;
   out_8522983127573850096[298] = 0.0;
   out_8522983127573850096[299] = 0.0;
   out_8522983127573850096[300] = 0.0;
   out_8522983127573850096[301] = 0.0;
   out_8522983127573850096[302] = 0.0;
   out_8522983127573850096[303] = 0.0;
   out_8522983127573850096[304] = 1.0;
   out_8522983127573850096[305] = 0.0;
   out_8522983127573850096[306] = 0.0;
   out_8522983127573850096[307] = 0.0;
   out_8522983127573850096[308] = 0.0;
   out_8522983127573850096[309] = 0.0;
   out_8522983127573850096[310] = 0.0;
   out_8522983127573850096[311] = 0.0;
   out_8522983127573850096[312] = 0.0;
   out_8522983127573850096[313] = 0.0;
   out_8522983127573850096[314] = 0.0;
   out_8522983127573850096[315] = 0.0;
   out_8522983127573850096[316] = 0.0;
   out_8522983127573850096[317] = 0.0;
   out_8522983127573850096[318] = 0.0;
   out_8522983127573850096[319] = 0.0;
   out_8522983127573850096[320] = 0.0;
   out_8522983127573850096[321] = 0.0;
   out_8522983127573850096[322] = 0.0;
   out_8522983127573850096[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_611896847437543302) {
   out_611896847437543302[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_611896847437543302[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_611896847437543302[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_611896847437543302[3] = dt*state[12] + state[3];
   out_611896847437543302[4] = dt*state[13] + state[4];
   out_611896847437543302[5] = dt*state[14] + state[5];
   out_611896847437543302[6] = state[6];
   out_611896847437543302[7] = state[7];
   out_611896847437543302[8] = state[8];
   out_611896847437543302[9] = state[9];
   out_611896847437543302[10] = state[10];
   out_611896847437543302[11] = state[11];
   out_611896847437543302[12] = state[12];
   out_611896847437543302[13] = state[13];
   out_611896847437543302[14] = state[14];
   out_611896847437543302[15] = state[15];
   out_611896847437543302[16] = state[16];
   out_611896847437543302[17] = state[17];
}
void F_fun(double *state, double dt, double *out_3104916241349686315) {
   out_3104916241349686315[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3104916241349686315[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3104916241349686315[2] = 0;
   out_3104916241349686315[3] = 0;
   out_3104916241349686315[4] = 0;
   out_3104916241349686315[5] = 0;
   out_3104916241349686315[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3104916241349686315[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3104916241349686315[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3104916241349686315[9] = 0;
   out_3104916241349686315[10] = 0;
   out_3104916241349686315[11] = 0;
   out_3104916241349686315[12] = 0;
   out_3104916241349686315[13] = 0;
   out_3104916241349686315[14] = 0;
   out_3104916241349686315[15] = 0;
   out_3104916241349686315[16] = 0;
   out_3104916241349686315[17] = 0;
   out_3104916241349686315[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3104916241349686315[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3104916241349686315[20] = 0;
   out_3104916241349686315[21] = 0;
   out_3104916241349686315[22] = 0;
   out_3104916241349686315[23] = 0;
   out_3104916241349686315[24] = 0;
   out_3104916241349686315[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3104916241349686315[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3104916241349686315[27] = 0;
   out_3104916241349686315[28] = 0;
   out_3104916241349686315[29] = 0;
   out_3104916241349686315[30] = 0;
   out_3104916241349686315[31] = 0;
   out_3104916241349686315[32] = 0;
   out_3104916241349686315[33] = 0;
   out_3104916241349686315[34] = 0;
   out_3104916241349686315[35] = 0;
   out_3104916241349686315[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3104916241349686315[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3104916241349686315[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3104916241349686315[39] = 0;
   out_3104916241349686315[40] = 0;
   out_3104916241349686315[41] = 0;
   out_3104916241349686315[42] = 0;
   out_3104916241349686315[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3104916241349686315[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3104916241349686315[45] = 0;
   out_3104916241349686315[46] = 0;
   out_3104916241349686315[47] = 0;
   out_3104916241349686315[48] = 0;
   out_3104916241349686315[49] = 0;
   out_3104916241349686315[50] = 0;
   out_3104916241349686315[51] = 0;
   out_3104916241349686315[52] = 0;
   out_3104916241349686315[53] = 0;
   out_3104916241349686315[54] = 0;
   out_3104916241349686315[55] = 0;
   out_3104916241349686315[56] = 0;
   out_3104916241349686315[57] = 1;
   out_3104916241349686315[58] = 0;
   out_3104916241349686315[59] = 0;
   out_3104916241349686315[60] = 0;
   out_3104916241349686315[61] = 0;
   out_3104916241349686315[62] = 0;
   out_3104916241349686315[63] = 0;
   out_3104916241349686315[64] = 0;
   out_3104916241349686315[65] = 0;
   out_3104916241349686315[66] = dt;
   out_3104916241349686315[67] = 0;
   out_3104916241349686315[68] = 0;
   out_3104916241349686315[69] = 0;
   out_3104916241349686315[70] = 0;
   out_3104916241349686315[71] = 0;
   out_3104916241349686315[72] = 0;
   out_3104916241349686315[73] = 0;
   out_3104916241349686315[74] = 0;
   out_3104916241349686315[75] = 0;
   out_3104916241349686315[76] = 1;
   out_3104916241349686315[77] = 0;
   out_3104916241349686315[78] = 0;
   out_3104916241349686315[79] = 0;
   out_3104916241349686315[80] = 0;
   out_3104916241349686315[81] = 0;
   out_3104916241349686315[82] = 0;
   out_3104916241349686315[83] = 0;
   out_3104916241349686315[84] = 0;
   out_3104916241349686315[85] = dt;
   out_3104916241349686315[86] = 0;
   out_3104916241349686315[87] = 0;
   out_3104916241349686315[88] = 0;
   out_3104916241349686315[89] = 0;
   out_3104916241349686315[90] = 0;
   out_3104916241349686315[91] = 0;
   out_3104916241349686315[92] = 0;
   out_3104916241349686315[93] = 0;
   out_3104916241349686315[94] = 0;
   out_3104916241349686315[95] = 1;
   out_3104916241349686315[96] = 0;
   out_3104916241349686315[97] = 0;
   out_3104916241349686315[98] = 0;
   out_3104916241349686315[99] = 0;
   out_3104916241349686315[100] = 0;
   out_3104916241349686315[101] = 0;
   out_3104916241349686315[102] = 0;
   out_3104916241349686315[103] = 0;
   out_3104916241349686315[104] = dt;
   out_3104916241349686315[105] = 0;
   out_3104916241349686315[106] = 0;
   out_3104916241349686315[107] = 0;
   out_3104916241349686315[108] = 0;
   out_3104916241349686315[109] = 0;
   out_3104916241349686315[110] = 0;
   out_3104916241349686315[111] = 0;
   out_3104916241349686315[112] = 0;
   out_3104916241349686315[113] = 0;
   out_3104916241349686315[114] = 1;
   out_3104916241349686315[115] = 0;
   out_3104916241349686315[116] = 0;
   out_3104916241349686315[117] = 0;
   out_3104916241349686315[118] = 0;
   out_3104916241349686315[119] = 0;
   out_3104916241349686315[120] = 0;
   out_3104916241349686315[121] = 0;
   out_3104916241349686315[122] = 0;
   out_3104916241349686315[123] = 0;
   out_3104916241349686315[124] = 0;
   out_3104916241349686315[125] = 0;
   out_3104916241349686315[126] = 0;
   out_3104916241349686315[127] = 0;
   out_3104916241349686315[128] = 0;
   out_3104916241349686315[129] = 0;
   out_3104916241349686315[130] = 0;
   out_3104916241349686315[131] = 0;
   out_3104916241349686315[132] = 0;
   out_3104916241349686315[133] = 1;
   out_3104916241349686315[134] = 0;
   out_3104916241349686315[135] = 0;
   out_3104916241349686315[136] = 0;
   out_3104916241349686315[137] = 0;
   out_3104916241349686315[138] = 0;
   out_3104916241349686315[139] = 0;
   out_3104916241349686315[140] = 0;
   out_3104916241349686315[141] = 0;
   out_3104916241349686315[142] = 0;
   out_3104916241349686315[143] = 0;
   out_3104916241349686315[144] = 0;
   out_3104916241349686315[145] = 0;
   out_3104916241349686315[146] = 0;
   out_3104916241349686315[147] = 0;
   out_3104916241349686315[148] = 0;
   out_3104916241349686315[149] = 0;
   out_3104916241349686315[150] = 0;
   out_3104916241349686315[151] = 0;
   out_3104916241349686315[152] = 1;
   out_3104916241349686315[153] = 0;
   out_3104916241349686315[154] = 0;
   out_3104916241349686315[155] = 0;
   out_3104916241349686315[156] = 0;
   out_3104916241349686315[157] = 0;
   out_3104916241349686315[158] = 0;
   out_3104916241349686315[159] = 0;
   out_3104916241349686315[160] = 0;
   out_3104916241349686315[161] = 0;
   out_3104916241349686315[162] = 0;
   out_3104916241349686315[163] = 0;
   out_3104916241349686315[164] = 0;
   out_3104916241349686315[165] = 0;
   out_3104916241349686315[166] = 0;
   out_3104916241349686315[167] = 0;
   out_3104916241349686315[168] = 0;
   out_3104916241349686315[169] = 0;
   out_3104916241349686315[170] = 0;
   out_3104916241349686315[171] = 1;
   out_3104916241349686315[172] = 0;
   out_3104916241349686315[173] = 0;
   out_3104916241349686315[174] = 0;
   out_3104916241349686315[175] = 0;
   out_3104916241349686315[176] = 0;
   out_3104916241349686315[177] = 0;
   out_3104916241349686315[178] = 0;
   out_3104916241349686315[179] = 0;
   out_3104916241349686315[180] = 0;
   out_3104916241349686315[181] = 0;
   out_3104916241349686315[182] = 0;
   out_3104916241349686315[183] = 0;
   out_3104916241349686315[184] = 0;
   out_3104916241349686315[185] = 0;
   out_3104916241349686315[186] = 0;
   out_3104916241349686315[187] = 0;
   out_3104916241349686315[188] = 0;
   out_3104916241349686315[189] = 0;
   out_3104916241349686315[190] = 1;
   out_3104916241349686315[191] = 0;
   out_3104916241349686315[192] = 0;
   out_3104916241349686315[193] = 0;
   out_3104916241349686315[194] = 0;
   out_3104916241349686315[195] = 0;
   out_3104916241349686315[196] = 0;
   out_3104916241349686315[197] = 0;
   out_3104916241349686315[198] = 0;
   out_3104916241349686315[199] = 0;
   out_3104916241349686315[200] = 0;
   out_3104916241349686315[201] = 0;
   out_3104916241349686315[202] = 0;
   out_3104916241349686315[203] = 0;
   out_3104916241349686315[204] = 0;
   out_3104916241349686315[205] = 0;
   out_3104916241349686315[206] = 0;
   out_3104916241349686315[207] = 0;
   out_3104916241349686315[208] = 0;
   out_3104916241349686315[209] = 1;
   out_3104916241349686315[210] = 0;
   out_3104916241349686315[211] = 0;
   out_3104916241349686315[212] = 0;
   out_3104916241349686315[213] = 0;
   out_3104916241349686315[214] = 0;
   out_3104916241349686315[215] = 0;
   out_3104916241349686315[216] = 0;
   out_3104916241349686315[217] = 0;
   out_3104916241349686315[218] = 0;
   out_3104916241349686315[219] = 0;
   out_3104916241349686315[220] = 0;
   out_3104916241349686315[221] = 0;
   out_3104916241349686315[222] = 0;
   out_3104916241349686315[223] = 0;
   out_3104916241349686315[224] = 0;
   out_3104916241349686315[225] = 0;
   out_3104916241349686315[226] = 0;
   out_3104916241349686315[227] = 0;
   out_3104916241349686315[228] = 1;
   out_3104916241349686315[229] = 0;
   out_3104916241349686315[230] = 0;
   out_3104916241349686315[231] = 0;
   out_3104916241349686315[232] = 0;
   out_3104916241349686315[233] = 0;
   out_3104916241349686315[234] = 0;
   out_3104916241349686315[235] = 0;
   out_3104916241349686315[236] = 0;
   out_3104916241349686315[237] = 0;
   out_3104916241349686315[238] = 0;
   out_3104916241349686315[239] = 0;
   out_3104916241349686315[240] = 0;
   out_3104916241349686315[241] = 0;
   out_3104916241349686315[242] = 0;
   out_3104916241349686315[243] = 0;
   out_3104916241349686315[244] = 0;
   out_3104916241349686315[245] = 0;
   out_3104916241349686315[246] = 0;
   out_3104916241349686315[247] = 1;
   out_3104916241349686315[248] = 0;
   out_3104916241349686315[249] = 0;
   out_3104916241349686315[250] = 0;
   out_3104916241349686315[251] = 0;
   out_3104916241349686315[252] = 0;
   out_3104916241349686315[253] = 0;
   out_3104916241349686315[254] = 0;
   out_3104916241349686315[255] = 0;
   out_3104916241349686315[256] = 0;
   out_3104916241349686315[257] = 0;
   out_3104916241349686315[258] = 0;
   out_3104916241349686315[259] = 0;
   out_3104916241349686315[260] = 0;
   out_3104916241349686315[261] = 0;
   out_3104916241349686315[262] = 0;
   out_3104916241349686315[263] = 0;
   out_3104916241349686315[264] = 0;
   out_3104916241349686315[265] = 0;
   out_3104916241349686315[266] = 1;
   out_3104916241349686315[267] = 0;
   out_3104916241349686315[268] = 0;
   out_3104916241349686315[269] = 0;
   out_3104916241349686315[270] = 0;
   out_3104916241349686315[271] = 0;
   out_3104916241349686315[272] = 0;
   out_3104916241349686315[273] = 0;
   out_3104916241349686315[274] = 0;
   out_3104916241349686315[275] = 0;
   out_3104916241349686315[276] = 0;
   out_3104916241349686315[277] = 0;
   out_3104916241349686315[278] = 0;
   out_3104916241349686315[279] = 0;
   out_3104916241349686315[280] = 0;
   out_3104916241349686315[281] = 0;
   out_3104916241349686315[282] = 0;
   out_3104916241349686315[283] = 0;
   out_3104916241349686315[284] = 0;
   out_3104916241349686315[285] = 1;
   out_3104916241349686315[286] = 0;
   out_3104916241349686315[287] = 0;
   out_3104916241349686315[288] = 0;
   out_3104916241349686315[289] = 0;
   out_3104916241349686315[290] = 0;
   out_3104916241349686315[291] = 0;
   out_3104916241349686315[292] = 0;
   out_3104916241349686315[293] = 0;
   out_3104916241349686315[294] = 0;
   out_3104916241349686315[295] = 0;
   out_3104916241349686315[296] = 0;
   out_3104916241349686315[297] = 0;
   out_3104916241349686315[298] = 0;
   out_3104916241349686315[299] = 0;
   out_3104916241349686315[300] = 0;
   out_3104916241349686315[301] = 0;
   out_3104916241349686315[302] = 0;
   out_3104916241349686315[303] = 0;
   out_3104916241349686315[304] = 1;
   out_3104916241349686315[305] = 0;
   out_3104916241349686315[306] = 0;
   out_3104916241349686315[307] = 0;
   out_3104916241349686315[308] = 0;
   out_3104916241349686315[309] = 0;
   out_3104916241349686315[310] = 0;
   out_3104916241349686315[311] = 0;
   out_3104916241349686315[312] = 0;
   out_3104916241349686315[313] = 0;
   out_3104916241349686315[314] = 0;
   out_3104916241349686315[315] = 0;
   out_3104916241349686315[316] = 0;
   out_3104916241349686315[317] = 0;
   out_3104916241349686315[318] = 0;
   out_3104916241349686315[319] = 0;
   out_3104916241349686315[320] = 0;
   out_3104916241349686315[321] = 0;
   out_3104916241349686315[322] = 0;
   out_3104916241349686315[323] = 1;
}
void h_4(double *state, double *unused, double *out_6638106921781301540) {
   out_6638106921781301540[0] = state[6] + state[9];
   out_6638106921781301540[1] = state[7] + state[10];
   out_6638106921781301540[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_7325035645690951992) {
   out_7325035645690951992[0] = 0;
   out_7325035645690951992[1] = 0;
   out_7325035645690951992[2] = 0;
   out_7325035645690951992[3] = 0;
   out_7325035645690951992[4] = 0;
   out_7325035645690951992[5] = 0;
   out_7325035645690951992[6] = 1;
   out_7325035645690951992[7] = 0;
   out_7325035645690951992[8] = 0;
   out_7325035645690951992[9] = 1;
   out_7325035645690951992[10] = 0;
   out_7325035645690951992[11] = 0;
   out_7325035645690951992[12] = 0;
   out_7325035645690951992[13] = 0;
   out_7325035645690951992[14] = 0;
   out_7325035645690951992[15] = 0;
   out_7325035645690951992[16] = 0;
   out_7325035645690951992[17] = 0;
   out_7325035645690951992[18] = 0;
   out_7325035645690951992[19] = 0;
   out_7325035645690951992[20] = 0;
   out_7325035645690951992[21] = 0;
   out_7325035645690951992[22] = 0;
   out_7325035645690951992[23] = 0;
   out_7325035645690951992[24] = 0;
   out_7325035645690951992[25] = 1;
   out_7325035645690951992[26] = 0;
   out_7325035645690951992[27] = 0;
   out_7325035645690951992[28] = 1;
   out_7325035645690951992[29] = 0;
   out_7325035645690951992[30] = 0;
   out_7325035645690951992[31] = 0;
   out_7325035645690951992[32] = 0;
   out_7325035645690951992[33] = 0;
   out_7325035645690951992[34] = 0;
   out_7325035645690951992[35] = 0;
   out_7325035645690951992[36] = 0;
   out_7325035645690951992[37] = 0;
   out_7325035645690951992[38] = 0;
   out_7325035645690951992[39] = 0;
   out_7325035645690951992[40] = 0;
   out_7325035645690951992[41] = 0;
   out_7325035645690951992[42] = 0;
   out_7325035645690951992[43] = 0;
   out_7325035645690951992[44] = 1;
   out_7325035645690951992[45] = 0;
   out_7325035645690951992[46] = 0;
   out_7325035645690951992[47] = 1;
   out_7325035645690951992[48] = 0;
   out_7325035645690951992[49] = 0;
   out_7325035645690951992[50] = 0;
   out_7325035645690951992[51] = 0;
   out_7325035645690951992[52] = 0;
   out_7325035645690951992[53] = 0;
}
void h_10(double *state, double *unused, double *out_7245991018613219639) {
   out_7245991018613219639[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_7245991018613219639[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_7245991018613219639[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_3241674189223813251) {
   out_3241674189223813251[0] = 0;
   out_3241674189223813251[1] = 9.8100000000000005*cos(state[1]);
   out_3241674189223813251[2] = 0;
   out_3241674189223813251[3] = 0;
   out_3241674189223813251[4] = -state[8];
   out_3241674189223813251[5] = state[7];
   out_3241674189223813251[6] = 0;
   out_3241674189223813251[7] = state[5];
   out_3241674189223813251[8] = -state[4];
   out_3241674189223813251[9] = 0;
   out_3241674189223813251[10] = 0;
   out_3241674189223813251[11] = 0;
   out_3241674189223813251[12] = 1;
   out_3241674189223813251[13] = 0;
   out_3241674189223813251[14] = 0;
   out_3241674189223813251[15] = 1;
   out_3241674189223813251[16] = 0;
   out_3241674189223813251[17] = 0;
   out_3241674189223813251[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_3241674189223813251[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_3241674189223813251[20] = 0;
   out_3241674189223813251[21] = state[8];
   out_3241674189223813251[22] = 0;
   out_3241674189223813251[23] = -state[6];
   out_3241674189223813251[24] = -state[5];
   out_3241674189223813251[25] = 0;
   out_3241674189223813251[26] = state[3];
   out_3241674189223813251[27] = 0;
   out_3241674189223813251[28] = 0;
   out_3241674189223813251[29] = 0;
   out_3241674189223813251[30] = 0;
   out_3241674189223813251[31] = 1;
   out_3241674189223813251[32] = 0;
   out_3241674189223813251[33] = 0;
   out_3241674189223813251[34] = 1;
   out_3241674189223813251[35] = 0;
   out_3241674189223813251[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_3241674189223813251[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_3241674189223813251[38] = 0;
   out_3241674189223813251[39] = -state[7];
   out_3241674189223813251[40] = state[6];
   out_3241674189223813251[41] = 0;
   out_3241674189223813251[42] = state[4];
   out_3241674189223813251[43] = -state[3];
   out_3241674189223813251[44] = 0;
   out_3241674189223813251[45] = 0;
   out_3241674189223813251[46] = 0;
   out_3241674189223813251[47] = 0;
   out_3241674189223813251[48] = 0;
   out_3241674189223813251[49] = 0;
   out_3241674189223813251[50] = 1;
   out_3241674189223813251[51] = 0;
   out_3241674189223813251[52] = 0;
   out_3241674189223813251[53] = 1;
}
void h_13(double *state, double *unused, double *out_3910102813404433436) {
   out_3910102813404433436[0] = state[3];
   out_3910102813404433436[1] = state[4];
   out_3910102813404433436[2] = state[5];
}
void H_13(double *state, double *unused, double *out_4112761820358619191) {
   out_4112761820358619191[0] = 0;
   out_4112761820358619191[1] = 0;
   out_4112761820358619191[2] = 0;
   out_4112761820358619191[3] = 1;
   out_4112761820358619191[4] = 0;
   out_4112761820358619191[5] = 0;
   out_4112761820358619191[6] = 0;
   out_4112761820358619191[7] = 0;
   out_4112761820358619191[8] = 0;
   out_4112761820358619191[9] = 0;
   out_4112761820358619191[10] = 0;
   out_4112761820358619191[11] = 0;
   out_4112761820358619191[12] = 0;
   out_4112761820358619191[13] = 0;
   out_4112761820358619191[14] = 0;
   out_4112761820358619191[15] = 0;
   out_4112761820358619191[16] = 0;
   out_4112761820358619191[17] = 0;
   out_4112761820358619191[18] = 0;
   out_4112761820358619191[19] = 0;
   out_4112761820358619191[20] = 0;
   out_4112761820358619191[21] = 0;
   out_4112761820358619191[22] = 1;
   out_4112761820358619191[23] = 0;
   out_4112761820358619191[24] = 0;
   out_4112761820358619191[25] = 0;
   out_4112761820358619191[26] = 0;
   out_4112761820358619191[27] = 0;
   out_4112761820358619191[28] = 0;
   out_4112761820358619191[29] = 0;
   out_4112761820358619191[30] = 0;
   out_4112761820358619191[31] = 0;
   out_4112761820358619191[32] = 0;
   out_4112761820358619191[33] = 0;
   out_4112761820358619191[34] = 0;
   out_4112761820358619191[35] = 0;
   out_4112761820358619191[36] = 0;
   out_4112761820358619191[37] = 0;
   out_4112761820358619191[38] = 0;
   out_4112761820358619191[39] = 0;
   out_4112761820358619191[40] = 0;
   out_4112761820358619191[41] = 1;
   out_4112761820358619191[42] = 0;
   out_4112761820358619191[43] = 0;
   out_4112761820358619191[44] = 0;
   out_4112761820358619191[45] = 0;
   out_4112761820358619191[46] = 0;
   out_4112761820358619191[47] = 0;
   out_4112761820358619191[48] = 0;
   out_4112761820358619191[49] = 0;
   out_4112761820358619191[50] = 0;
   out_4112761820358619191[51] = 0;
   out_4112761820358619191[52] = 0;
   out_4112761820358619191[53] = 0;
}
void h_14(double *state, double *unused, double *out_4449773984855147180) {
   out_4449773984855147180[0] = state[6];
   out_4449773984855147180[1] = state[7];
   out_4449773984855147180[2] = state[8];
}
void H_14(double *state, double *unused, double *out_8038919995723227328) {
   out_8038919995723227328[0] = 0;
   out_8038919995723227328[1] = 0;
   out_8038919995723227328[2] = 0;
   out_8038919995723227328[3] = 0;
   out_8038919995723227328[4] = 0;
   out_8038919995723227328[5] = 0;
   out_8038919995723227328[6] = 1;
   out_8038919995723227328[7] = 0;
   out_8038919995723227328[8] = 0;
   out_8038919995723227328[9] = 0;
   out_8038919995723227328[10] = 0;
   out_8038919995723227328[11] = 0;
   out_8038919995723227328[12] = 0;
   out_8038919995723227328[13] = 0;
   out_8038919995723227328[14] = 0;
   out_8038919995723227328[15] = 0;
   out_8038919995723227328[16] = 0;
   out_8038919995723227328[17] = 0;
   out_8038919995723227328[18] = 0;
   out_8038919995723227328[19] = 0;
   out_8038919995723227328[20] = 0;
   out_8038919995723227328[21] = 0;
   out_8038919995723227328[22] = 0;
   out_8038919995723227328[23] = 0;
   out_8038919995723227328[24] = 0;
   out_8038919995723227328[25] = 1;
   out_8038919995723227328[26] = 0;
   out_8038919995723227328[27] = 0;
   out_8038919995723227328[28] = 0;
   out_8038919995723227328[29] = 0;
   out_8038919995723227328[30] = 0;
   out_8038919995723227328[31] = 0;
   out_8038919995723227328[32] = 0;
   out_8038919995723227328[33] = 0;
   out_8038919995723227328[34] = 0;
   out_8038919995723227328[35] = 0;
   out_8038919995723227328[36] = 0;
   out_8038919995723227328[37] = 0;
   out_8038919995723227328[38] = 0;
   out_8038919995723227328[39] = 0;
   out_8038919995723227328[40] = 0;
   out_8038919995723227328[41] = 0;
   out_8038919995723227328[42] = 0;
   out_8038919995723227328[43] = 0;
   out_8038919995723227328[44] = 1;
   out_8038919995723227328[45] = 0;
   out_8038919995723227328[46] = 0;
   out_8038919995723227328[47] = 0;
   out_8038919995723227328[48] = 0;
   out_8038919995723227328[49] = 0;
   out_8038919995723227328[50] = 0;
   out_8038919995723227328[51] = 0;
   out_8038919995723227328[52] = 0;
   out_8038919995723227328[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_8846465336200542325) {
  err_fun(nom_x, delta_x, out_8846465336200542325);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_904878762552493072) {
  inv_err_fun(nom_x, true_x, out_904878762552493072);
}
void pose_H_mod_fun(double *state, double *out_8522983127573850096) {
  H_mod_fun(state, out_8522983127573850096);
}
void pose_f_fun(double *state, double dt, double *out_611896847437543302) {
  f_fun(state,  dt, out_611896847437543302);
}
void pose_F_fun(double *state, double dt, double *out_3104916241349686315) {
  F_fun(state,  dt, out_3104916241349686315);
}
void pose_h_4(double *state, double *unused, double *out_6638106921781301540) {
  h_4(state, unused, out_6638106921781301540);
}
void pose_H_4(double *state, double *unused, double *out_7325035645690951992) {
  H_4(state, unused, out_7325035645690951992);
}
void pose_h_10(double *state, double *unused, double *out_7245991018613219639) {
  h_10(state, unused, out_7245991018613219639);
}
void pose_H_10(double *state, double *unused, double *out_3241674189223813251) {
  H_10(state, unused, out_3241674189223813251);
}
void pose_h_13(double *state, double *unused, double *out_3910102813404433436) {
  h_13(state, unused, out_3910102813404433436);
}
void pose_H_13(double *state, double *unused, double *out_4112761820358619191) {
  H_13(state, unused, out_4112761820358619191);
}
void pose_h_14(double *state, double *unused, double *out_4449773984855147180) {
  h_14(state, unused, out_4449773984855147180);
}
void pose_H_14(double *state, double *unused, double *out_8038919995723227328) {
  H_14(state, unused, out_8038919995723227328);
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
