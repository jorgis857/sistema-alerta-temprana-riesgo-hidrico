#include "wokwi-api.h"
#include <stdio.h>
#include <stdlib.h>

typedef struct {
  pin_t pos_pin;
  pin_t neg_pin;

  uint32_t irradiance_attr;
  timer_t timer;
} chip_state_t;

static void update_output(void *user_data) {
  chip_state_t *chip = (chip_state_t *)user_data;

  float irradiance = attr_read_float(chip->irradiance_attr);

  // Simulación funcional:
  // 0 W/m²    -> 0 V
  // 1000 W/m² -> 5 V
  float voltage = (irradiance / 1200.0f) * 5.0f;

  if (voltage > 5.0f) {
    voltage = 5.0f;
  }

  if (voltage < 0.0f) {
    voltage = 0.0f;
  }

  pin_dac_write(chip->pos_pin, voltage);
  pin_dac_write(chip->neg_pin, 0.0f);
}

void chip_init() {
  chip_state_t *chip = malloc(sizeof(chip_state_t));

  chip->pos_pin = pin_init("POS", ANALOG);
  chip->neg_pin = pin_init("NEG", ANALOG);

  chip->irradiance_attr =
      attr_init_float("irradiance", 500.0f);

  const timer_config_t timer_config = {
    .callback = update_output,
    .user_data = chip,
  };

  chip->timer = timer_init(&timer_config);

  timer_start(chip->timer, 100000, true);

  printf("Solar Panel Custom iniciado\n");
}