import help_functions.floodlight_code as floodlight_code
# import plot_functions.plot_phases as plot_phases
import variables.data_variables as dv

# plot_phases.plot_phases(23400263, dv.Approach.RULE_BASED)
# plot_phases.plotEvents(23400263)
match_ids_20_21 = [
    23400263, 23400265, 23400267, 23400271, 23400275, 23400277, 23400297,
    23400303, 23400305, 23400307, 23400311, 23400315, 23400319, 23400321,
    23400325, 23400339, 23400341, 23400343, 23400345, 23400349, 23400355,
    23400367, 23400369, 23400373, 23400385, 23400389, 23400397, 23400403,
    23400415, 23400419, 23400431, 23400439,
    23400433, 23400429, 23400441,
    23400447, 23400445, 23400459, 23400473, 24605004, 23400471, 23400479,
    23400467, 23400485, 23400487, 23400481, 23400793,
    23400507, 23400511, 23400517, 23400513, 23400525, 23400527, 23400605,
    23400539, 23400523, 23400551, 23400545, 23400553, 23400557, 23400563,
    23400565, 23400567, 23400579, 23400593, 23400619, 23400603, 23400605,
    23400507, 23400511, 23400517, 23400513, 23400525, 23400527, 23400539,
    23400523, 23400551, 23400545, 23400553, 23400557, 23400563, 23400565,
    23400567, 23400579, 23400593, 23400619, 23400603, 23400629,
    23400631, 25825972, 23400633, 25318658, 25702920, 25679964, 24481658,
    23400649, 23400651, 23400647, 23400659, 23400677, 23400663, 23400665,
    23400667, 23400671, 23400691, 23400699, 23400687, 25463968, 23400705,
    23400707, 23400717, 23400947, 23400727, 23400729, 23400745, 23400885,
    23400743, 23400757, 23400767, 23400769, 23400779, 23400771,
    23400765, 23400783, 23400799, 23400789, 26666794, 26666166, 23400809,
    23400811, 23400819, 23400805, 23400807, 23400831, 23400837, 23400839,
    23400823, 23400827, 23400845, 23400849, 23400851, 23400853, 25562234,
    27131492, 27131532, 27131424, 27219362, 27131536, 27219364, 27131528,
    23400871, 23400877, 23400867, 23400879, 23400883, 23400889, 23400887,
    23400891, 23400893, 23400913, 23400909, 23400905, 23400901, 27396646,
    27373216, 23400933, 23400931, 23400939, 23400935, 23400929, 23400951,
    23400949, 23400973, 23400979, 23400971, 23400993, 23400989, 23400991,
    23400987, 23401015, 23401011, 23401009, 23401007
]
match_ids_20_21_not_working = [23400749]

for match_id in match_ids_20_21:
    floodlight_code.approach_plot(match_id, dv.Approach.NONE)

# floodlight_code.approach_plot(23400439, dv.Approach.POS_RB)


# # 23400307 THW Kiel_HSG Wetzlar 10.10.20

# floodlight_code.approach_plot(23400307, dv.Approach.NONE)
# floodlight_code.approach_plot(23400307, dv.Approach.BASELINE)
# floodlight_code.approach_plot(23400307, dv.Approach.RULE_BASED)
# floodlight_code.approach_plot(23400307, dv.Approach.POS_DATA)
# floodlight_code.approach_plot(23400307, dv.Approach.POS_CORRECTION)
# floodlight_code.approach_plot(23400307, dv.Approach.POS_RB)
# floodlight_code.approach_plot(23400307, dv.Approach.COST_BASED)
# # floodlight_code.approach_plot(23400307, dv.Approach.COST_BASED_COR)
# # floodlight_code.approach_plot(23400307, dv.Approach.COST_BASED_RB)

# # 23400263 TSV GWD Minden_TSV Hannover-Burgdorf 01.10.20

# floodlight_code.approach_plot(23400263, dv.Approach.NONE)
# floodlight_code.approach_plot(23400263, dv.Approach.BASELINE)
# floodlight_code.approach_plot(23400263, dv.Approach.RULE_BASED)
# floodlight_code.approach_plot(23400263, dv.Approach.POS_DATA)
# floodlight_code.approach_plot(23400263, dv.Approach.POS_CORRECTION)
# floodlight_code.approach_plot(23400263, dv.Approach.POS_RB)
# floodlight_code.approach_plot(23400263, dv.Approach.COST_BASED)
# # floodlight_code.approach_plot(23400263, dv.Approach.COST_BASED_COR)
# # floodlight_code.approach_plot(23400263, dv.Approach.COST_BASED_RB)

# # 23400275 Rhein-Neckar Löwen_TVB Stuttgart 04.10.20

# floodlight_code.approach_plot(23400275, dv.Approach.NONE)
# floodlight_code.approach_plot(23400275, dv.Approach.BASELINE)
# floodlight_code.approach_plot(23400275, dv.Approach.RULE_BASED)
# floodlight_code.approach_plot(23400275, dv.Approach.POS_DATA)
# floodlight_code.approach_plot(23400275, dv.Approach.POS_CORRECTION)
# floodlight_code.approach_plot(23400275, dv.Approach.POS_RB)
# floodlight_code.approach_plot(23400275, dv.Approach.COST_BASED)

# # 23400277 HSG Wetzlar_SG Flensburg-Handewitt 04.10.20

