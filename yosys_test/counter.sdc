# Clock definition
create_clock -name clk -period 10.0 [get_ports clk]

# Input delay
set_input_delay 2.0 -clock clk [get_ports rst_n]

# Output delay
set_output_delay 2.0 -clock clk [get_ports count[*]]

# Max transition and load constraints (optional, but useful)
set_max_delay 8.0 -from [get_ports clk] -to [get_ports count[*]]
set_max_transition 0.5 [get_ports count[*]]
set_load 0.1 [get_ports count[*]]
