import board
import adafruit_tca9548a
import adafruit_sht4x
from typing import Dict
from logging import exception
import time


class MultiSensor:
    def __init__(self, sensors: Dict[str, int]):
        self.i2c = board.I2C()
        self.multiplexer = adafruit_tca9548a.TCA9548A(self.i2c)
        self.sensors = {
            k: adafruit_sht4x.SHT4x(self.multiplexer[v]) for k, v in sensors.items()
        }

    def check_sensor(self, name: str):
        if name in self.sensors.keys():
            try:
                temp, hum = self.sensors[name].measurements
            except:
                exception("Encountered I2C Error:")
                raise RuntimeError(
                    f"Failed to read sensor {name} due to unexpected I2C error."
                )
            return {"temperature": temp, "humidity": hum}
        else:
            raise KeyError(f"Failed to read sensor {name} as it does not exist.")

    def read_sensors(self):
        return {n: self.check_sensor(n) for n in self.sensors.keys()}


if __name__ == "__main__":
    ms = MultiSensor({"01": 1, "02": 2})
    while True:
        print(ms.read_sensors())
        time.sleep(1)
