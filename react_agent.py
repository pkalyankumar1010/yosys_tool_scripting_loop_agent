from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv  
from langchain_core.messages import BaseMessage # The foundational class for all message types in LangGraph
from langchain_core.messages import ToolMessage # Passes data back to LLM after it calls a tool such as the content and the tool_call_id
from langchain_core.messages import SystemMessage # Message for providing instructions to the LLM
from langchain_core.messages import HumanMessage # Message from human user
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import subprocess


load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


@tool
def add(a: int, b:int):
    """This is an addition function that adds 2 numbers together"""

    return a + b 

@tool
def subtract(a: int, b: int):
    """Subtraction function"""
    return a - b

@tool
def multiply(a: int, b: int):
    """Multiplication function"""
    return a * b

@tool
def yosys_tool():
    """Get Yosys version information"""
    try:
        # Run yosys with -V or --version to get version info
        result = subprocess.run(['yosys', '-V'], capture_output=True, text=True, check=True)
        
        # The version is typically in stdout
        version_output = result.stdout.strip()
        
        return f"Yosys version: {version_output}"
    except subprocess.CalledProcessError as e:
        return f"Yosys command failed: {e}"
    except FileNotFoundError:
        return "Yosys tool is not installed or not in PATH. Please install Yosys first."
    
@tool
def yosys_script_generator(description: str):
    """Generate yosys script using llm call based on user description"""
    try:
        # Create a separate LLM instance for script generation
        script_model = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # System prompt for Yosys script generation
        system_prompt = """You are an expert in Yosys synthesis tool. Generate a Yosys script based on the user's description.

Yosys script format:
- Use `read_verilog` to read Verilog files
- Use `read_ilang` to read intermediate language files
- Use `synth` for synthesis
- Use `write_verilog` to write output
- Use `write_json` to write JSON netlist
- Use `stat` to show statistics
- Use `show` to visualize
- Use `flatten` to flatten hierarchy
- Use `hierarchy` to check hierarchy

Return ONLY the Yosys script commands, one per line, without explanations or markdown formatting.
Example:
read_verilog design.v
synth
write_verilog output.v"""

        # Generate the script
        response = script_model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate a Yosys script for: {description}")
        ])
        
        return f"Generated Yosys script:\n{response.content}"
        
    except Exception as e:
        return f"Error generating Yosys script: {str(e)}"

@tool
def yosys_script_with_paths():
    """Generate yosys script by asking for SDC and Verilog file paths"""
    try:
        # Create a separate LLM instance for interactive script generation
        script_model = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # Interactive prompt to get file paths
        interactive_prompt = """I need to generate a Yosys synthesis script. Please provide:
1. The path to your Verilog file (.v)
2. The path to your SDC constraints file (.sdc)

Please respond in this exact format:
Verilog file: [path_to_your_file.v]
SDC file: [path_to_your_file.sdc]

Example:
Verilog file: counter.v
SDC file: counter.sdc"""

        response = script_model.invoke([
            SystemMessage(content=interactive_prompt)
        ])
        
        return f"Please provide your file paths:\n{response.content}"
        
    except Exception as e:
        return f"Error in interactive script generation: {str(e)}"

@tool
def generate_yosys_script_from_paths(verilog_path: str, sdc_path: str):
    """Generate yosys script using LLM based on provided Verilog and SDC file paths"""
    try:
        import os
        
        # Extract base name from verilog file path
        verilog_basename = os.path.splitext(os.path.basename(verilog_path))[0]
        sdc_basename = os.path.splitext(os.path.basename(sdc_path))[0]
        
        # Generate output filename
        output_filename = f"{verilog_basename}_synthesized_netlist.v"
        
        # Create a separate LLM instance for script generation
        script_model = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # System prompt for Yosys script generation with specific paths
        system_prompt = f"""You are an expert in Yosys synthesis tool. Generate a comprehensive Yosys script based on the provided file paths.

Input files:
- Verilog file: {verilog_path}
- SDC constraints file: {sdc_path}
- Output file should be named: {output_filename}

Generate a complete Yosys synthesis script that includes:
1. Reading the Verilog file
2. Reading the SDC constraints file
3. Synthesis with proper top module detection
4. Optimization steps
5. Statistics reporting
6. Writing the synthesized netlist
7. Optional JSON output

Use these Yosys commands as needed:
- read_verilog [file] - Read Verilog files
- read_sdc [file] - Read SDC constraints
- synth -top [module_name] - Synthesize design
- opt - Optimize design
- stat - Show statistics
- write_verilog [file] - Write Verilog netlist
- write_json [file] - Write JSON netlist
- hierarchy - Check hierarchy
- flatten - Flatten hierarchy

Return ONLY the Yosys script commands, one per line, without explanations or markdown formatting.
Include comments using # for clarity."""

        # Generate the script using LLM
        response = script_model.invoke([
            SystemMessage(content=system_prompt)
        ])
        
        return f"Generated Yosys script for {verilog_basename}:\n{response.content}"
        
    except Exception as e:
        return f"Error generating script from paths: {str(e)}"

