# test_runner.py

import os
from pathlib import Path
from cocotb.runner import get_runner


def test_systolic_pe_runner():
    sim = os.getenv("SIM", "icarus")

    proj_path = Path(__file__).resolve().parent

    # Include both design and testbench files
    sources = [
        proj_path / "systolic_pe.v",
        proj_path / "systolic_pe_tb.v"
    ]

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="systolic_pe_tb",  # Use testbench as top level
        parameters={}  # Parameters now defined in testbench
    )

    runner.test(
        hdl_toplevel="systolic_pe_tb",
        test_module="test_systolic_pe",
    )


if __name__ == "__main__":
    test_systolic_pe_runner()