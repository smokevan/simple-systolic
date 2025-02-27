# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# test_systolic_pe.py

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
from cocotb.queue import Queue
from cocotb.result import TestError


class HandshakeDriver:
    """Helper class to drive the handshaking interface"""
    
    def __init__(self, clk, stb, busy):
        self.clk = clk
        self.stb = stb
        self.busy = busy
        
    async def send_data(self, wait_for_ready=True):
        """Drive strobe and wait for not busy if requested"""
        self.stb.value = 1
        
        if wait_for_ready:
            while True:
                await RisingEdge(self.clk)
                if self.busy.value == 0:
                    break
        else:
            await RisingEdge(self.clk)
            
    async def clear_strobe(self):
        """Clear the strobe signal"""
        self.stb.value = 0
        await RisingEdge(self.clk)


@cocotb.test()
@cocotb.test()
async def test_basic_mac_operation(dut):
    """Test basic MAC functionality with simple values"""
    
    # Create and start the clock
    clock = Clock(dut.clk, 10, units="step")
    cocotb.start_soon(clock.start())
    
    # Reset the design
    dut.reset.value = 1
    dut.i_stb.value = 0
    dut.i_busy.value = 0
    dut.data_in.value = 0
    dut.weight_in.value = 0
    dut.acc_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.reset.value = 0
    await ClockCycles(dut.clk, 1)
    
    # Create input driver
    input_driver = HandshakeDriver(dut.clk, dut.i_stb, dut.o_busy)
    
    # Test cases
    test_cases = [
        (5, 4, 0),     # 5*4 + 0 = 20
        (10, 3, 5),    # 10*3 + 5 = 35
        (7, 8, 10),    # 7*8 + 10 = 66
    ]
    
    # Run test cases
    for data, weight, acc in test_cases:
        dut._log.info(f"Testing MAC: {data} * {weight} + {acc}")
        
        # Set input values
        dut.data_in.value = data
        dut.weight_in.value = weight
        dut.acc_in.value = acc
        
        # Drive handshake signals
        dut._log.info("Sending data")
        await input_driver.send_data()
        dut._log.info(f"After send: o_busy={dut.o_busy.value}")
        await input_driver.clear_strobe()
        
        # Wait for result to be valid
        cycles_waited = 0
        max_wait_cycles = 20  # Set a reasonable timeout
        
        while cycles_waited < max_wait_cycles:
            await RisingEdge(dut.clk)
            cycles_waited += 1
            
            # Log current state for debugging
            dut._log.info(f"Cycle {cycles_waited}: o_stb={dut.o_stb.value}, o_busy={dut.o_busy.value}, acc_out={int(dut.acc_out.value)}")
            
            if dut.o_stb.value == 1:
                break
        
        if cycles_waited >= max_wait_cycles:
            raise TestError(f"Timeout waiting for o_stb to assert after {max_wait_cycles} cycles")
        
        # Calculate expected result
        expected = acc + (data * weight)
        
        # Check result
        actual = int(dut.acc_out.value)
        dut._log.info(f"Expected: {expected}, Actual: {actual}")
        
        assert actual == expected, \
            f"MAC result incorrect. Expected {expected}, got {actual}"
        
        # Accept the output
        dut.i_busy.value = 0
        await RisingEdge(dut.clk)
        
    dut._log.info("All basic MAC tests passed!")

@cocotb.test()
async def test_pipeline_flow(dut):
    """Test continuous flow of data through the pipeline with better diagnostics"""
    
    # Create and start the clock
    clock = Clock(dut.clk, 10, units="step")
    cocotb.start_soon(clock.start())
    
    # Reset the design
    dut._log.info("Resetting the design")
    dut.reset.value = 1
    dut.i_stb.value = 0
    dut.i_busy.value = 0
    await ClockCycles(dut.clk, 5)
    dut.reset.value = 0
    await ClockCycles(dut.clk, 1)
    
    # Simplified test - just focus on getting one value through first
    data1, weight1, acc1 = 5, 4, 0
    expected1 = acc1 + (data1 * weight1)
    
    dut._log.info(f"Test 1: data={data1}, weight={weight1}, acc={acc1}, expected={expected1}")
    
    # Set input values
    dut.data_in.value = data1
    dut.weight_in.value = weight1
    dut.acc_in.value = acc1
    
    # Drive strobe signal
    dut._log.info("Asserting i_stb")
    dut.i_stb.value = 1
    
    # Wait until o_busy is low
    timeout = 0
    while dut.o_busy.value == 1 and timeout < 10:
        await RisingEdge(dut.clk)


