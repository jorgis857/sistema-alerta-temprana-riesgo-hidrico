#include "wokwi-api.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define INA219_ADDRESS 0x40

typedef struct {
  i2c_dev_t i2c;

  pin_t vin_plus;
  pin_t vin_minus;

  uint8_t selected_register;
  uint8_t read_index;

} chip_state_t;


// --------------------------------------------------
// Leer la señal que llega desde el panel solar
// --------------------------------------------------

static float get_panel_voltage(chip_state_t *chip) {

  float vplus = pin_adc_read(chip->vin_plus);
  float vminus = pin_adc_read(chip->vin_minus);

  float voltage = vplus - vminus;

  if (voltage < 0) {
    voltage = 0;
  }

  return voltage;
}


// --------------------------------------------------
// Convertir señal del panel a corriente simulada
//
// Nuestro modelo:
// 0 V -> 0 mA
// 5 V -> 100 mA
//
// Más adelante podremos cambiar 100 mA
// por la Isc REAL de la celda que compremos.
// --------------------------------------------------

static float get_current_ma(chip_state_t *chip) {

  float voltage = get_panel_voltage(chip);

  float current_ma =
      (voltage / 5.0f) * 120.0f;

  return current_ma;
}


// --------------------------------------------------
// I2C
// --------------------------------------------------

static bool on_i2c_connect(
  void *user_data,
  uint32_t address,
  bool read
) {

  chip_state_t *chip = (chip_state_t *)user_data;

  if (address == INA219_ADDRESS) {

    if (read) {
      chip->read_index = 0;
    }

    return true;
  }

  return false;
}


// --------------------------------------------------
// Lectura de registros
// --------------------------------------------------

static uint8_t on_i2c_read(void *user_data) {

  chip_state_t *chip =
      (chip_state_t *)user_data;

  float current_ma =
      get_current_ma(chip);

  /*
   * Guardaremos corriente × 100
   *
   * Ejemplo:
   *
   * 42.35 mA
   *
   * se convierte en:
   *
   * 4235
   */

  uint16_t current_raw =
      (uint16_t)(current_ma * 100.0f);

  uint8_t result = 0;

  switch (chip->selected_register) {

    // Registro custom de corriente
    case 0x04:

      if (chip->read_index == 0) {

        result =
            (current_raw >> 8) & 0xFF;

      } else {

        result =
            current_raw & 0xFF;
      }

      chip->read_index++;

      break;


    // Registro de identificación simple
    case 0xFF:

      if (chip->read_index == 0) {
        result = 0x21;
      } else {
        result = 0x90;
      }

      chip->read_index++;

      break;


    default:

      result = 0;

      break;
  }

  return result;
}


// --------------------------------------------------
// Escritura I2C
// --------------------------------------------------

static bool on_i2c_write(
  void *user_data,
  uint8_t data
) {

  chip_state_t *chip =
      (chip_state_t *)user_data;

  chip->selected_register = data;
  chip->read_index = 0;

  return true;
}


static void on_i2c_disconnect(
  void *user_data
) {
}


// --------------------------------------------------
// Inicialización
// --------------------------------------------------

void chip_init() {

  chip_state_t *chip =
      malloc(sizeof(chip_state_t));

  chip->selected_register = 0;
  chip->read_index = 0;

  chip->vin_plus =
      pin_init("VIN+", ANALOG);

  chip->vin_minus =
      pin_init("VIN-", ANALOG);


  const i2c_config_t i2c_config = {

    .address = INA219_ADDRESS,

    .scl =
        pin_init("SCL", INPUT_PULLUP),

    .sda =
        pin_init("SDA", INPUT_PULLUP),

    .connect =
        on_i2c_connect,

    .read =
        on_i2c_read,

    .write =
        on_i2c_write,

    .disconnect =
        on_i2c_disconnect,

    .user_data =
        chip,
  };


  chip->i2c =
      i2c_init(&i2c_config);


  printf(
    "INA219 Custom iniciado en 0x40\n"
  );
}