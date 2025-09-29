# claude_meter_reader
This Home assistant custom integration "claude_meter_reader" (domain: claude_meter_reader), is a water meter reader using an ESP32 camera via ESPHome integration to capture images and extract values via the Claude AI API. You need a claude API Key and account.
- Create a new ESPHome device. You can use the Template "esphome\wasserzähler.yaml"
- Create a new folder in HA /config/custom_components/claude_meter_reader
- Copy the files to the folder
- Restart HA
- Add the integration an configure the parameters
- You can define your own request thats fits for you meter:

    READ WATER METER: The image shows a water meter with:
    
    Main digits: 00087 (= 87 m³)
    Decimal places from the round displays on the right
    Meter reading: 87.18 m³
    Return only the number: 87.18

- The code will try to use the latest LLM model from claude if you have a valid pir2 account. If not he will use the pir1 LLM model (low cost $0.24$ per Month).

HA Dashboard: <img width="499" height="346" alt="image" src="https://github.com/user-attachments/assets/c10af065-e2c6-4942-b934-ab508877b57f" />

Zähler: <img width="500" height="531" alt="image" src="https://github.com/user-attachments/assets/ab05efd5-5485-498d-997f-90fe37614073" />


