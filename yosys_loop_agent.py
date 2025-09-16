import re
import subprocess
import tempfile
import os
from typing import TypedDict, Literal, List, Optional
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv 
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

# Define the state structure for Yosys script generation loop
class YosysAgentState(TypedDict):
    verilog_path: str
    sdc_path: str
    iteration: int
    max_iterations: int
    current_script: str
    last_script: Optional[str]
    execution_log: str
    last_execution_log: Optional[str]
    feedback: Literal["success", "failure", "timeout", "error", None]
    game_over: bool
    message_history: List
    output_file: str
    error_details: str

def initialize_yosys_game(state: YosysAgentState):
    """Initialize the Yosys script generation game"""
    if "iteration" not in state:
        state["iteration"] = 0
        
    if "max_iterations" not in state:
        state["max_iterations"] = 5
        
    if "feedback" not in state:
        state["feedback"] = None
        
    if "game_over" not in state:
        state["game_over"] = False
        
    if "current_script" not in state:
        state["current_script"] = ""
        
    if "last_script" not in state:
        state["last_script"] = None
        
    if "execution_log" not in state:
        state["execution_log"] = ""
        
    if "last_execution_log" not in state:
        state["last_execution_log"] = None
        
    if "error_details" not in state:
        state["error_details"] = ""
        
    if "message_history" not in state:
        state["message_history"] = [
            SystemMessage(content="You are an expert Yosys synthesis tool assistant. Generate and refine Yosys scripts until they execute successfully. Always return ONLY the Yosys commands without any explanations, markdown formatting, or additional text.")
        ]
    
    # Generate output filename from verilog path
    if "output_file" not in state and state.get("verilog_path"):
        verilog_basename = os.path.splitext(os.path.basename(state["verilog_path"]))[0]
        state["output_file"] = f"{verilog_basename}_synthesized_netlist.v"
    
    return state

def extract_script_from_text(text: str) -> str:
    """Extract Yosys script from LLM response"""
    lines = text.split('\n')
    script_lines = []
    in_code_block = False
    in_script_section = False
    
    for line in lines:
        line = line.strip()
        
        # Check for code block markers
        if line.startswith('```'):
            in_code_block = not in_code_block
            continue
        
        # Check for script section markers
        if 'yosys synthesis script' in line.lower() or 'here\'s the' in line.lower():
            in_script_section = True
            continue
        
        # Skip explanatory text
        if any(skip_word in line.lower() for skip_word in ['here\'s', 'to generate', 'you can', 'step', 'note:', 'key points:', 'make sure', 'adjust', 'if you', 'for example']):
            continue
        
        # If we're in a code block or script section, extract Yosys commands
        if (in_code_block or in_script_section) and line:
            # Only include lines that look like Yosys commands
            if (line.startswith('#') or  # Comments
                any(cmd in line.lower() for cmd in ['read_verilog', 'read_sdc', 'synth', 'write_verilog', 'write_json', 'stat', 'opt', 'hierarchy', 'flatten', 'show', 'abc', 'write_edif'])):
                script_lines.append(line)
    
    # If no script found in code blocks, try to extract from the whole text
    if not script_lines:
        for line in lines:
            line = line.strip()
            if (line.startswith('#') or  # Comments
                any(cmd in line.lower() for cmd in ['read_verilog', 'read_sdc', 'synth', 'write_verilog', 'write_json', 'stat', 'opt', 'hierarchy', 'flatten', 'show', 'abc', 'write_edif'])):
                script_lines.append(line)
    
    return '\n'.join(script_lines).strip()

def generate_yosys_script(state: YosysAgentState):
    """Generate a Yosys script based on previous feedback"""
    state = initialize_yosys_game(state)
    
    # Prepare the prompt based on previous feedback
    if state["iteration"] == 0:
        prompt = f"""Generate a Yosys synthesis script for:
        - Verilog file: {state['verilog_path']}
        - SDC constraints file: {state['sdc_path']}
        - Output file: {state['output_file']}

        IMPORTANT: Return ONLY the Yosys commands, one per line. Do not include any explanations, markdown formatting, or additional text. Just the commands.

        Example format:
        read_verilog counter.v
        synth -top counter
        opt
        write_verilog output.v
        stat"""
    else:
        # Include previous script and execution log for refinement
        prompt = f"""The previous Yosys script failed. Please generate an improved script.

        Previous script:
        {state['last_script']}

        Previous execution log:
        {state['last_execution_log']}

        Error details: {state['error_details']}

        IMPORTANT: Return ONLY the corrected Yosys commands, one per line. Do not include any explanations, markdown formatting, or additional text. Just the commands.

        Generate a corrected Yosys script for:
        - Verilog file: {state['verilog_path']}
        - SDC constraints file: {state['sdc_path']}
        - Output file: {state['output_file']}

        Focus on fixing the issues identified in the previous execution."""
    
    # Add to message history
    state["message_history"].append(HumanMessage(content=prompt))
    
    # Get the LLM's script generation
    response = llm.invoke(state["message_history"])
    state["message_history"].append(response)
    
    # Extract the script from the response
    script = extract_script_from_text(response.content)
    
    if not script:
        # If no script found, add a special message
        state["message_history"].append(HumanMessage(
            content="Please generate a valid Yosys script with proper commands like read_verilog, synth, write_verilog, etc."
        ))
        return state
    
    state["current_script"] = script
    state["iteration"] += 1
    
    return state

