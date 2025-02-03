import help_functions.floodlight_code as floodlight_code
# import plot_functions.plot_phases as plot_phases
import variables.data_variables as dv

# plot_phases.plot_phases(23400263, dv.Approach.RULE_BASED)
# plot_phases.plotEvents(23400263)
floodlight_code.plot_phases(23400263, dv.Approach.POS_DATA)
