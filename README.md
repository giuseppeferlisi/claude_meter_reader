# claude_meter_reader
This Home assistant custom integration "claude_meter_reader" (domain: claude_meter_reader), is a water meter reader using an ESP32 camera via ESPHome integration to capture images and extract values via the Claude AI API. You need a claude API Key and account.
- Create a new ESPHome device. You can use the Template "wasserzähler_ESPHome.yaml"
- Create a new folder in HA /config/custom_components/claude_meter_reader
- Copy the files to the folder
- Restart HA
- Add the integration an configure the parameters

- The code will try to use the latest LLM model from claude if you have a valid pir2 account. If not he will use the pir1 LLM model (low cost $0.24$ per Month). 
