#include <Arduino.h>
#include <Adafruit_BMP085_U.h>

#include "packet.h"

//Constants
#define BAUD_RATE 115200

//Sensor object
Adafruit_BMP085_Unified bmpSensor = Adafruit_BMP085_Unified(10085);

// Declares and initializes our boot info packet.
BootPacket bootPacket = {
	START_BYTE, START_BYTE, START_BYTE, BOOT_PACKET,
	0,0,
#ifdef COMMIT_INFO
    COMMIT_INFO
#elif
    0, { 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 }, 0
#endif
};

DataPacket dataPacket;

void setup() {
	// We assume that someone is listening since, even if this were not true, who would we tell?
	Serial.begin(BAUD_RATE);
	// Initializes the BMP air pressure & temperature sensor communication via I2C
	if(bmpSensor.begin()) bootPacket.bmpSensorOk = 1;
	// Initializes the GPS serial communication
	// ...
	// bootpacket.gpsSerialOk = 1;
	// ...
	// Sends our boot packet.
	Serial.write((const uint8_t*)&bootPacket,sizeof(bootPacket));
	// Initializes the constant header of our data packet.
	dataPacket.start[0] = START_BYTE;
	dataPacket.start[1] = START_BYTE;
	dataPacket.start[2] = START_BYTE;
	dataPacket.type = DATA_PACKET;
}

void loop() {
	if(bootPacket.bmpSensorOk) {
		// Reads BMP sensors
		bmpSensor.getTemperature(&dataPacket.temperature);
		bmpSensor.getPressure(&dataPacket.pressure);
	}
	// Sends binary packet data
	Serial.write((const uint8_t*)&dataPacket,sizeof(dataPacket));
	// Waits for about 1 sec...
	delay(1000);
}

int main(void) {
	init();
	setup();
	for(;;) {
		loop();
	}
	return 0;
}