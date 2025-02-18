#include <AccelStepper.h>

// Define motor pins
#define StepX 2    // Step pin for X-axis
#define DirX 5     // Direction pin for X-axis
#define StepY 3    // Step pin for Y-axis
#define DirY 6     // Direction pin for Y-axis
#define StepZ 4    // Step pin for Z-axis
#define DirZ 7     // Direction pin for Z-axis

// Initialize AccelStepper objects for each axis
// AccelStepper::DRIVER indicates the use of a driver that takes STEP and DIR signals
AccelStepper stepperX(AccelStepper::DRIVER, StepX, DirX);
AccelStepper stepperY(AccelStepper::DRIVER, StepY, DirY);
AccelStepper stepperZ(AccelStepper::DRIVER, StepZ, DirZ);

// Function prototypes
void handleSetCommand(String command);
void handleMoveAbsCommand(String command);
void handleMoveRelCommand(String command);
void handleStopCommand();
void handlePositionCommand();
void handleSetCurrentPositionCommand(); // New function prototype

void setup() {
  Serial.begin(115200); // Initialize serial communication at 115200 baud

  // ===============================
  // Configuration Parameters Start
  // ===============================

  // -------------------------------
  // X and Y Axes Configuration
  // -------------------------------
  // These parameters control the behavior of the X and Y axes.

  // Maximum speed (steps per second)
  // Adjust this value based on your motor's specifications and desired speed.
  stepperX.setMaxSpeed(1000);    // X-axis max speed
  stepperY.setMaxSpeed(1000);    // Y-axis max speed

  // Acceleration (steps per second squared)
  // Higher acceleration allows faster speed changes but may cause jitter if too high.
  stepperX.setAcceleration(500); // X-axis acceleration
  stepperY.setAcceleration(500); // Y-axis acceleration

  // -------------------------------
  // Z Axis Configuration
  // -------------------------------
  // The Z-axis is now configured to move with acceleration and deceleration.

  // Maximum speed (steps per second)
  // Adjust this value based on your motor's specifications and desired speed.
  stepperZ.setMaxSpeed(1000);    // Z-axis max speed

  // Acceleration (steps per second squared)
  // Setting acceleration allows the Z-axis to ramp up and down smoothly.
  stepperZ.setAcceleration(500); // Z-axis acceleration

  // ===============================
  // Configuration Parameters End
  // ===============================

  // Optionally, set initial positions to zero
  stepperX.setCurrentPosition(0);
  stepperY.setCurrentPosition(0);
  stepperZ.setCurrentPosition(0);
}

void loop() {
  // Check if data is available on the Serial port
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // Read the incoming command until newline
    command.trim(); // Remove any leading/trailing whitespace

    // Parse and handle the command based on its prefix
    if (command.startsWith("SET ")) { // Note: added space to ensure 'SET ' is matched
      handleSetCommand(command);
    } else if (command.startsWith("MOVEABS")) {
      handleMoveAbsCommand(command);
    } else if (command.startsWith("MOVEREL")) {
      handleMoveRelCommand(command);
    } else if (command.startsWith("STOP")) {
      handleStopCommand();
    } else if (command.startsWith("POSITION")) {
      handlePositionCommand();
    } else if (command.startsWith("SETCURRENTPOS")) { // New command
      handleSetCurrentPositionCommand();
    } else {
      Serial.println("Invalid command.");
    }
  }

  // Run all steppers with acceleration
  stepperX.run(); // Handles movement with acceleration for X-axis
  stepperY.run(); // Handles movement with acceleration for Y-axis
  stepperZ.run(); // Handles movement with acceleration for Z-axis
}

// ===============================
// Command Handler Functions Start
// ===============================

// Handles the SET command to configure speed and acceleration for a specific axis
// Example command format: SET X 1500 750
void handleSetCommand(String command) {
  // Ensure the command has enough length to parse
  if (command.length() < 6) {
    Serial.println("Invalid SET command format.");
    return;
  }

  char axis = command.charAt(4); // Get the axis character (X, Y, or Z)
  int speedStart = 6;             // Starting index for speed value
  int space1 = command.indexOf(' ', speedStart); // Find space after speed

  // Check if both speed and acceleration are provided
  // Z-axis now also requires acceleration
  if (space1 == -1) {
    Serial.println("Invalid SET command format. Usage: SET <Axis> <Speed> <Acceleration>");
    return;
  }

  // Extract speed and acceleration values
  int speed = command.substring(speedStart, space1).toInt();
  int accel = command.substring(space1 + 1).toInt();

  // Update the corresponding stepper's speed and acceleration
  if (axis == 'X') {
    stepperX.setMaxSpeed(speed);
    stepperX.setAcceleration(accel);
    Serial.println("X Speed and Acceleration set.");
  } else if (axis == 'Y') {
    stepperY.setMaxSpeed(speed);
    stepperY.setAcceleration(accel);
    Serial.println("Y Speed and Acceleration set.");
  } else if (axis == 'Z') {
    // For Z-axis, set both speed and acceleration
    stepperZ.setMaxSpeed(speed);
    stepperZ.setAcceleration(accel);
    Serial.println("Z Speed and Acceleration set.");
  } else {
    Serial.println("Invalid axis. Use X, Y, or Z.");
  }
}

