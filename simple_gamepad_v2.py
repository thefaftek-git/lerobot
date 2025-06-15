#!/usr/bin/env python

"""
Simple gamepad control for SO101 -         print("🎮 Gamepad control active! Starting from current positions.")
        print(f"Current gripper state: {'OPEN' if gripper_open else 'CLOSED'}")
        print("Press A to toggle gripper, move sticks to control joints, B to exit")pper toggle and wrist roll control
"""

import time
import logging
import pygame
from lerobot.common.robots.so101_follower.config_so101_follower import SO101FollowerConfig
from lerobot.common.robots.so101_follower.so101_follower import SO101Follower

def simple_gamepad_control():
    """Simple gamepad control - A button toggles gripper, sticks control joints, triggers control shoulder pan."""
    print("Starting simple gamepad control...")
    print("Controls:")
    print("  A button: Toggle gripper open/closed")
    print("  Left stick horizontal: Control wrist roll")
    print("  Left stick vertical: Control wrist flex")
    print("  Right stick horizontal: Control elbow flex")
    print("  Right stick vertical: Control shoulder lift")
    print("  Left trigger: Pan shoulder left")
    print("  Right trigger: Pan shoulder right")
    print("  B button: Exit")
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize pygame and gamepad
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("❌ No gamepad detected. Please connect a gamepad and try again.")
        return
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"✓ Initialized gamepad: {joystick.get_name()}")
    
    # Create robot config and connect
    robot_config = SO101FollowerConfig(port="COM8")
    robot = SO101Follower(robot_config)
    
    try:
        print("Connecting to robot...")
        robot.connect(calibrate=False)
        print("✓ Robot connected successfully!")
        
        # Read current positions from servo motors
        print("Reading current servo positions...")
        current_gripper_pos = robot.bus.read("Present_Position", "gripper", normalize=False)
        current_wrist_roll_pos = robot.bus.read("Present_Position", "wrist_roll", normalize=False)
        current_wrist_flex_pos = robot.bus.read("Present_Position", "wrist_flex", normalize=False)
        current_elbow_flex_pos = robot.bus.read("Present_Position", "elbow_flex", normalize=False)
        current_shoulder_lift_pos = robot.bus.read("Present_Position", "shoulder_lift", normalize=False)
        current_shoulder_pan_pos = robot.bus.read("Present_Position", "shoulder_pan", normalize=False)
        
        print(f"Current positions - Gripper: {current_gripper_pos}, Wrist Roll: {current_wrist_roll_pos}, Wrist Flex: {current_wrist_flex_pos}, Elbow Flex: {current_elbow_flex_pos}, Shoulder Lift: {current_shoulder_lift_pos}, Shoulder Pan: {current_shoulder_pan_pos}")
        
        # Gripper state tracking - determine initial state based on current position
        gripper_open = current_gripper_pos > 2048  # Consider gripper open if position > middle
        last_a_pressed = False          # Control speeds
        wrist_roll_speed = 50  # How fast the wrist moves per stick input
        wrist_flex_speed = 50  # How fast the wrist flexes per stick input
        elbow_flex_speed = 50  # How fast the elbow flexes per stick input
        shoulder_lift_speed = 50  # How fast the shoulder lifts per stick input
        shoulder_pan_speed = 50  # How fast the shoulder pans per trigger input
        
        print("Starting from current positions (no movement on startup)...")
        print(f"\n🎮 Gamepad control active! Starting from current positions.")
        print(f"Current gripper state: {'OPEN' if gripper_open else 'CLOSED'}")
        print("Press A to toggle gripper, move sticks to control wrist/elbow, B to exit")
        
        while True:
            # Handle pygame events
            pygame.event.pump()
            
            # Check A button for gripper toggle
            a_pressed = joystick.get_button(0)  # A button is typically button 0
            
            # Debug: Show button state changes
            if a_pressed != last_a_pressed:
                print(f"🔘 A button: {'PRESSED' if a_pressed else 'RELEASED'}")
            
            if a_pressed and not last_a_pressed:  # Button just pressed (edge detection)
                gripper_open = not gripper_open
                gripper_pos = 4095 if gripper_open else 0  # Raw servo values: 4095 = open, 0 = closed                
                print(f"🤏 Gripper {'OPEN' if gripper_open else 'CLOSED'} (pos: {gripper_pos})")
                robot.bus.write("Goal_Position", "gripper", gripper_pos, normalize=False)
            
            last_a_pressed = a_pressed
            
            # Check left stick horizontal axis for wrist roll
            left_stick_x = joystick.get_axis(0)  # Left stick horizontal axis
            
            # Apply deadzone to prevent drift
            deadzone = 0.1
            if abs(left_stick_x) > deadzone:
                # Calculate new wrist roll position
                wrist_roll_delta = left_stick_x * wrist_roll_speed
                new_wrist_roll_pos = current_wrist_roll_pos - wrist_roll_delta
                
                # Clamp to servo limits (0-4095)
                new_wrist_roll_pos = max(0, min(4095, new_wrist_roll_pos))
                
                if abs(new_wrist_roll_pos - current_wrist_roll_pos) > 1:  # Only update if significant change
                    current_wrist_roll_pos = new_wrist_roll_pos
                    print(f"🔄 Wrist roll: {current_wrist_roll_pos:.0f} (stick: {left_stick_x:.2f})")
                    robot.bus.write("Goal_Position", "wrist_roll", int(current_wrist_roll_pos), normalize=False)
            
            # Check left stick vertical axis for wrist flex
            left_stick_y = joystick.get_axis(1)  # Left stick vertical axis
            
            if abs(left_stick_y) > deadzone:
                # Calculate new wrist flex position
                wrist_flex_delta = left_stick_y * wrist_flex_speed
                new_wrist_flex_pos = current_wrist_flex_pos + wrist_flex_delta
                  # Clamp to servo limits (0-4095)
                new_wrist_flex_pos = max(0, min(4095, new_wrist_flex_pos))
                
                if abs(new_wrist_flex_pos - current_wrist_flex_pos) > 1:  # Only update if significant change
                    current_wrist_flex_pos = new_wrist_flex_pos
                    print(f"🔽 Wrist flex: {current_wrist_flex_pos:.0f} (stick: {left_stick_y:.2f})")
                    robot.bus.write("Goal_Position", "wrist_flex", int(current_wrist_flex_pos), normalize=False)            # Check right stick horizontal axis for elbow flex (avoiding problematic axis 4)
            right_stick_x = joystick.get_axis(3)  # Right stick horizontal axis
            
            if abs(right_stick_x) > deadzone:
                # Calculate new elbow flex position
                elbow_flex_delta = right_stick_x * elbow_flex_speed
                new_elbow_flex_pos = current_elbow_flex_pos + elbow_flex_delta
                
                # Clamp to servo limits (0-4095)
                new_elbow_flex_pos = max(0, min(4095, new_elbow_flex_pos))
                
                if abs(new_elbow_flex_pos - current_elbow_flex_pos) > 1:  # Only update if significant change
                    current_elbow_flex_pos = new_elbow_flex_pos
                    print(f"💪 Elbow flex: {current_elbow_flex_pos:.0f} (stick: {right_stick_x:.2f})")
                    robot.bus.write("Goal_Position", "elbow_flex", int(current_elbow_flex_pos), normalize=False)
            
            # Check right stick vertical axis for shoulder lift
            right_stick_y = joystick.get_axis(2)  # Right stick vertical axis
            
            if abs(right_stick_y) > deadzone:
                # Calculate new shoulder lift position
                shoulder_lift_delta = right_stick_y * shoulder_lift_speed
                new_shoulder_lift_pos = current_shoulder_lift_pos + shoulder_lift_delta
                  # Clamp to servo limits (0-4095)
                new_shoulder_lift_pos = max(0, min(4095, new_shoulder_lift_pos))
                
                if abs(new_shoulder_lift_pos - current_shoulder_lift_pos) > 1:  # Only update if significant change
                    current_shoulder_lift_pos = new_shoulder_lift_pos
                    print(f"🏋️ Shoulder lift: {current_shoulder_lift_pos:.0f} (stick: {right_stick_y:.2f})")
                    robot.bus.write("Goal_Position", "shoulder_lift", int(current_shoulder_lift_pos), normalize=False)
              # Check triggers for shoulder pan control
            left_trigger = joystick.get_axis(4)   # Left trigger (LT)
            right_trigger = joystick.get_axis(5)  # Right trigger (RT)
            
            # Xbox Elite 2 triggers: rest state = -1.0, pressed state = +1.0
            # Convert to 0.0-1.0 range: (trigger + 1.0) / 2.0
            left_trigger_normalized = (left_trigger + 1.0) / 2.0
            right_trigger_normalized = (right_trigger + 1.0) / 2.0
            
            # Use a threshold to determine when they're pressed
            trigger_threshold = 0.1
            
            # Calculate shoulder pan movement based on triggers
            shoulder_pan_input = 0.0
            if left_trigger_normalized > trigger_threshold:
                # Left trigger pressed - pan left (negative direction)
                shoulder_pan_input = -left_trigger_normalized
            elif right_trigger_normalized > trigger_threshold:
                # Right trigger pressed - pan right (positive direction)  
                shoulder_pan_input = right_trigger_normalized
            
            if abs(shoulder_pan_input) > trigger_threshold:
                # Calculate new shoulder pan position
                shoulder_pan_delta = shoulder_pan_input * shoulder_pan_speed
                new_shoulder_pan_pos = current_shoulder_pan_pos + shoulder_pan_delta
                
                # Clamp to servo limits (0-4095)
                new_shoulder_pan_pos = max(0, min(4095, new_shoulder_pan_pos))
                
                if abs(new_shoulder_pan_pos - current_shoulder_pan_pos) > 1:  # Only update if significant change
                    current_shoulder_pan_pos = new_shoulder_pan_pos
                    direction = "LEFT" if shoulder_pan_input < 0 else "RIGHT"
                    trigger_value = left_trigger_normalized if shoulder_pan_input < 0 else right_trigger_normalized
                    print(f"🔄 Shoulder pan {direction}: {current_shoulder_pan_pos:.0f} (trigger: {trigger_value:.2f})")
                    robot.bus.write("Goal_Position", "shoulder_pan", int(current_shoulder_pan_pos), normalize=False)
            
            # Check B button for exit
            if joystick.get_button(1):  # B button is typically button 1
                print("B button pressed - exiting...")
                break
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.01)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("Disconnecting robot...")
        robot.disconnect()
        pygame.quit()
        print("✓ Disconnected")

if __name__ == "__main__":
    simple_gamepad_control()