@cocotb.test()
async def test_realistic_backpressure(dut):
    """Test how the PE handles backpressure in realistic systolic array scenarios"""
    
    # Create and start the clock
    clock = Clock(dut.clk, 10, units="step")
    cocotb.start_soon(clock.start())
    
    # Reset the design
    dut.reset.value = 1
    dut.i_stb.value = 0
    dut.i_busy.value = 0
    await ClockCycles(dut.clk, 5)
    dut.reset.value = 0
    await ClockCycles(dut.clk, 1)
    
    # Scenario 1: Module is busy processing first input and rejects second input
    dut._log.info("Scenario 1: Testing when PE is busy with first operation")
    
    # Send first input
    data1, weight1, acc1 = 5, 4, 0
    expected1 = acc1 + (data1 * weight1)
    
    dut.data_in.value = data1
    dut.weight_in.value = weight1
    dut.acc_in.value = acc1
    dut.i_stb.value = 1
    
    # Wait for module to accept data and set o_busy
    # This might take multiple cycles depending on your design
    cycles_waited = 0
    max_wait = 10
    while cycles_waited < max_wait:
        await RisingEdge(dut.clk)
        cycles_waited += 1
        dut._log.info(f"Cycle {cycles_waited}: o_busy = {dut.o_busy.value}")
        if dut.o_busy.value == 1:
            break
    
    assert cycles_waited < max_wait, "Timeout waiting for o_busy to be asserted"
    dut._log.info(f"Module asserted o_busy after {cycles_waited} cycles")
    
    # Clear input strobe after module has accepted the data
    dut.i_stb.value = 0
    await RisingEdge(dut.clk)
    
    # Try to send second input immediately (should be rejected due to o_busy)
    data2, weight2, acc2 = 7, 6, 10
    
    dut.data_in.value = data2
    dut.weight_in.value = weight2
    dut.acc_in.value = acc2
    dut.i_stb.value = 1
    
    # Check module keeps busy flag high
    await RisingEdge(dut.clk)
    assert dut.o_busy.value == 1, "o_busy should remain high, rejecting second input"
    dut._log.info("Module correctly maintained o_busy when second input attempted")
    
    # Clear second input attempt
    dut.i_stb.value = 0
    
    # Wait for first result
    cycles = 0
    while cycles < 20:
        await RisingEdge(dut.clk)
        cycles += 1
        if dut.o_stb.value == 1:
            break
    
    # Check first result
    assert dut.o_stb.value == 1, "o_stb should be asserted when result is ready"
    try:
        actual = int(dut.acc_out.value)
        assert actual == expected1, f"Expected {expected1}, got {actual}"
        dut._log.info(f"First result correct: {actual}")
    except ValueError:
        assert False, "Output contains X values"
    
    # Scenario 2: Module completes first operation before accepting second
    dut._log.info("Scenario 2: Testing sequential operations with output acceptance")
    
    # Accept the first output
    dut.i_busy.value = 0
    await RisingEdge(dut.clk)
    
    # Check module is ready for next input
    await RisingEdge(dut.clk)
    assert dut.o_busy.value == 0, "Module should be ready for next input after output accepted"
    dut._log.info("Module correctly ready for second input after first output accepted")
    
    # Send second input
    dut.data_in.value = data2
    dut.weight_in.value = weight2
    dut.acc_in.value = acc2
    dut.i_stb.value = 1
    
    # Wait for module to accept data
    await RisingEdge(dut.clk)
    dut.i_stb.value = 0
    
    # Wait for second result
    cycles = 0
    while cycles < 20:
        await RisingEdge(dut.clk)
        cycles += 1
        if dut.o_stb.value == 1:
            break
    
    # Check second result
    expected2 = acc2 + (data2 * weight2)
    try:
        actual = int(dut.acc_out.value)
        assert actual == expected2, f"Expected {expected2}, got {actual}"
        dut._log.info(f"Second result correct: {actual}")
    except ValueError:
        assert False, "Output contains X values"
    
    dut._log.info("Realistic backpressure test passed!")