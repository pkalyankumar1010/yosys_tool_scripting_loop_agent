import random
import re
from typing import TypedDict, Literal
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv 
from langchain_core.messages import HumanMessage, SystemMessage
load_dotenv()
# Initialize the LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

# Define the state structure
class AgentState(TypedDict):
    target_number: int
    attempt: int
    max_attempts: int
    last_guess: int
    min_range: int
    max_range: int
    feedback: Literal["higher", "lower", "correct", None]
    game_over: bool
    message_history: list

def initialize_game(state: AgentState):
    """Initialize the game with a random target number"""
    if "target_number" not in state or state["target_number"] is None:
        state["target_number"] = random.randint(1, 100)
        print("Target Number: ", state["target_number"])
    
    if "attempt" not in state:
        state["attempt"] = 0
        
    if "max_attempts" not in state:
        state["max_attempts"] = 10
        
    if "min_range" not in state:
        state["min_range"] = 1
        
    if "max_range" not in state:
        state["max_range"] = 100
        
    if "feedback" not in state:
        state["feedback"] = None
        
    if "game_over" not in state:
        state["game_over"] = False
        
    if "message_history" not in state:
        state["message_history"] = [
            SystemMessage(content="You are playing a number guessing game. I've selected a number between 1 and 100. Try to guess it!")
        ]
    
    return state

def extract_number_from_text(text):
    """Extract a number from text using regex"""
    numbers = re.findall(r'\b\d+\b', text)
    if numbers:
        return int(numbers[0])
    return None

def agent_guess(state: AgentState):
    """Agent makes a guess based on previous feedback"""
    state = initialize_game(state)
    
    # Prepare the prompt based on previous feedback
    if state["attempt"] == 0:
        prompt = f"I'm thinking of a number between {state['min_range']} and {state['max_range']}. Make your first guess!"
    else:
        if state["feedback"] == "higher":
            prompt = f"Your guess of {state['last_guess']} was too low. Try a higher number between {state['last_guess']+1} and {state['max_range']}."
        elif state["feedback"] == "lower":
            prompt = f"Your guess of {state['last_guess']} was too high. Try a lower number between {state['min_range']} and {state['last_guess']-1}."
        else:
            prompt = f"Make your guess between {state['min_range']} and {state['max_range']}!"
    
    # Add to message history
    state["message_history"].append(HumanMessage(content=prompt))
    
    # Get the LLM's guess
    response = llm.invoke(state["message_history"])
    state["message_history"].append(response)
    
    # Extract the guess from the response
    guess = extract_number_from_text(response.content)
    
    if guess is None:
        # If no number found, add a special message and keep the same guess
        state["message_history"].append(HumanMessage(
            content="Please respond with only a number between 1 and 100. No other text."
        ))
        # Don't increment attempt count for invalid responses
        return state
    
    # Validate the guess is within the current range
    if guess < state["min_range"] or guess > state["max_range"]:
        state["message_history"].append(HumanMessage(
            content=f"Your guess of {guess} is outside the valid range of {state['min_range']} to {state['max_range']}. Please try again."
        ))
        # Don't increment attempt count for invalid guesses
        return state
    
    state["last_guess"] = guess
    state["attempt"] += 1
    
    return state

def evaluate_guess(state: AgentState):
    """Evaluate the agent's guess against the target number"""
    if state["last_guess"] == state["target_number"]:
        state["feedback"] = "correct"
        state["game_over"] = True
    elif state["last_guess"] < state["target_number"]:
        state["feedback"] = "higher"
        state["min_range"] = state["last_guess"] + 1
    else:
        state["feedback"] = "lower"
        state["max_range"] = state["last_guess"] - 1
    
    # Check if max attempts reached
    if state["attempt"] >= state["max_attempts"] and not state["game_over"]:
        state["game_over"] = True
        state["feedback"] = "max_attempts_reached"
    
    return state

def should_continue(state: AgentState):
    """Determine whether to continue the game"""
    if state["game_over"]:
        return END
    return "agent_guess"

# Build the graph
builder = StateGraph(AgentState)
builder.add_node("agent_guess", agent_guess)
builder.add_node("evaluate_guess", evaluate_guess)

builder.set_entry_point("agent_guess")
builder.add_edge("agent_guess", "evaluate_guess")
builder.add_conditional_edges("evaluate_guess", should_continue)

graph = builder.compile()

# Run the game
def play_game():
    print("I'm thinking of a number between 1 and 100. Try to guess it!")
    
    # Initialize state
    initial_state = {
        "target_number": None,
        "attempt": 0,
        "max_attempts": 10,
        "last_guess": None,
        "min_range": 1,
        "max_range": 100,
        "feedback": None,
        "game_over": False,
        "message_history": []
    }
    
    # Run the graph
    final_state = graph.invoke(initial_state)
    
    # Print results
    if final_state["feedback"] == "correct":
        print(f"\nCongratulations! You guessed the number {final_state['target_number']} in {final_state['attempt']} attempts.")
    else:
        print(f"\nGame over! The number was {final_state['target_number']}. You used {final_state['attempt']} attempts.")
    
    # Print the guessing history
    print("\nGuessing history:")
    for i, msg in enumerate(final_state["message_history"]):
        if msg.type == "human" and not msg.content.startswith("Please respond"):
            print(f"System: {msg.content}")
        elif msg.type == "ai":
            print(f"AI: {msg.content}")

if __name__ == "__main__":
    play_game()