# floodlight_code.approach_plot(23400277, dv.Approach.NONE)
# floodlight_code.approach_plot(23400277, dv.Approach.BASELINE)
# floodlight_code.approach_plot(23400277, dv.Approach.RULE_BASED)
# floodlight_code.approach_plot(23400277, dv.Approach.POS_DATA)
# floodlight_code.approach_plot(23400277, dv.Approach.POS_CORRECTION)
# floodlight_code.approach_plot(23400277, dv.Approach.POS_RB)
# floodlight_code.approach_plot(23400277, dv.Approach.COST_BASED)
# # floodlight_code.approach_plot(23400277, dv.Approach.COST_BASED_COR)
# # floodlight_code.approach_plot(23400277, dv.Approach.COST_BASED_RB)

# # 23400267  HSC 2000 Coburg_TBV Lemgo Lippe 01.10.20

# floodlight_code.approach_plot(23400267, dv.Approach.NONE)
# floodlight_code.approach_plot(23400267, dv.Approach.BASELINE)
# floodlight_code.approach_plot(23400267, dv.Approach.RULE_BASED)
# floodlight_code.approach_plot(23400267, dv.Approach.POS_DATA)
# floodlight_code.approach_plot(23400267, dv.Approach.POS_CORRECTION)
# floodlight_code.approach_plot(23400267, dv.Approach.POS_RB)
# floodlight_code.approach_plot(23400267, dv.Approach.COST_BASED)
# # # # Keine Passende Phase gefunden Fehler
# # floodlight_code.approach_plot(23400267, dv.Approach.COST_BASED_COR)
# # floodlight_code.approach_plot(23400267, dv.Approach.COST_BASED_RB)


# # 23400319 BHC NordhornLingen 11.10.20

# floodlight_code.approach_plot(23400319, dv.Approach.NONE)
# floodlight_code.approach_plot(23400319, dv.Approach.BASELINE)
# floodlight_code.approach_plot(23400319, dv.Approach.RULE_BASED)
# floodlight_code.approach_plot(23400319, dv.Approach.POS_DATA)
# floodlight_code.approach_plot(23400319, dv.Approach.POS_CORRECTION)
# floodlight_code.approach_plot(23400319, dv.Approach.POS_RB)
# floodlight_code.approach_plot(23400319, dv.Approach.COST_BASED)
# # floodlight_code.approach_plot(23400319, dv.Approach.COST_BASED_COR)
# # floodlight_code.approach_plot(23400319, dv.Approach.COST_BASED_RB)

# # 23400311 Füchse Berlin SC DHFK Leipzig 11.10.20

# floodlight_code.approach_plot(23400311, dv.Approach.NONE)
# floodlight_code.approach_plot(23400311, dv.Approach.BASELINE)
# # floodlight_code.approach_plot(23400311, dv.Approach.RULE_BASED)
# floodlight_code.approach_plot(23400311, dv.Approach.POS_DATA)
# # # #  Ball data. N == 3 and both (0 und 1) data are valid in 10 frames
# floodlight_code.approach_plot(23400311, dv.Approach.POS_CORRECTION)
# floodlight_code.approach_plot(23400311, dv.Approach.POS_RB)
# floodlight_code.approach_plot(23400311, dv.Approach.COST_BASED)
# # # floodlight_code.approach_plot(23400311, dv.Approach.COST_BASED_COR)
# # # floodlight_code.approach_plot(23400311, dv.Approach.COST_BASED_RB)


# # 23400321 Rhein-Neckar Löwen_SC DHfK Leipzig 15.10.20

# # floodlight_code.approach_plot(23400321, dv.Approach.NONE)
# # floodlight_code.approach_plot(23400321, dv.Approach.BASELINE)
# # floodlight_code.approach_plot(23400321, dv.Approach.RULE_BASED)
# floodlight_code.approach_plot(23400321, dv.Approach.POS_DATA)
# # floodlight_code.approach_plot(23400321, dv.Approach.POS_CORRECTION)
# floodlight_code.approach_plot(23400321, dv.Approach.POS_RB)
# floodlight_code.approach_plot(23400321, dv.Approach.COST_BASED)
# # # floodlight_code.approach_plot(23400321, dv.Approach.COST_BASED_COR)
# # # floodlight_code.approach_plot(23400321, dv.Approach.COST_BASED_RB)


# # # 23400303 TSV Hannover-Burgdorf_HSC 2000 Coburg 08.10.20

# # floodlight_code.approach_plot(23400303, dv.Approach.NONE)
# # floodlight_code.approach_plot(23400303, dv.Approach.BASELINE)
# # floodlight_code.approach_plot(23400303, dv.Approach.RULE_BASED)
# floodlight_code.approach_plot(23400303, dv.Approach.POS_DATA)
# # floodlight_code.approach_plot(23400303, dv.Approach.POS_CORRECTION)
# # floodlight_code.approach_plot(23400303, dv.Approach.POS_RB)
# # floodlight_code.approach_plot(23400303, dv.Approach.COST_BASED)
# # # floodlight_code.approach_plot(23400303, dv.Approach.COST_BASED_COR)
# # # floodlight_code.approach_plot(23400303, dv.Approach.COST_BASED_RB)

# # # 23400315 TUSEM Essen_Rhein-Neckar Löwen 11.10.20

# # floodlight_code.approach_plot(23400315, dv.Approach.NONE)
# # floodlight_code.approach_plot(23400315, dv.Approach.BASELINE)
# # floodlight_code.approach_plot(23400315, dv.Approach.RULE_BASED)
# floodlight_code.approach_plot(23400315, dv.Approach.POS_DATA)
# # floodlight_code.approach_plot(23400315, dv.Approach.POS_CORRECTION)
# # floodlight_code.approach_plot(23400315, dv.Approach.POS_RB)
# floodlight_code.approach_plot(23400315, dv.Approach.COST_BASED)
# # # floodlight_code.approach_plot(23400315, dv.Approach.COST_BASED_COR)
# # # floodlight_code.approach_plot(23400315, dv.Approach.COST_BASED_RB)

# # 311, 315, 321, 263
