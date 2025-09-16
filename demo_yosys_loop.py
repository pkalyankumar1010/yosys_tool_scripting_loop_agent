#!/usr/bin/env python3
"""
Demo script for Yosys Loop Agent
This script demonstrates how to use the Yosys script generation and execution loop.
"""

import os
import sys
from yosys_loop_agent import run_yosys_script_loop

def main():
    """Main demo function"""
    print("="*60)
    print("YOSYS LOOP AGENT DEMO")
    print("="*60)
    
    # Check if test files exist
    verilog_path = "yosys_test/counter.v"
    sdc_path = "yosys_test/counter.sdc"
    
    if not os.path.exists(verilog_path):
        print(f"❌ Verilog file not found: {verilog_path}")
        print("Please ensure the test files exist before running the demo.")
        return False
    
    if not os.path.exists(sdc_path):
        print(f"❌ SDC file not found: {sdc_path}")
        print("Please ensure the test files exist before running the demo.")
        return False
    
    print(f"✅ Found Verilog file: {verilog_path}")
    print(f"✅ Found SDC file: {sdc_path}")
    
    # Run the Yosys script loop
    print("\nStarting Yosys script generation and execution loop...")
    print("This will attempt to generate and run Yosys scripts until success or max iterations.")
    
    try:
        result = run_yosys_script_loop(
            verilog_path=verilog_path,
            sdc_path=sdc_path,
            max_iterations=3
        )
        
        if result["feedback"] == "success":
            print("\n🎉 Demo completed successfully!")
            print(f"The Yosys script was generated and executed successfully in {result['iteration']} iterations.")
            
            # Check if output file was created
            output_file = result.get("output_file", "")
            if output_file and os.path.exists(output_file):
                print(f"✅ Output file created: {output_file}")
            else:
                print("⚠️  Output file not found (may have been created with a different name)")
            
            return True
        else:
            print(f"\n⚠️  Demo completed with status: {result['feedback']}")
            print(f"Iterations used: {result['iteration']}")
            return False
            
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        return False

def interactive_demo():
    """Interactive demo where user can specify their own files"""
    print("\n" + "="*60)
    print("INTERACTIVE DEMO")
    print("="*60)
    
    print("Enter your Verilog and SDC file paths (or press Enter to use defaults):")
    
    verilog_path = input(f"Verilog file path [yosys_test/counter.v]: ").strip()
    if not verilog_path:
        verilog_path = "yosys_test/counter.v"
    
    sdc_path = input(f"SDC file path [yosys_test/counter.sdc]: ").strip()
    if not sdc_path:
        sdc_path = "yosys_test/counter.sdc"
    
    max_iterations = input("Max iterations [3]: ").strip()
    if not max_iterations:
        max_iterations = 3
    else:
        try:
            max_iterations = int(max_iterations)
        except ValueError:
            print("Invalid number, using default of 3")
            max_iterations = 3
    
    print(f"\nRunning with:")
    print(f"- Verilog file: {verilog_path}")
    print(f"- SDC file: {sdc_path}")
    print(f"- Max iterations: {max_iterations}")
    
    try:
        result = run_yosys_script_loop(
            verilog_path=verilog_path,
            sdc_path=sdc_path,
            max_iterations=max_iterations
        )
        
        if result["feedback"] == "success":
            print("\n🎉 Interactive demo completed successfully!")
        else:
            print(f"\n⚠️  Interactive demo completed with status: {result['feedback']}")
            
    except Exception as e:
        print(f"\n❌ Interactive demo failed with error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
    else:
        success = main()
        if success:
            print("\n" + "="*60)
            print("DEMO COMPLETED SUCCESSFULLY")
            print("="*60)
            print("The Yosys Loop Agent is working correctly!")
            print("You can now use it to generate and execute Yosys scripts.")
            print("\nTo run an interactive demo with your own files, use:")
            print("python demo_yosys_loop.py --interactive")
        else:
            print("\n" + "="*60)
            print("DEMO COMPLETED WITH ISSUES")
            print("="*60)
            print("Please check the output above for details.")