@tool
def run_yosys_tool(yosys_script: str):
    """Run yosys tool with the provided script"""
    try:
        import tempfile
        import os
        
        # Create a temporary file to store the Yosys script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ys', delete=False) as temp_file:
            temp_file.write(yosys_script)
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
            
            # Return the output
            output = f"Yosys execution completed successfully!\n\n"
            output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            return output
            
        except subprocess.TimeoutExpired:
            # Clean up the temporary file
            os.unlink(temp_script_path)
            return "Yosys execution timed out after 60 seconds"
            
        except subprocess.CalledProcessError as e:
            # Clean up the temporary file
            os.unlink(temp_script_path)
            error_output = f"Yosys execution failed with return code {e.returncode}\n\n"
            error_output += f"STDOUT:\n{e.stdout}\n"
            error_output += f"STDERR:\n{e.stderr}\n"
            return error_output
            
    except FileNotFoundError:
        return "Yosys tool is not installed or not in PATH. Please install Yosys first."
    except Exception as e:
        return f"Error running Yosys tool: {str(e)}"

tools = [add, subtract, multiply, yosys_tool, yosys_script_generator, yosys_script_with_paths, generate_yosys_script_from_paths, run_yosys_tool]

model = ChatOpenAI(model = "gpt-4o").bind_tools(tools)


def model_call(state:AgentState) -> AgentState:
    # Check if the last message is a tool message from various yosys tools
    last_message = state["messages"][-1]
    strict_instruction = ""
    
    # Check if the last message is a ToolMessage from yosys_tool
    if isinstance(last_message, ToolMessage) and last_message.name == "yosys_tool":
        strict_instruction = (
            "CRITICAL: You must respond with ONLY the version number from the tool output. "
            "Do not add any explanations, formatting, or extra text. Just return the exact version number."
        )
    # Check if the last message is a ToolMessage from yosys_script_generator
    elif isinstance(last_message, ToolMessage) and last_message.name == "yosys_script_generator":
        strict_instruction = (
            "CRITICAL: You must respond with ONLY the generated Yosys script. "
            "Do not add any explanations, formatting, or extra text. Just return the script commands."
        )
    # Check if the last message is a ToolMessage from generate_yosys_script_from_paths
    elif isinstance(last_message, ToolMessage) and last_message.name == "generate_yosys_script_from_paths":
        strict_instruction = (
            "CRITICAL: You must respond with ONLY the generated Yosys script. "
            "Do not add any explanations, formatting, or extra text. Just return the script commands."
        )
    # Check if the last message is a ToolMessage from yosys_script_with_paths
    elif isinstance(last_message, ToolMessage) and last_message.name == "yosys_script_with_paths":
        strict_instruction = (
            "CRITICAL: You must respond with ONLY the request for file paths. "
            "Do not add any explanations, formatting, or extra text. Just return the path request."
        )
    # Check if the last message is a ToolMessage from run_yosys_tool
    elif isinstance(last_message, ToolMessage) and last_message.name == "run_yosys_tool":
        strict_instruction = (
            "CRITICAL: You must respond with ONLY the Yosys execution output. "
            "Do not add any explanations, formatting, or extra text. Just return the execution results."
        )
    
    system_prompt = SystemMessage(content=
        "You are my AI assistant, please answer my query to the best of your ability." + strict_instruction
    )
    response = model.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState): 
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls: 
        return "end"
    else:
        return "continue"
    

graph = StateGraph(AgentState)
graph.add_node("our_agent", model_call)


tool_node = ToolNode(tools=tools)
graph.add_node("tools", tool_node)

graph.set_entry_point("our_agent")

graph.add_conditional_edges(
    "our_agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)

graph.add_edge("tools", "our_agent")

app = graph.compile()

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
from IPython.display import Image, display
from PIL import Image as PILImage
import io
# Open the image from bytes
image_data = app.get_graph().draw_mermaid_png()
image = PILImage.open(io.BytesIO(image_data))

# Show the image using default image viewer
image.show()

# inputs = {"messages": [("user", "Generate a yosys script")]}
# print_stream(app.stream(inputs, stream_mode="values"))

# ... existing code ...

def interactive_mode():
    """Run the agent in interactive mode"""
    print("Welcome to the Yosys Script Generator Agent!")
    print("Available commands:")
    print("- Ask for Yosys version: 'What is the version of yosys?'")
    print("- Generate script: 'Generate a yosys script'")
    print("- Generate with paths: 'Generate yosys script with paths'")
    print("- Run Yosys: 'Run the yosys script' (after generating one)")
    print("- Math operations: 'Add 5 + 3' or 'Multiply 10 * 2'")
    print("- Type 'quit' or 'exit' to stop the program.")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
                
            if not user_input:
                continue
                
            # Process the user input
            inputs = {"messages": [("user", user_input)]}
            
            print("\n" + "="*50)
            print("Agent Response:")
            print("="*50)
            
            # Stream the response
            for s in app.stream(inputs, stream_mode="values"):
                message = s["messages"][-1]
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    interactive_mode()