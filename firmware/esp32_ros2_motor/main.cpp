#include <Arduino.h>                                                                                           
#include <HardwareSerial.h>                                                                                    
#include <ESP32Servo.h>                                                                                        
                                                                                                               
// Motor pins                                                                                                  
#define MOTOR_A_IN1 12                                                                                         
#define MOTOR_A_IN2 14                                                                                         
#define MOTOR_B_IN1 27                                                                                         
#define MOTOR_B_IN2 26                                                                                         
#define SERVO_PIN 13                                                                                           
                                                                                                               
// Serial communication                                                                                        
HardwareSerial SerialPort(2); // Use UART2                                                                     
                                                                                                               
struct MotorCommand {                                                                                          
  float linear_x;                                                                                              
  float angular_z;                                                                                             
};                                                                                                             
                                                                                                               
MotorCommand current_cmd = {0.0, 0.0};                                                                         
Servo arm_servo;                                                                                               
                                                                                                               
void setup() {                                                                                                 
  Serial.begin(115200);                                                                                        
  SerialPort.begin(115200, SERIAL_8N1, 16, 17); // RX=16, TX=17                                                
                                                                                                               
  pinMode(MOTOR_A_IN1, OUTPUT);                                                                                
  pinMode(MOTOR_A_IN2, OUTPUT);                                                                                
  pinMode(MOTOR_B_IN1, OUTPUT);                                                                                
  pinMode(MOTOR_B_IN2, OUTPUT);                                                                                
                                                                                                               
  // Initialize motors stopped                                                                                 
  digitalWrite(MOTOR_A_IN1, LOW);                                                                              
  digitalWrite(MOTOR_A_IN2, LOW);                                                                              
  digitalWrite(MOTOR_B_IN1, LOW);                                                                              
  digitalWrite(MOTOR_B_IN2, LOW);                                                                              
                                                                                                               
  // Setup servo                                                                                               
  arm_servo.attach(SERVO_PIN);                                                                                 
  arm_servo.write(90); // initial position                                                                     
                                                                                                               
  Serial.println("ESP32 Motor & Arm Controller Ready");                                                        
}                                                                                                              
                                                                                                               
void loop() {                                                                                                  
  // Check for incoming data                                                                                   
  if (SerialPort.available() >= 3) {                                                                           
    char header[3];                                                                                            
    SerialPort.readBytes(header, 3);                                                                           
                                                                                                               
    if (header[0] == 'A' && header[1] == 'R' && header[2] == 'M') {                                            
      // Arm command: 4 bytes float                                                                            
      if (SerialPort.available() >= 4) {                                                                       
        uint8_t buffer[4];                                                                                     
        SerialPort.readBytes(buffer, 4);                                                                       
        float angle;                                                                                           
        memcpy(&angle, buffer, 4);                                                                             
        angle = constrain(angle, 0.0, 180.0);                                                                  
        arm_servo.write((int)angle);                                                                           
        Serial.printf("Arm angle set to: %.1f\n", angle);                                                      
      }                                                                                                        
    } else {                                                                                                   
      // Motor command: need 8 more bytes (total 11, but we already read 3)                                    
      // Put back the header bytes to buffer for motor processing                                              
      // Simpler: we'll handle motor commands separately                                                       
    }                                                                                                          
  }                                                                                                            
                                                                                                               
  // Motor command handling (8 bytes)                                                                          
  if (SerialPort.available() >= 8) {                                                                           
    uint8_t buffer[8];                                                                                         
    SerialPort.readBytes(buffer, 8);                                                                           
    memcpy(&current_cmd.linear_x, buffer, 4);                                                                  
    memcpy(&current_cmd.angular_z, buffer + 4, 4);                                                             
                                                                                                               
    Serial.printf("Received: linear=%.2f, angular=%.2f\n",                                                     
                  current_cmd.linear_x, current_cmd.angular_z);                                                
  }                                                                                                            
                                                                                                               
  // Simple differential drive conversion                                                                      
  float left_speed = current_cmd.linear_x - current_cmd.angular_z;                                             
  float right_speed = current_cmd.linear_x + current_cmd.angular_z;                                            
                                                                                                               
  // Clamp to [-1, 1]                                                                                          
  left_speed = constrain(left_speed, -1.0, 1.0);                                                               
  right_speed = constrain(right_speed, -1.0, 1.0);                                                             
                                                                                                               
  // Drive motors (simplified PWM)                                                                             
  // In real implementation, use PWM and motor driver logic                                                    
  // This is just example                                                                                      
  if (left_speed > 0) {                                                                                        
    digitalWrite(MOTOR_A_IN1, HIGH);                                                                           
    digitalWrite(MOTOR_A_IN2, LOW);                                                                            
  } else if (left_speed < 0) {                                                                                 
    digitalWrite(MOTOR_A_IN1, LOW);                                                                            
    digitalWrite(MOTOR_A_IN2, HIGH);                                                                           
  } else {                                                                                                     
    digitalWrite(MOTOR_A_IN1, LOW);                                                                            
    digitalWrite(MOTOR_A_IN2, LOW);                                                                            
  }                                                                                                            
                                                                                                               
  if (right_speed > 0) {                                                                                       
    digitalWrite(MOTOR_B_IN1, HIGH);                                                                           
    digitalWrite(MOTOR_B_IN2, LOW);                                                                            
  } else if (right_speed < 0) {                                                                                
    digitalWrite(MOTOR_B_IN1, LOW);                                                                            
    digitalWrite(MOTOR_B_IN2, HIGH);                                                                           
  } else {                                                                                                     
    digitalWrite(MOTOR_B_IN1, LOW);                                                                            
    digitalWrite(MOTOR_B_IN2, LOW);                                                                            
  }                                                                                                            
                                                                                                               
  delay(10);                                                                                                   
}                                   