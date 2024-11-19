#include "GPIO_Driver.hpp"
#include "Reset_Clock_Control.hpp"

#define BTN_PRESSED true

const GPIO_CONFIG led_conf = {output, push_pull, high_speed, no_pull};
const GPIO_CONFIG toggle_conf = {output, push_pull, high_speed, no_pull};
const GPIO_CONFIG bt_conf = {input, push_pull, high_speed, no_pull};

RC_Control gRCC_Control = RC_Control();

int main() {
  auto gpio_led_green = GPIO_Driver(PORT_D, PIN_POS_12, led_conf);
  auto gpio_toggler = GPIO_Driver(PORT_E, PIN_POS_15, toggle_conf);
  auto gpio_button = GPIO_Driver(PORT_A, PIN_POS_0, bt_conf);
  asm("nop");  // TEST TAG A
  gpio_led_green.set_pin_val(true);
  asm("nop");  // TEST TAG A
  gpio_led_green.set_pin_val(false);
  asm("nop");  // TEST TAG A
  auto bt = gpio_button.get_pin_val();
  while (1) {
    asm("nop");  // TEST TAG A
    gpio_toggler.set_pin_val(true);
    bt = gpio_button.get_pin_val();
    asm("nop");  // TEST TAG A
    gpio_toggler.set_pin_val(false);
    bt = gpio_button.get_pin_val();
    asm("nop");  // TEST TAG A
  }
}
