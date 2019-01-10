// Arduino code for the usb volume mixer
// Only works on HID enabled Arudino models(leonardo, pro micro, etc...)
// By: Daniel Luan

#include "HID-Project.h"

uint8_t rawhidData[255];
uint8_t buff[64] = {0};
uint8_t last_buff[64] = {0};

// number of channels
int num = 5;

// pin number of switches
int switches[] = {2, 3, 4, 5, 6};

// pin number of pots
int pots[] = {A0, A1, A2, A3, A10};

void setup() {
  for (int i = 0; i < num; i++) {
    pinMode(switches[i], INPUT_PULLUP);
  }

  pinMode(LED_BUILTIN, OUTPUT);

  RawHID.begin(rawhidData, sizeof(rawhidData));
}

// compare arrays, return true if there is a difference
bool array_cmp(uint8_t* a, uint8_t* b) {
  for (int n = 0; n < 64; n++) if (a[n] != b[n]) return true;
  return false;
}

void loop() {
  // HID report format
  // Index: |       0         |      1      |      2      | ... |     num + 1    |     num + 2    | ... | 
  // Value: | num of channels | pot value 1 | pot value 2 | ... | switch value 1 | switch value 2 | ... |
  // Example:
  // |0|1|2 |3 |4 | 5 |6|7|8|9|10|
  // |5|0|10|50|90|100|1|0|1|0|1 |   
  
  buff[0] = num;

  for (int i = 0; i < num; i++) {
    buff[i + 1] = map(analogRead(pots[i]), 0, 1023, 0, 100);
    buff[i + num + 1] = digitalRead(switches[i]);
  }

  // only send on change
  if (array_cmp(buff, last_buff)) {
    digitalWrite(LED_BUILTIN, 1);
    RawHID.write(buff, sizeof(buff));
    delay(200);
    digitalWrite(LED_BUILTIN, 0);
  }

  memcpy(last_buff, buff, sizeof(buff[0])*64);
}