// Handles the MOVEABS command to move all axes to absolute positions
// Example command format: MOVEABS 1000 2000 3000
void handleMoveAbsCommand(String command) {
  // Expected format: MOVEABS <X_Pos> <Y_Pos> <Z_Pos>
  // Example: MOVEABS 1000 2000 3000

  // Split the command into tokens based on spaces
  int firstSpace = command.indexOf(' ');
  if (firstSpace == -1) {
    Serial.println("Invalid MOVEABS command format.");
    return;
  }

  // Extract the positions for X, Y, and Z
  String params = command.substring(firstSpace + 1);
  int paramCount = 0;
  long positions[3] = {0, 0, 0};
  int prevIndex = 0;
  int spaceIndex;

  while (paramCount < 2 && (spaceIndex = params.indexOf(' ', prevIndex)) != -1) {
    positions[paramCount] = params.substring(prevIndex, spaceIndex).toInt();
    paramCount++;
    prevIndex = spaceIndex + 1;
  }

  // Capture the last parameter (Z position)
  if (paramCount < 3) {
    positions[paramCount] = params.substring(prevIndex).toInt();
    paramCount++;
  }

  // Validate that three parameters were received
  if (paramCount != 3) {
    Serial.println("Invalid MOVEABS command format. Usage: MOVEABS <X_Pos> <Y_Pos> <Z_Pos>");
    return;
  }

  // Set the target positions for each stepper
  stepperX.moveTo(positions[0]);
  stepperY.moveTo(positions[1]);
  stepperZ.moveTo(positions[2]);

  Serial.println("Move to Absolute positions initiated.");
}

// Handles the MOVEREL command to move all axes by relative amounts
// Example command format: MOVEREL 100 -50 25
void handleMoveRelCommand(String command) {
  // Expected format: MOVEREL <X_Delta> <Y_Delta> <Z_Delta>
  // Example: MOVEREL 100 -50 25

  // Split the command into tokens based on spaces
  int firstSpace = command.indexOf(' ');
  if (firstSpace == -1) {
    Serial.println("Invalid MOVEREL command format.");
    return;
  }

  // Extract the relative movements for X, Y, and Z
  String params = command.substring(firstSpace + 1);
  int paramCount = 0;
  long deltas[3] = {0, 0, 0};
  int prevIndex = 0;
  int spaceIndex;

  while (paramCount < 2 && (spaceIndex = params.indexOf(' ', prevIndex)) != -1) {
    deltas[paramCount] = params.substring(prevIndex, spaceIndex).toInt();
    paramCount++;
    prevIndex = spaceIndex + 1;
  }

  // Capture the last parameter (Z delta)
  if (paramCount < 3) {
    deltas[paramCount] = params.substring(prevIndex).toInt();
    paramCount++;
  }

  // Validate that three parameters were received
  if (paramCount != 3) {
    Serial.println("Invalid MOVEREL command format. Usage: MOVEREL <X_Delta> <Y_Delta> <Z_Delta>");
    return;
  }

  // Calculate new target positions by adding deltas to current positions
  long newX = stepperX.currentPosition() + deltas[0];
  long newY = stepperY.currentPosition() + deltas[1];
  long newZ = stepperZ.currentPosition() + deltas[2];

  // Set the target positions for each stepper
  stepperX.moveTo(newX);
  stepperY.moveTo(newY);
  stepperZ.moveTo(newZ);

  Serial.println("Move Relative command executed.");
}

// Handles the STOP command to halt all steppers immediately
void handleStopCommand() {
  // Decelerate all steppers to a stop
  stepperX.stop(); // Gracefully stops X-axis with deceleration
  stepperY.stop(); // Gracefully stops Y-axis with deceleration
  stepperZ.stop(); // Gracefully stops Z-axis with deceleration

  Serial.println("Motors stopping.");
}

// Handles the POSITION command to report current positions of all steppers
void handlePositionCommand() {
  // Retrieve and print the current position of each stepper
  Serial.print("X:");
  Serial.print(stepperX.currentPosition());
  Serial.print("Y:");
  Serial.print(stepperY.currentPosition());
  Serial.print("Z:");
  Serial.println(stepperZ.currentPosition());
}

// ===============================
// Command Handler Functions End
// ===============================

// ===============================
// New Command Handler: SETCURRENTPOS Start
// ===============================

// Handles the SETCURRENTPOS command to reset all current positions to zero
void handleSetCurrentPositionCommand() {
  stepperX.setCurrentPosition(0);
  stepperY.setCurrentPosition(0);
  stepperZ.setCurrentPosition(0);
  Serial.println("Current positions set to zero.");
}

// ===============================
// New Command Handler: SETCURRENTPOS End
// ===============================
