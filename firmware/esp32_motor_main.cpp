#include <Arduino.h>                                                                                           
#include <HardwareSerial.h>                                                                                    
#include <ESP32Servo.h>                                                                                        
                                                                                                               
// Motor pins for differential drive                                                                           
#define MOTOR_A_IN1 12                                                                                         
#define MOTOR_A_IN2 14                                                                                         
#define MOTOR_B_IN1 27                                                                                         
#define MOTOR_B_IN2 26                                                                                         
                                                                                                               
// Arm pins                                                                                                    
#define SERVO_PIN 13          // Gripper servo                                                                 
#define LIFT_MOTOR_IN1 32     // Lift motor direction 1                                                        
#define LIFT_MOTOR_IN2 33     // Lift motor direction 2                                                        
#define LIFT_MOTOR_PWM 25     // Lift motor speed (PWM)                                                        
                                                                                                               
// Serial communication                                                                                        
HardwareSerial SerialPort(2); // Use UART2 (RX=16, TX=17)                                                      
                                                                                                               
struct MotorCommand {                                                                                          
  float linear_x;                                                                                              
  float angular_z;                                                                                             
};                                                                                                             
                                                                                                               
MotorCommand current_cmd = {0.0, 0.0};                                                                         
Servo grip_servo;                                                                                              
                                                                                                               
// Arm state                                                                                                   
float lift_speed = 0.0;   // -1..1                                                                             
float grip_angle = 90.0;  // 0..180                                                                            
                                                                                                               
void setup() {                                                                                                 
  Serial.begin(115200);                                                                                        
  SerialPort.begin(115200, SERIAL_8N1, 16, 17);                                                                
                                                                                                               
  // Differential drive motors                                                                                 
  pinMode(MOTOR_A_IN1, OUTPUT);                                                                                
  pinMode(MOTOR_A_IN2, OUTPUT);                                                                                
  pinMode(MOTOR_B_IN1, OUTPUT);                                                                                
  pinMode(MOTOR_B_IN2, OUTPUT);                                                                                
                                                                                                               
  // Arm motors                                                                                                
  pinMode(LIFT_MOTOR_IN1, OUTPUT);                                                                             
  pinMode(LIFT_MOTOR_IN2, OUTPUT);                                                                             
  pinMode(LIFT_MOTOR_PWM, OUTPUT);                                                                             
                                                                                                               
  // Initialize motors stopped                                                                                 
  digitalWrite(MOTOR_A_IN1, LOW);                                                                              
  digitalWrite(MOTOR_A_IN2, LOW);                                                                              
  digitalWrite(MOTOR_B_IN1, LOW);                                                                              
  digitalWrite(MOTOR_B_IN2, LOW);                                                                              
  digitalWrite(LIFT_MOTOR_IN1, LOW);                                                                           
  digitalWrite(LIFT_MOTOR_IN2, LOW);                                                                           
  analogWrite(LIFT_MOTOR_PWM, 0);                                                                              
                                                                                                               
  // Setup gripper servo                                                                                       
  grip_servo.attach(SERVO_PIN);                                                                                
  grip_servo.write(grip_angle);                                                                                
                                                                                                               
  Serial.println("ESP32 Motor & Arm Controller Ready");                                                        
}                                                                                                              
                                                                                                               
