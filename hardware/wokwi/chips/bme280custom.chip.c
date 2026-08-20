#include "wokwi-api.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BME280_ADDRESS 0x76

typedef struct {
  i2c_dev_t i2c;
  uint32_t temperature_attr;
  uint32_t humidity_attr;
  uint32_t pressure_attr;

  uint8_t selected_register;
} chip_state_t;


// Convierte temperatura °C a un valor entero simple
static int32_t get_temperature(chip_state_t *chip) {
  float temp = attr_read_float(chip->temperature_attr);
  return (int32_t)(temp * 100);
}

// Humedad %
static uint32_t get_humidity(chip_state_t *chip) {
  float humidity = attr_read_float(chip->humidity_attr);
  return (uint32_t)(humidity * 100);
}

// Presión hPa
static uint32_t get_pressure(chip_state_t *chip) {
  float pressure = attr_read_float(chip->pressure_attr);
  return (uint32_t)(pressure * 100);
}


static bool on_i2c_connect(void *user_data, uint32_t address, bool read) {
  return address == BME280_ADDRESS;
}


static uint8_t on_i2c_read(void *user_data) {

  chip_state_t *chip = (chip_state_t *)user_data;

  int32_t temperature = get_temperature(chip);
  uint32_t humidity = get_humidity(chip);
  uint32_t pressure = get_pressure(chip);

  uint8_t result = 0;

  switch (chip->selected_register) {

    // CHIP ID BME280
    case 0xD0:
      result = 0x60;
      break;

    // Temperatura custom
    case 0xFA:
      result = (temperature >> 8) & 0xFF;
      break;

    case 0xFB:
      result = temperature & 0xFF;
      break;

    // Presión custom
    case 0xF7:
      result = (pressure >> 16) & 0xFF;
      break;

    case 0xF8:
      result = (pressure >> 8) & 0xFF;
      break;

    case 0xF9:
      result = pressure & 0xFF;
      break;

    // Humedad custom
    case 0xFD:
      result = (humidity >> 8) & 0xFF;
      break;

    case 0xFE:
      result = humidity & 0xFF;
      break;

    default:
      result = 0;
      break;
  }

  chip->selected_register++;

  return result;
}


static bool on_i2c_write(void *user_data, uint8_t data) {

  chip_state_t *chip = (chip_state_t *)user_data;

  chip->selected_register = data;

  return true;
}


static void on_i2c_disconnect(void *user_data) {
}


void chip_init() {

  chip_state_t *chip = malloc(sizeof(chip_state_t));

  chip->temperature_attr = attr_init_float("temperature", 25.0);
  chip->humidity_attr = attr_init_float("humidity", 50.0);
  chip->pressure_attr = attr_init_float("pressure", 1013.0);

  const i2c_config_t i2c_config = {
    .address = BME280_ADDRESS,
    .scl = pin_init("SCL", INPUT_PULLUP),
    .sda = pin_init("SDA", INPUT_PULLUP),

    .connect = on_i2c_connect,
    .read = on_i2c_read,
    .write = on_i2c_write,
    .disconnect = on_i2c_disconnect,

    .user_data = chip,
  };

  chip->i2c = i2c_init(&i2c_config);

  printf("BME280 Custom iniciado en direccion 0x76\n");
}