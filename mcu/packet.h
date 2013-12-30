#ifndef PACKET_H
#define PACKET_H

#include <stdint.h>

#define START_BYTE 0xFE
#define BOOT_PACKET 0x00
#define DATA_PACKET 0x01
#define NUM_RAW_BYTES 8

// Defines the boot packet structure
typedef struct {
	// Header
	uint8_t start[3];
	uint8_t type;
	// Non-zero if our BMP sensor was sucessfully initialized
	uint8_t bmpSensorOk;
	// Non-zero if our GPS serial communication was successfully initialized
	uint8_t gpsSerialOk;
	// Git info about the code we are running.
    uint32_t commitTimestamp;
    uint8_t commitID[20];
    uint8_t commitStatus;
} BootPacket;

// Defines the data packet structure
typedef struct {
	// Header
	uint8_t start[3];
	uint8_t type;
	// GPS timing info
	uint16_t gpsAlarms;
	uint16_t gpsStatus;
	int16_t utcOffset;
	uint16_t weekNumber;
	uint32_t timeOfWeek;
	// BMP180 sensor measurements
	int32_t temperature;	// divide by 160 to get degrees C
	int32_t pressure;		// in Pascals
	// block thermistor reading
	uint16_t thermistor;	// in ADC counts
	// IR sensor raw ADC readings
	uint16_t rawPhase;
	uint8_t raw[NUM_RAW_BYTES];
} DataPacket;

#endif
