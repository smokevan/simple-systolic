# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# Makefile

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/systolic_pe.v
# use VHDL_SOURCES for VHDL files


# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = systolic_pe

# MODULE is the basename of the Python test file
MODULE = test_systolic_pe

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
