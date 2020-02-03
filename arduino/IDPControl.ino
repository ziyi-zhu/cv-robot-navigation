#include <SPI.h>
#include <WiFiNINA.h>

#include "arduino_secrets.h"

//include HttpRequest object library
#include <HttpRequest.h>

#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"

Adafruit_MotorShield AFMS = Adafruit_MotorShield(); 
Adafruit_DCMotor *motor_red = AFMS.getMotor(1); // 
Adafruit_DCMotor *motor_wht = AFMS.getMotor(2); //

//Create an object to handle the HTTP request
HttpRequest httpReq;

///////please enter your sensitive data in the Secret tab/arduino_secrets.h
char ssid[] = SECRET_SSID;        // your network SSID (name)
char pass[] = SECRET_PASS;        // your network password (use for WPA, or use as key for WEP)
int keyIndex = 0;                 // your network key Index number (needed only for WEP)

int status = WL_IDLE_STATUS;
WiFiServer server(80);

int motor_speed = 50;

void turn_right() {
  Serial.println("Motor turning right");
  motor_red->setSpeed(motor_speed);
  motor_wht->setSpeed(motor_speed);
  motor_red->run(FORWARD);
  motor_wht->run(BACKWARD);
}

void turn_left() {
  Serial.println("Motor turning left");
  motor_red->setSpeed(motor_speed);
  motor_wht->setSpeed(motor_speed);
  motor_red->run(BACKWARD);
  motor_wht->run(FORWARD);
}

void move_forward(){
  Serial.println("Motor moving");
  motor_red->setSpeed(motor_speed*4);
  motor_wht->setSpeed(motor_speed*4);
  motor_red->run(FORWARD);
  motor_wht->run(FORWARD);
}

void release_motors() {
  Serial.println("Motor stopped");
  motor_red->run(RELEASE);
  motor_wht->run(RELEASE);
}

void setup() {
  AFMS.begin();
  Serial.begin(9600);      // initialize serial communication

  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // don't continue
    while (true);
  }

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("Please upgrade the firmware");
  }

  // attempt to connect to Wifi network:
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to Network named: ");
    Serial.println(ssid);                   // print the network name (SSID);

    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(ssid, pass);
    // wait 10 seconds for connection:
    delay(10000);
  }
  server.begin();                           // start the web server on port 80
  printWifiStatus();                        // you're connected now, so print out the status
}


void loop() {
  WiFiClient client = server.available();   // listen for incoming clients

  //declare name and value to use the request parameters and cookies
  char name[HTTP_REQ_PARAM_NAME_LENGTH], value[HTTP_REQ_PARAM_VALUE_LENGTH];
  float angle;
  int distance;

  if (client) {                             // if you get a client,
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      if (client.available()) {             // if there's bytes to read from the client,
        char c = client.read();             // read a byte, then      
        httpReq.parseRequest(c);            // parse the received caracter
        
        //IF request has ended -> handle response
        if (httpReq.endOfRequest()) {
          if(httpReq.uri[1] == 'm') {
            //list received parameters GET /move
            for(int i = 1; i <= httpReq.paramCount; i++){
              httpReq.getParam(i, name, value);
              if(name[0] == 'a') angle = atof(value);
              else if(name[0] == 'd') distance = atoi(value);

              if(distance < 0) release_motors();
              else {
                if(angle <= 0.05 && angle >= -0.1) move_forward();
                else if(angle < -0.1) turn_left();
                else if(angle > 0.1) turn_right();  
              }
            }
            client.println("HTTP/1.1 200 OK");
          }

          if(httpReq.uri[1] == 'g') {
            delay(3000);
            client.println("HTTP/1.1 200 OK");
          }
          
          //Reset object and free dynamic allocated memory
          httpReq.resetRequest();
               
          break;
        }     
      }
    }
    // close the connection:
    client.stop();
  }
}

void printWifiStatus() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
  // print where to go in a browser:
  Serial.print("To see this page in action, open a browser to http://");
  Serial.println(ip);
}