void loop() {                                                                                                  
  // Check for incoming data                                                                                   
  if (SerialPort.available() >= 4) {                                                                           
    char header[4];                                                                                            
    SerialPort.readBytes(header, 4);                                                                           
                                                                                                               
    if (header[0] == 'A' && header[1] == 'R' && header[2] == 'M' && header[3] == '2') {                        
      // New arm command: 8 bytes (two floats)                                                                 
      if (SerialPort.available() >= 8) {                                                                       
        uint8_t buffer[8];                                                                                     
        SerialPort.readBytes(buffer, 8);                                                                       
        memcpy(&lift_speed, buffer, 4);                                                                        
        memcpy(&grip_angle, buffer + 4, 4);                                                                    
                                                                                                               
        // Clamp values                                                                                        
        lift_speed = constrain(lift_speed, -1.0, 1.0);                                                         
        grip_angle = constrain(grip_angle, 0.0, 180.0);                                                        
                                                                                                               
        // Apply gripper angle                                                                                 
        grip_servo.write((int)grip_angle);                                                                     
                                                                                                               
        // Apply lift motor speed (simplified: direction + PWM)                                                
        int pwm_val = (int)(abs(lift_speed) * 255);                                                            
        if (lift_speed > 0.1) {                                                                                
          digitalWrite(LIFT_MOTOR_IN1, HIGH);                                                                  
          digitalWrite(LIFT_MOTOR_IN2, LOW);                                                                   
          analogWrite(LIFT_MOTOR_PWM, pwm_val);                                                                
        } else if (lift_speed < -0.1) {                                                                        
          digitalWrite(LIFT_MOTOR_IN1, LOW);                                                                   
          digitalWrite(LIFT_MOTOR_IN2, HIGH);                                                                  
          analogWrite(LIFT_MOTOR_PWM, pwm_val);                                                                
        } else {                                                                                               
          digitalWrite(LIFT_MOTOR_IN1, LOW);                                                                   
          digitalWrite(LIFT_MOTOR_IN2, LOW);                                                                   
          analogWrite(LIFT_MOTOR_PWM, 0);                                                                      
        }                                                                                                      
                                                                                                               
        Serial.printf("Arm: lift=%.2f, grip=%.1f\n", lift_speed, grip_angle);                                  
      }                                                                                                        
    } else {                                                                                                   
      // Not an ARM2 header, maybe it's a motor command (8 bytes without header)                               
      // We need to rewind the serial buffer – simpler: we'll handle motor commands                            
      // in a separate block below (they have no header)                                                       
    }                                                                                                          
  }                                                                                                            
                                                                                                               
  // Motor command handling (8 bytes, no header)                                                               
  if (SerialPort.available() >= 8) {                                                                           
    uint8_t buffer[8];                                                                                         
    SerialPort.readBytes(buffer, 8);                                                                           
    memcpy(&current_cmd.linear_x, buffer, 4);                                                                  
    memcpy(&current_cmd.angular_z, buffer + 4, 4);                                                             
                                                                                                               
    Serial.printf("Drive: linear=%.2f, angular=%.2f\n",                                                        
                  current_cmd.linear_x, current_cmd.angular_z);                                                
  }                                                                                                            
                                                                                                               
  // Differential drive conversion                                                                             
  float left_speed = current_cmd.linear_x - current_cmd.angular_z;                                             
  float right_speed = current_cmd.linear_x + current_cmd.angular_z;                                            
                                                                                                               
  left_speed = constrain(left_speed, -1.0, 1.0);                                                               
  right_speed = constrain(right_speed, -1.0, 1.0);                                                             
                                                                                                               
  // Left motor                                                                                                
  if (left_speed > 0.1) {                                                                                      
    digitalWrite(MOTOR_A_IN1, HIGH);                                                                           
    digitalWrite(MOTOR_A_IN2, LOW);                                                                            
  } else if (left_speed < -0.1) {                                                                              
    digitalWrite(MOTOR_A_IN1, LOW);                                                                            
    digitalWrite(MOTOR_A_IN2, HIGH);                                                                           
  } else {                                                                                                     
    digitalWrite(MOTOR_A_IN1, LOW);                                                                            
    digitalWrite(MOTOR_A_IN2, LOW);                                                                            
  }                                                                                                            
                                                                                                               
  // Right motor                                                                                               
  if (right_speed > 0.1) {                                                                                     
    digitalWrite(MOTOR_B_IN1, HIGH);                                                                           
    digitalWrite(MOTOR_B_IN2, LOW);                                                                            
  } else if (right_speed < -0.1) {                                                                             
    digitalWrite(MOTOR_B_IN1, LOW);                                                                            
    digitalWrite(MOTOR_B_IN2, HIGH);                                                                           
  } else {                                                                                                     
    digitalWrite(MOTOR_B_IN1, LOW);                                                                            
    digitalWrite(MOTOR_B_IN2, LOW);                                                                            
  }                                                                                                            
                                                                                                               
  delay(10);                                                                                                   
}                                   