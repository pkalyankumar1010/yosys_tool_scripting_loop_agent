# Yosys Loop Agent

A looping mechanism similar to the number guessing game for generating and executing Yosys synthesis scripts until they succeed or reach maximum iterations.

## Overview

This implementation creates an intelligent loop that:
1. Generates Yosys synthesis scripts using LLM
2. Executes the scripts and captures results
3. Analyzes failures and generates improved scripts
4. Continues until success or max iterations reached

## Files Created

### Core Implementation
- **`yosys_loop_agent.py`** - Main implementation with the looping mechanism
- **`test_yosys_loop.py`** - Comprehensive test suite
- **`demo_yosys_loop.py`** - Demo script showing usage

### Test Files
- **`yosys_test/counter.v`** - Sample Verilog counter module
- **`yosys_test/counter.sdc`** - Sample SDC constraints file

## Key Features

### 1. State Management
Similar to the number guessing game, the system maintains state including:
- Current iteration count
- Maximum iterations allowed
- Previous script and execution log
- Error details and feedback
- Success/failure status

### 2. Intelligent Script Generation
- Uses LLM to generate Yosys scripts based on Verilog and SDC files
- Learns from previous failures to improve subsequent scripts
- Extracts only valid Yosys commands from LLM responses

### 3. Error Analysis and Correction
- Captures execution logs and error details
- Provides feedback to LLM for script improvement
- Handles common Yosys errors (e.g., invalid commands)

### 4. Robust Execution
- Runs Yosys scripts in temporary files
- Handles timeouts and execution errors
- Cleans up temporary files automatically

## Usage

### Basic Usage
```python
from yosys_loop_agent import run_yosys_script_loop

result = run_yosys_script_loop(
    verilog_path="yosys_test/counter.v",
    sdc_path="yosys_test/counter.sdc",
    max_iterations=5
)
```

### Running Tests
```bash
python test_yosys_loop.py
```

### Running Demo
```bash
# Basic demo
python demo_yosys_loop.py

# Interactive demo with custom files
python demo_yosys_loop.py --interactive
```

## How It Works

### 1. Initialization
- Sets up state with file paths and iteration limits
- Initializes message history for LLM communication

### 2. Script Generation Loop
```
generate_yosys_script → execute_yosys_script → evaluate_execution → (continue/end)
```

### 3. Learning from Failures
- First iteration: Generates initial script
- Subsequent iterations: Uses previous script + execution log + error details
- LLM learns from specific errors to generate corrected scripts

### 4. Success Criteria
- Yosys execution completes without errors
- Output files are generated successfully
- Maximum iterations reached (failure case)

## Example Output

```
Starting Yosys script generation loop for:
- Verilog file: yosys_test/counter.v
- SDC file: yosys_test/counter.sdc
- Max iterations: 3

============================================================
FINAL RESULTS
============================================================
✅ SUCCESS! Yosys script executed successfully in 2 iterations.
Output file: counter_synthesized_netlist.v

Total iterations: 2
```

## Key Improvements Made

### 1. Script Extraction
- Enhanced extraction logic to handle various LLM response formats
- Filters out explanatory text and focuses on Yosys commands
- Handles code blocks and script sections properly

### 2. Prompt Engineering
- Clear instructions to return only Yosys commands
- Examples provided in prompts
- Specific feedback for error correction

### 3. Error Handling
- Comprehensive error capture and analysis
- Specific error details passed to LLM for correction
- Handles timeouts, command errors, and file issues

### 4. State Management
- Tracks previous scripts and logs for learning
- Maintains iteration count and success status
- Proper cleanup and resource management

## Testing

The test suite includes:
- ✅ Yosys installation check
- ✅ Test file validation
- ✅ State initialization testing
- ✅ Script extraction testing
- ✅ Yosys execution testing
- ✅ Full loop testing

All tests pass successfully, demonstrating the robustness of the implementation.

## Dependencies

- `langchain-openai` - For LLM integration
- `langgraph` - For state graph management
- `python-dotenv` - For environment variable management
- `yosys` - Must be installed and in PATH

## Environment Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Yosys:
   - Ubuntu/Debian: `sudo apt-get install yosys`
   - macOS: `brew install yosys`
   - Or download from: https://github.com/YosysHQ/yosys

3. Set up OpenAI API key in `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Architecture Comparison

### Number Guessing Game
- **State**: target_number, attempt, feedback, game_over
- **Loop**: guess → evaluate → continue/end
- **Learning**: Uses feedback to adjust guess range

### Yosys Loop Agent
- **State**: verilog_path, sdc_path, iteration, current_script, execution_log, feedback, game_over
- **Loop**: generate_script → execute_script → evaluate → continue/end
- **Learning**: Uses execution logs and error details to improve scripts

Both implementations follow the same pattern of iterative improvement with state management and intelligent feedback loops.
