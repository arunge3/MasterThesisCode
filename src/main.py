import help_functions.floodlight_code as floodlight_code
# import plot_functions.plot_phases as plot_phases
import variables.data_variables as dv

# plot_phases.plot_phases(23400263, dv.Approach.RULE_BASED)
# plot_phases.plotEvents(23400263)
floodlight_code.plot_phases(23400275, dv.Approach.NONE)

# floodlight_code.plot_phases(23400275, dv.Approach.BASELINE)

# floodlight_code.plot_phases(23400275, dv.Approach.RULE_BASED)

# floodlight_code.plot_phases(23400275, dv.Approach.POS_DATA)
# floodlight_code.plot_phases(23400275, dv.Approach.POS_CORRECTION)
# floodlight_code.plot_phases(23400275, dv.Approach.POS_RB)

# floodlight_code.plot_phases(23400275, dv.Approach.COST_BASED)
# floodlight_code.plot_phases(23400275, dv.Approach.COST_BASED_COR)
# floodlight_code.plot_phases(23400275, dv.Approach.COST_BASED_RB)
