import board
import adafruit_tca9548a
import adafruit_sht4x
from typing import Dict
from logging import exception, error
import time
import requests
import dotenv
import os
import json


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
    dotenv.load_dotenv()
    with open(os.environ["SENSORS"], "r") as f:
        ms = MultiSensor(json.load(f))
    s_url = os.environ["SERVER_URL"]
    api_key = os.environ["API_KEY"]
    s_name = os.environ["SENSOR_NAME"]
    interval = int(os.environ["SCAN_INTERVAL"])
    while True:
        data = ms.read_sensors()
        print(data)
        resp = requests.post(s_url + f"/data/{s_name}", data=json.dumps({
            "logged_at": time.time(),
            "data": data
        }), headers={
            "Authorization": api_key
        })
        if resp.status_code > 300:
            try:
                error(f"Failed to log data with code {resp.status_code} and data {json.dumps(resp.json())}")
            except:
                error(f"Failed to log data with code {resp.status_code} and no data")
        time.sleep(interval)

