"""Tool execution module - executes computer control and workflow tools"""
import asyncio
import base64
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

RESOLUTION = {"x": 1024, "y": 768}


async def execute_tool(
    tool_call: Dict,
    parsed_args: Dict,
    desktop,
    kernel_client
) -> Tuple[Optional[Dict], Dict, List[Dict]]:
    """
    Execute a tool call (computer_use or update_workflow)
    Returns: (screenshot_data, tool_result, events_to_send)
    """
    screenshot_data = None
    events_to_send = []
    
    try:
        result_data = {"type": "text", "text": ""}
        result_text = ""
        
        if tool_call["name"] == "computer_use":
            action = parsed_args["action"]
            
            if action == "screenshot":
                response = await kernel_client.browsers.computer.capture_screenshot(desktop.session_id)
                blob_data = await response.read()
                buffer = blob_data
                
                timestamp = datetime.now().isoformat()
                width = RESOLUTION["x"]
                height = RESOLUTION["y"]
                base64_image = base64.b64encode(buffer).decode('utf-8')
                
                screenshot_data = {
                    "type": "image",
                    "data": base64_image,
                    "timestamp": timestamp,
                    "width": width,
                    "height": height
                }
                
                result_text = f"""Screenshot taken at {timestamp}

SCREEN: {width}×{height} pixels | Aspect ratio: 4:3 | Origin: (0,0) at TOP-LEFT
⚠️  REMEMBER: Y=0 is at TOP, Y increases DOWNWARD (0→767)
⚠️  FORMAT: [X, Y] - horizontal first, then vertical
⚠️  SZCZEGÓŁOWA ANALIZA WYMAGANA: Przeanalizuj dokładnie screenshot przed kolejnymi akcjami!"""
                
                result_data = {
                    "type": "image",
                    "data": base64_image
                }
                
                events_to_send.append({
                    "type": "screenshot-update",
                    "screenshot": base64_image
                })
            
            elif action == "wait":
                duration = parsed_args.get("duration", 1)
                await asyncio.sleep(duration)
                result_text = f"Waited for {duration} seconds"
                result_data = {"type": "text", "text": result_text}
            
            elif action == "left_click":
                x, y = parsed_args["coordinate"]
                await kernel_client.browsers.computer.click_mouse(
                    desktop.session_id,
                    x=round(x),
                    y=round(y),
                    button='left'
                )
                result_text = f"Left clicked at coordinates ({round(x)}, {round(y)})"
                result_data = {"type": "text", "text": result_text}
            
            elif action == "double_click":
                x, y = parsed_args["coordinate"]
                await kernel_client.browsers.computer.click_mouse(
                    desktop.session_id,
                    x=round(x),
                    y=round(y),
                    button='left',
                    num_clicks=2
                )
                result_text = f"Double clicked at coordinates ({round(x)}, {round(y)})"
                result_data = {"type": "text", "text": result_text}
            
            elif action == "right_click":
                x, y = parsed_args["coordinate"]
                await kernel_client.browsers.computer.click_mouse(
                    desktop.session_id,
                    x=round(x),
                    y=round(y),
                    button='right'
                )
                result_text = f"Right clicked at coordinates ({round(x)}, {round(y)})"
                result_data = {"type": "text", "text": result_text}
            
            elif action == "mouse_move":
                x, y = parsed_args["coordinate"]
                await kernel_client.browsers.computer.move_mouse(
                    desktop.session_id,
                    x=round(x),
                    y=round(y)
                )
                result_text = f"Moved mouse to {round(x)}, {round(y)}"
                result_data = {"type": "text", "text": result_text}
            
            elif action == "type":
                text_to_type = parsed_args["text"]
                await kernel_client.browsers.computer.type_text(
                    desktop.session_id,
                    text=text_to_type
                )
                result_text = f"Typed: {text_to_type}"
                result_data = {"type": "text", "text": result_text}
            
            elif action == "key":
                key_to_press = parsed_args["text"]
                
                # OnKernel uses X11 keysym names - convert common variants to X11 format
                if key_to_press in ["Enter", "enter"]:
                    key_to_press = "Return"
                
                await kernel_client.browsers.computer.press_key(
                    desktop.session_id,
                    keys=[key_to_press]
                )
                result_text = f"Pressed key: {parsed_args['text']}"
                result_data = {"type": "text", "text": result_text}
            
            elif action == "scroll":
                coordinate = parsed_args.get("coordinate", [512, 384])
                x, y = coordinate
                delta_x = parsed_args.get("delta_x", 0)
                delta_y = parsed_args.get("delta_y", 0)
                await kernel_client.browsers.computer.scroll(
                    desktop.session_id,
                    x=round(x),
                    y=round(y),
                    delta_x=round(delta_x),
                    delta_y=round(delta_y)
                )
                result_text = f"Scrolled at ({round(x)}, {round(y)}) with delta_x: {round(delta_x)}, delta_y: {round(delta_y)}"
                result_data = {"type": "text", "text": result_text}
            
            elif action == "left_click_drag":
                start_x, start_y = parsed_args["start_coordinate"]
                end_x, end_y = parsed_args["coordinate"]
                await kernel_client.browsers.computer.drag_mouse(
                    desktop.session_id,
                    path=[[round(start_x), round(start_y)], [round(end_x), round(end_y)]],
                    button='left'
                )
                result_text = f"Dragged from ({round(start_x)}, {round(start_y)}) to ({round(end_x)}, {round(end_y)})"
                result_data = {"type": "text", "text": result_text}
            
            else:
                result_text = f"Unknown action: {action}"
                result_data = {"type": "text", "text": result_text}
                print(f"Unknown action: {action}")
            
            events_to_send.append({
                "type": "tool-output-available",
                "toolCallId": tool_call["id"],
                "output": result_data
            })
            
            tool_result = {
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "content": result_text,
                "image": result_data.get("data") if action == "screenshot" else None
            }
        
        elif tool_call["name"] == "update_workflow":
            workflow_data = parsed_args
            
            events_to_send.append({
                "type": "workflow-update",
                "workflow": workflow_data,
                "timestamp": datetime.now().isoformat()
            })
            
            events_to_send.append({
                "type": "tool-output-available",
                "toolCallId": tool_call["id"],
                "output": {"type": "text", "text": "Workflow updated"}
            })
            
            tool_result = {
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "content": "Workflow updated successfully. Continue with the next action."
            }
        
        else:
            tool_result = {
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "content": f"Unknown tool: {tool_call['name']}"
            }
    
    except Exception as error:
        print(f"Error executing tool: {error}")
        error_msg = str(error)
        detailed_error = f"Error: {error_msg}"
        
        if 'Failed to type' in error_msg:
            detailed_error += '\n\nSuggestion: The text field might not be active. Try clicking on the text field first before typing.'
        elif any(x in error_msg for x in ['Failed to click', 'Failed to double click', 'Failed to right click']):
            detailed_error += '\n\nSuggestion: The click action failed. Take a screenshot to see what happened, then try clicking again.'
        elif 'Failed to take screenshot' in error_msg:
            detailed_error += '\n\nSuggestion: Screenshot failed. The desktop might be loading. Wait a moment and try again.'
        elif 'Failed to press key' in error_msg:
            detailed_error += '\n\nSuggestion: Key press failed. Make sure the correct window is focused.'
        elif 'Failed to move mouse' in error_msg:
            detailed_error += '\n\nSuggestion: Mouse movement failed. Try again.'
        elif 'Failed to drag' in error_msg:
            detailed_error += '\n\nSuggestion: Drag operation failed. Try again with different coordinates.'
        elif 'Failed to scroll' in error_msg:
            detailed_error += '\n\nSuggestion: Scroll failed. Make sure a scrollable window is active.'
        
        events_to_send.append({
            "type": "error",
            "errorText": error_msg
        })
        
        tool_result = {
            "tool_call_id": tool_call["id"],
            "role": "tool",
            "content": detailed_error
        }
    
    return screenshot_data, tool_result, events_to_send