def execute_yosys_script(state: YosysAgentState):
    """Execute the generated Yosys script"""
    try:
        # Create a temporary file to store the Yosys script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ys', delete=False) as temp_file:
            temp_file.write(state["current_script"])
            temp_script_path = temp_file.name
        
        try:
            # Run Yosys with the temporary script file
            result = subprocess.run(
                ['yosys', temp_script_path], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=60  # 60 second timeout
            )
            
            # Clean up the temporary file
            os.unlink(temp_script_path)
            
            # Success case
            state["feedback"] = "success"
            state["game_over"] = True
            state["execution_log"] = f"Yosys execution completed successfully!\n\nSTDOUT:\n{result.stdout}\n"
            if result.stderr:
                state["execution_log"] += f"STDERR:\n{result.stderr}\n"
            
        except subprocess.TimeoutExpired:
            # Clean up the temporary file
            os.unlink(temp_script_path)
            state["feedback"] = "timeout"
            state["execution_log"] = "Yosys execution timed out after 60 seconds"
            state["error_details"] = "Script execution timed out"
            
        except subprocess.CalledProcessError as e:
            # Clean up the temporary file
            os.unlink(temp_script_path)
            state["feedback"] = "failure"
            state["execution_log"] = f"Yosys execution failed with return code {e.returncode}\n\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}\n"
            state["error_details"] = f"Return code: {e.returncode}, Error: {e.stderr}"
            
    except FileNotFoundError:
        state["feedback"] = "error"
        state["execution_log"] = "Yosys tool is not installed or not in PATH. Please install Yosys first."
        state["error_details"] = "Yosys not found"
        state["game_over"] = True
    except Exception as e:
        state["feedback"] = "error"
        state["execution_log"] = f"Error running Yosys tool: {str(e)}"
        state["error_details"] = str(e)
        state["game_over"] = True
    
    # Store current script and log as "last" for next iteration
    state["last_script"] = state["current_script"]
    state["last_execution_log"] = state["execution_log"]
    
    return state

def evaluate_execution(state: YosysAgentState):
    """Evaluate the execution result and determine next steps"""
    if state["feedback"] == "success":
        state["game_over"] = True
    elif state["iteration"] >= state["max_iterations"]:
        state["game_over"] = True
        state["feedback"] = "max_iterations_reached"
    
    return state

def should_continue_yosys(state: YosysAgentState):
    """Determine whether to continue the script generation loop"""
    if state["game_over"]:
        return END
    return "generate_yosys_script"

# Build the graph
builder = StateGraph(YosysAgentState)
builder.add_node("generate_yosys_script", generate_yosys_script)
builder.add_node("execute_yosys_script", execute_yosys_script)
builder.add_node("evaluate_execution", evaluate_execution)

builder.set_entry_point("generate_yosys_script")
builder.add_edge("generate_yosys_script", "execute_yosys_script")
builder.add_edge("execute_yosys_script", "evaluate_execution")
builder.add_conditional_edges("evaluate_execution", should_continue_yosys)

graph = builder.compile()

def run_yosys_script_loop(verilog_path: str, sdc_path: str, max_iterations: int = 5):
    """Run the Yosys script generation and execution loop"""
    print(f"Starting Yosys script generation loop for:")
    print(f"- Verilog file: {verilog_path}")
    print(f"- SDC file: {sdc_path}")
    print(f"- Max iterations: {max_iterations}")
    print("-" * 60)
    
    # Initialize state
    initial_state = {
        "verilog_path": verilog_path,
        "sdc_path": sdc_path,
        "iteration": 0,
        "max_iterations": max_iterations,
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
    
    # Run the graph
    final_state = graph.invoke(initial_state)
    
    # Print results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    if final_state["feedback"] == "success":
        print(f"✅ SUCCESS! Yosys script executed successfully in {final_state['iteration']} iterations.")
        print(f"Output file: {final_state['output_file']}")
    elif final_state["feedback"] == "max_iterations_reached":
        print(f"❌ FAILED! Maximum iterations ({final_state['max_iterations']}) reached without success.")
    else:
        print(f"❌ FAILED! Error: {final_state['feedback']}")
    
    print(f"\nTotal iterations: {final_state['iteration']}")
    
    # Print the script generation history
    print("\n" + "="*60)
    print("SCRIPT GENERATION HISTORY")
    print("="*60)
    
    for i, msg in enumerate(final_state["message_history"]):
        if msg.type == "human" and not msg.content.startswith("Please generate"):
            print(f"\nIteration {i//2 + 1} - Request:")
            print(f"{msg.content}")
        elif msg.type == "ai":
            print(f"\nIteration {i//2 + 1} - Generated Script:")
            print(f"{msg.content}")
    
    # Print final execution log
    if final_state["execution_log"]:
        print("\n" + "="*60)
        print("FINAL EXECUTION LOG")
        print("="*60)
        print(final_state["execution_log"])
    
    return final_state

if __name__ == "__main__":
    # Test with the provided counter files
    verilog_path = "yosys_test/counter.v"
    sdc_path = "yosys_test/counter.sdc"
    
    if os.path.exists(verilog_path) and os.path.exists(sdc_path):
        run_yosys_script_loop(verilog_path, sdc_path, max_iterations=5)
    else:
        print(f"Error: Required files not found:")
        print(f"- {verilog_path}: {'✓' if os.path.exists(verilog_path) else '✗'}")
        print(f"- {sdc_path}: {'✓' if os.path.exists(sdc_path) else '✗'}")
        print("Please ensure the files exist before running the script.")
