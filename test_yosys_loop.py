#!/usr/bin/env python3
"""
Test script for Yosys Loop Agent
This script tests the looping mechanism for Yosys script generation and execution.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yosys_loop_agent import run_yosys_script_loop, YosysAgentState, graph

def check_yosys_installation():
    """Check if Yosys is installed and accessible"""
    try:
        result = subprocess.run(['yosys', '-V'], capture_output=True, text=True, check=True)
        print(f"✅ Yosys is installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Yosys is not installed or not in PATH")
        print("Please install Yosys first:")
        print("  - Ubuntu/Debian: sudo apt-get install yosys")
        print("  - macOS: brew install yosys")
        print("  - Or download from: https://github.com/YosysHQ/yosys")
        return False

def check_test_files():
    """Check if test files exist"""
    verilog_path = "yosys_test/counter.v"
    sdc_path = "yosys_test/counter.sdc"
    
    print("Checking test files:")
    print(f"  - {verilog_path}: {'✅' if os.path.exists(verilog_path) else '❌'}")
    print(f"  - {sdc_path}: {'✅' if os.path.exists(sdc_path) else '❌'}")
    
    if not os.path.exists(verilog_path) or not os.path.exists(sdc_path):
        print("\nCreating test files...")
        create_test_files()
        return True
    
    return True

def create_test_files():
    """Create test files if they don't exist"""
    os.makedirs("yosys_test", exist_ok=True)
    
    # Create counter.v
    counter_v = """module counter (
    input wire clk,
    input wire rst_n,
    output reg [3:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        count <= 4'b0000;
    else
        count <= count + 1;
end

endmodule
"""
    
    # Create counter.sdc
    counter_sdc = """# Clock definition
create_clock -name clk -period 10.0 [get_ports clk]

# Input delay
set_input_delay 2.0 -clock clk [get_ports rst_n]

# Output delay
set_output_delay 2.0 -clock clk [get_ports count[*]]

# Max transition and load constraints (optional, but useful)
set_max_delay 8.0 -from [get_ports clk] -to [get_ports count[*]]
set_max_transition 0.5 [get_ports count[*]]
set_load 0.1 [get_ports count[*]]
"""
    
    with open("yosys_test/counter.v", "w") as f:
        f.write(counter_v)
    
    with open("yosys_test/counter.sdc", "w") as f:
        f.write(counter_sdc)
    
    print("✅ Test files created successfully")

def test_state_initialization():
    """Test the state initialization"""
    print("\n" + "="*50)
    print("TESTING STATE INITIALIZATION")
    print("="*50)
    
    initial_state = {
        "verilog_path": "yosys_test/counter.v",
        "sdc_path": "yosys_test/counter.sdc",
        "iteration": 0,
        "max_iterations": 3,
        "current_script": "",
        "last_script": None,
        "execution_log": "",
        "last_execution_log": None,
        "feedback": None,
        "game_over": False,
        "message_history": [],
        "output_file": "",
        "error_details": ""
    }
    
    # Test the graph with initial state
    try:
        result = graph.invoke(initial_state)
        print("✅ State initialization test passed")
        print(f"Final iteration: {result['iteration']}")
        print(f"Final feedback: {result['feedback']}")
        print(f"Game over: {result['game_over']}")
        return True
    except Exception as e:
        print(f"❌ State initialization test failed: {e}")
        return False

def test_script_extraction():
    """Test script extraction from LLM responses"""
    print("\n" + "="*50)
    print("TESTING SCRIPT EXTRACTION")
    print("="*50)
    
    from yosys_loop_agent import extract_script_from_text
    
    # Test cases
    test_cases = [
        {
            "input": "Generated Yosys script:\nread_verilog counter.v\nsynth\nwrite_verilog output.v",
            "expected": "read_verilog counter.v\nsynth\nwrite_verilog output.v"
        },
        {
            "input": "```\nread_verilog counter.v\nsynth\nwrite_verilog output.v\n```",
            "expected": "read_verilog counter.v\nsynth\nwrite_verilog output.v"
        },
        {
            "input": "Here's the script:\nread_verilog counter.v\nsynth\nwrite_verilog output.v\nThat should work!",
            "expected": "read_verilog counter.v\nsynth\nwrite_verilog output.v"
        }
    ]
    
    all_passed = True
    for i, test_case in enumerate(test_cases):
        result = extract_script_from_text(test_case["input"])
        if result.strip() == test_case["expected"].strip():
            print(f"✅ Test case {i+1} passed")
        else:
            print(f"❌ Test case {i+1} failed")
            print(f"  Expected: {test_case['expected']}")
            print(f"  Got: {result}")
            all_passed = False
    
    return all_passed

def test_yosys_execution():
    """Test Yosys execution with a simple script"""
    print("\n" + "="*50)
    print("TESTING YOSYS EXECUTION")
    print("="*50)
    
    # Create a simple test script
    test_script = """read_verilog yosys_test/counter.v
synth
write_verilog test_output.v
stat
"""
    
    try:
        # Create a temporary file to store the Yosys script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ys', delete=False) as temp_file:
            temp_file.write(test_script)
            temp_script_path = temp_file.name
        
        try:
            # Run Yosys with the temporary script file
            result = subprocess.run(
                ['yosys', temp_script_path], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=30
            )
            
            # Clean up the temporary file
            os.unlink(temp_script_path)
            
            print("✅ Yosys execution test passed")
            print(f"STDOUT length: {len(result.stdout)} characters")
            if result.stderr:
                print(f"STDERR length: {len(result.stderr)} characters")
            
            # Check if output file was created
            if os.path.exists("test_output.v"):
                print("✅ Output file created successfully")
                os.remove("test_output.v")  # Clean up
            else:
                print("⚠️  Output file not created")
            
            return True
            
        except subprocess.TimeoutExpired:
            os.unlink(temp_script_path)
            print("❌ Yosys execution timed out")
            return False
            
        except subprocess.CalledProcessError as e:
            os.unlink(temp_script_path)
            print(f"❌ Yosys execution failed: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Yosys execution test failed: {e}")
        return False

def test_full_loop():
    """Test the full loop with limited iterations"""
    print("\n" + "="*50)
    print("TESTING FULL LOOP")
    print("="*50)
    
    try:
        result = run_yosys_script_loop(
            verilog_path="yosys_test/counter.v",
            sdc_path="yosys_test/counter.sdc",
            max_iterations=2  # Limit iterations for testing
        )
        
        print("✅ Full loop test completed")
        print(f"Final state: {result['feedback']}")
        print(f"Iterations used: {result['iteration']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full loop test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("YOSYS LOOP AGENT TEST SUITE")
    print("="*60)
    
    tests = [
        ("Yosys Installation Check", check_yosys_installation),
        ("Test Files Check", check_test_files),
        ("State Initialization", test_state_initialization),
        ("Script Extraction", test_script_extraction),
        ("Yosys Execution", test_yosys_execution),
        ("Full Loop Test", test_full_loop),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Yosys loop agent is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
