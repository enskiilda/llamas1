"""
Chat endpoint handler with computer control
This module contains the CRITICAL LOOP LOGIC exactly ported from TypeScript
"""

import json
import asyncio
import re
import base64
from datetime import datetime
from typing import AsyncIterator, Dict, Any, List
from openai import AsyncOpenAI

from text_filter import remove_json_from_text
from instructions import INSTRUCTIONS

RESOLUTION = {"x": 1024, "y": 768}


async def handle_chat_stream(
    messages: List[Dict],
    sandbox_id: str,
    desktop,
    kernel_client,
    nvidia_client: AsyncOpenAI
) -> AsyncIterator[str]:
    """
    Stream generator for chat responses
    
    CRITICAL LOOP PRESERVATION:
    This maintains the exact while True loop from the original TypeScript code.
    Each iteration:
    1. Calls NVIDIA AI with current chat history
    2. Streams text response (with filtering)
    3. Executes tool calls (ONE at a time)
    4. Adds results back to chat history
    5. Continues loop until !isfinish command
    """
    
    def send_event(event: Dict[str, Any]) -> str:
        """Send JSON event to client"""
        try:
            json_line = json.dumps(event) + "\n"
            return json_line
        except Exception as err:
            print(f"Error sending event: {err}")
            return ""
    
    def send_text(text: str) -> str:
        """Send raw text to client"""
        try:
            return text + "\n"
        except Exception as err:
            print(f"Error sending text: {err}")
            return ""
    
    try:
        # Clean messages for NVIDIA API compatibility
        cleaned_messages = []
        for msg in messages:
            clean_msg = {k: v for k, v in msg.items() if k != "toolCalls"}
            # NVIDIA requires content to be a string, not null/undefined
            if clean_msg.get("content") is None or clean_msg.get("content") == "":
                clean_msg["content"] = ""
            # Convert toolCalls (camelCase) to tool_calls (snake_case) for NVIDIA
            if "toolCalls" in msg:
                clean_msg["tool_calls"] = msg["toolCalls"]
            cleaned_messages.append(clean_msg)
        
        chat_history = [
            {
                "role": "system",
                "content": INSTRUCTIONS
            },
            *cleaned_messages
        ]
        
        # Define tools for function calling
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "computer_use",
                    "description": "Control the computer desktop by performing actions like clicking, typing, taking screenshots, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["screenshot", "left_click", "right_click", "double_click", "mouse_move", "type", "key", "scroll", "wait", "left_click_drag"],
                                "description": "The action to perform on the computer"
                            },
                            "coordinate": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "X, Y coordinates for click/move actions (e.g., [512, 384])"
                            },
                            "text": {
                                "type": "string",
                                "description": "Text to type or key to press"
                            },
                            "start_coordinate": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "Starting coordinates for drag action"
                            },
                            "delta_x": {
                                "type": "number",
                                "description": "Horizontal scroll delta"
                            },
                            "delta_y": {
                                "type": "number",
                                "description": "Vertical scroll delta"
                            },
                            "duration": {
                                "type": "number",
                                "description": "Duration in seconds for wait action"
                            }
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_workflow",
                    "description": "Update the workflow/plan with current progress and steps",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "steps": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "number"},
                                        "title": {"type": "string"},
                                        "status": {
                                            "type": "string",
                                            "enum": ["pending", "in_progress", "completed", "skipped"]
                                        }
                                    }
                                }
                            },
                            "current_step": {
                                "type": "number"
                            },
                            "notes": {
                                "type": "string"
                            }
                        },
                        "required": ["steps"]
                    }
                }
            }
        ]
        
        message_counter = 0
        
        # CRITICAL: Main infinite loop - EXACT PORT from TypeScript
        # This loop continues until AI sends !isfinish command
        while True:
            # Call NVIDIA AI with streaming
            stream = await nvidia_client.chat.completions.create(
                model="meta/llama-4-scout-17b-16e-instruct",
                messages=chat_history,
                temperature=0.7,
                top_p=0.95,
                stream=True,
                tools=tools,
                tool_choice="auto"
            )
            
            full_text = ""
            tool_calls = []
            last_sent_text_length = 0
            
            # Stream the AI response
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta = choice.delta
                    
                    # Handle text content
                    if delta.content:
                        full_text += delta.content
                        
                        # Filter entire fullText accumulated so far
                        filtered_full_text = remove_json_from_text(full_text)
                        
                        # Send only the NEW part (difference from last sent text)
                        if len(filtered_full_text) > last_sent_text_length:
                            new_content = filtered_full_text[last_sent_text_length:]
                            
                            if new_content:
                                yield send_text(new_content)
                            
                            last_sent_text_length = len(filtered_full_text)
                    
                    # Handle tool calls - NVIDIA może zwracać w różnych formatach
                    if delta.tool_calls:
                        for tool_call_delta in delta.tool_calls:
                            index = getattr(tool_call_delta, 'index', 0) or 0
                            
                            # Ensure tool_calls list is large enough
                            while len(tool_calls) <= index:
                                tool_calls.append({
                                    "id": f"call_{int(datetime.now().timestamp() * 1000)}_{index}",
                                    "name": "",
                                    "arguments": ""
                                })
                            
                            # Update name if provided
                            if tool_call_delta.function and tool_call_delta.function.name:
                                tool_calls[index]["name"] = tool_call_delta.function.name
                            
                            # Update id if provided
                            if tool_call_delta.id:
                                tool_calls[index]["id"] = tool_call_delta.id
                            
                            # Append arguments
                            if tool_call_delta.function and tool_call_delta.function.arguments:
                                tool_calls[index]["arguments"] += tool_call_delta.function.arguments
            
            # Filter out empty tool calls
            tool_calls = [tc for tc in tool_calls if tc and tc.get("name")]
            
            # Fix malformed JSON arguments from NVIDIA streaming
            fixed_tool_calls = []
            for tc in tool_calls:
                if tc.get("arguments"):
                    fixed_args = tc["arguments"].strip()
                    
                    # Count braces to find if JSON is incomplete
                    open_braces = fixed_args.count('{')
                    close_braces = fixed_args.count('}')
                    
                    # If more opening braces than closing, add missing closing braces
                    if open_braces > close_braces:
                        missing = open_braces - close_braces
                        fixed_args += '}' * missing
                    
                    # Fix common NVIDIA streaming bugs
                    fixed_args = re.sub(r'"([^"]+)", "([^"]+)":\s*', r'"\1", "\2": ', fixed_args)
                    fixed_args = re.sub(r':\s*\[\](\d)', r': [\1', fixed_args)
                    fixed_args = re.sub(r'\[(\d+),\s*(\d+)(?!\])', r'[\1, \2]', fixed_args)
                    
                    # Ensure arrays are properly closed
                    if '[' in fixed_args and ']' not in fixed_args:
                        last_bracket = fixed_args.rfind('[')
                        after_bracket = fixed_args[last_bracket + 1:]
                        if re.search(r'\d', after_bracket):
                            fixed_args = re.sub(r'\[([^\]]+)$', r'[\1]', fixed_args)
                    
                    # Verify it's valid JSON
                    try:
                        json.loads(fixed_args)
                        tc["arguments"] = fixed_args
                    except json.JSONDecodeError as e:
                        print(f'[JSON FIX ERROR] {e}, Original: {tc["arguments"]}, Fixed: {fixed_args}')
                        # Try to salvage what we can
                        action_match = re.search(r'"action":\s*"([^"]+)"', tc["arguments"])
                        if action_match:
                            action = action_match.group(1)
                            
                            # Try to extract coordinate if present
                            coord_match = re.search(r'(\d+),\s*(\d+)', tc["arguments"])
                            if coord_match and (action in ['left_click', 'right_click', 'double_click', 'mouse_move', 'click']):
                                tc["arguments"] = json.dumps({
                                    "action": action,
                                    "coordinate": [int(coord_match.group(1)), int(coord_match.group(2))]
                                })
                            elif action in ['screenshot', 'wait']:
                                tc["arguments"] = json.dumps({"action": action})
                            else:
                                # Try to extract text
                                text_match = re.search(r'"text":\s*"([^"]+)"', tc["arguments"])
                                if text_match:
                                    tc["arguments"] = json.dumps({
                                        "action": action,
                                        "text": text_match.group(1)
                                    })
                                else:
                                    tc["arguments"] = json.dumps({"action": action})
                
                fixed_tool_calls.append(tc)
            
            tool_calls = fixed_tool_calls
            
            # Check if AI wants to finish - look for !isfinish command
            wants_to_finish = full_text and '!isfinish' in full_text.lower()
            
            # CRITICAL: Tool call execution logic - EXACT PORT from TypeScript
            if len(tool_calls) > 0:
                # AI is calling tools - EXECUTE ONLY FIRST ONE, then continue loop
                first_tool_call = tool_calls[0]
                
                # KROK 1: Wyślij finish event aby frontend zamknął obecną wiadomość tekstową
                yield send_event({"type": "finish"})
                
                message_counter += 1
                
                # KROK 2: Dodaj tekst do historii czatu (tylko jeśli był)
                if full_text and full_text.strip():
                    filtered_text = remove_json_from_text(full_text)
                    if filtered_text and filtered_text.strip():
                        chat_history.append({
                            "role": "assistant",
                            "content": filtered_text
                        })
                
                # KROK 3: Przygotuj tool call message - JAKO OSOBNA WIADOMOŚĆ
                message_counter += 1
                
                assistant_message = {
                    "role": "assistant",
                    "content": "",  # NO TEXT HERE - action only
                    "tool_calls": [{
                        "id": first_tool_call["id"],
                        "type": "function",
                        "function": {
                            "name": first_tool_call["name"],
                            "arguments": first_tool_call["arguments"]
                        }
                    }]
                }
                chat_history.append(assistant_message)
                
                tool_call = first_tool_call
                parsed_args = json.loads(tool_call["arguments"])
                tool_name = "computer" if tool_call["name"] == "computer_use" else ("workflow" if tool_call["name"] == "update_workflow" else "bash")
                
                yield send_event({
                    "type": "tool-input-available",
                    "toolCallId": tool_call["id"],
                    "toolName": tool_name,
                    "input": parsed_args
                })
                
                # Execute the tool - import tool executor
                from tool_executor import execute_tool
                
                screenshot_data, tool_result = await execute_tool(
                    tool_call, parsed_args, desktop, kernel_client, send_event
                )
                
                # Send tool result to chat history
                if screenshot_data:
                    # KRYTYCZNE: Screenshot jako TOOL MESSAGE (potwierdzenie akcji)
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_result["tool_call_id"],
                        "content": f"Screenshot captured successfully at {screenshot_data['timestamp']}"
                    }
                    chat_history.append(tool_message)
                    
                    # KRYTYCZNE: Screenshot jako USER MESSAGE (obraz do analizy)
                    user_screenshot_message = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Oto screenshot z sandboxa. Przeanalizuj go dokładnie przed podjęciem kolejnej akcji.\n\nSCREEN: {screenshot_data['width']}×{screenshot_data['height']} pixels | Aspect ratio: 4:3 | Origin: (0,0) at TOP-LEFT\n⚠️ REMEMBER: Y=0 is at TOP, Y increases DOWNWARD (0→767)\n⚠️ FORMAT: [X, Y] - horizontal first, then vertical\n⚠️ CO WIDZISZ NA TYM SCREENSHOCIE? OPISZ I PODEJMIJ DECYZJĘ O KOLEJNEJ AKCJI."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_data['data']}"
                                }
                            }
                        ]
                    }
                    chat_history.append(user_screenshot_message)
                else:
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_result["tool_call_id"],
                        "content": tool_result["content"]
                    }
                    chat_history.append(tool_message)
                
                # INFINITE LOOP: Po akcji kontynuujemy automatycznie bez delayów
                # Continue to next iteration of while True loop
            
            else:
                # No tool calls - AI is just sending text
                if full_text:
                    message_counter += 1
                    
                    # Normal text message - add to history and continue loop
                    chat_history.append({
                        "role": "assistant",
                        "content": full_text
                    })
                    
                    # Check if AI wants to finish
                    if wants_to_finish:
                        break
                
                # Continue loop - AI will execute next action or send another message
    
    except Exception as error:
        print(f"Chat API error: {error}")
        # Kill desktop on error
        try:
            await kernel_client.browsers.delete_by_id(sandbox_id)
        except:
            pass
        yield send_event({
            "type": "error",
            "errorText": str(error)
        })
